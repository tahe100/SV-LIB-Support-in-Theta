# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from copy import copy

from pysvlib.cfa.datatypes import (
    AssumeCfaEdge,
    BlankCfaEdge,
    ImmutableCfa,
    MutableCfa,
    MutableCfaNode,
    MutableFunctionEntryNode,
    StatementCfaEdge,
)
from pysvlib.svlib import Application, Sequence, Variable, parse_svlib
from pysvlib.svlib.syntax import Assign, Call, Command, Havoc, Sort
from pysvlib.svlib.visitor import Visitor


class CfaBuilderFactory(Visitor):
    def __init__(self):
        super().__init__()

        self.current_loop_head: MutableCfaNode | None = None
        self.current_loop_exit: MutableCfaNode | None = None
        self.current_cfa_node: MutableCfaNode | None = None
        self.assertions: set[object] = set()
        self.functions: dict[str, tuple[object, object]] = {}
        self.globals: set[Variable] = set()
        self.function_name_to_io_sorts: dict[str, tuple[Sort, Sort]] = {}
        self.variables_in_scope: set[Variable] = set()
        self.procedure_entry_nodes: dict[str, MutableFunctionEntryNode] = {}
        self.tag_to_cfa_node: dict[str, MutableCfaNode] = {}
        self.currently_parsing_procedure: str | None = None
        # Mutable CFA nodes are not hashable by default, so we use a list here
        self.nodes: list[MutableCfaNode] = []
        self.modified_vars = set()

        # Keep track of annotations
        self.properties = set()
        self.tags = set()
        self.current_annotation_scope = None
        self.current_resolve_function = None

    def _add_annotations_to_node(self, node: MutableCfaNode):
        node.properties |= self.properties
        node.tags |= self.tags

        for tag in self.tags:
            self.tag_to_cfa_node[tag] = node

        if self.current_resolve_function is not None:
            node.resolve = self.current_resolve_function
            node.scope = self.current_annotation_scope

        self.current_annotation_scope = None
        self.current_resolve_function = None
        self.properties.clear()
        self.tags.clear()

    def _new_node(
        self,
        attributes: set[object],
        annotations: set[str],
        is_loop_head: bool,
        variables_modified_in_scc: set[Variable] | None,
        scope: dict[str, Variable] | None = None,
    ) -> MutableCfaNode:
        node = MutableCfaNode(
            attributes,
            annotations,
            set(),
            set(),
            is_loop_head,
            variables_modified_in_scc,
            self.variables_in_scope,
            None,
            scope,
            None,
        )
        self.nodes.append(node)
        return node

    def returns(self):
        if self.currently_parsing_procedure is None:
            raise ValueError("return statement not inside a procedure")

        self._add_annotations_to_node(self.current_cfa_node)

        procedure_exit_node = self.procedure_entry_nodes[self.currently_parsing_procedure].function_exit_node

        BlankCfaEdge(
            self.current_cfa_node,
            procedure_exit_node,
        )
        self.current_cfa_node = None

    def breaks(self):
        if self.current_loop_exit is None:
            raise ValueError("break statement not inside a loop")

        self._add_annotations_to_node(self.current_cfa_node)

        BlankCfaEdge(
            self.current_cfa_node,
            self.current_loop_exit,
        )
        self.current_cfa_node = None

    def continues(self):
        # Connect to the current loop head
        if self.current_loop_head is None:
            raise ValueError("continue statement not inside a loop")

        self._add_annotations_to_node(self.current_cfa_node)

        BlankCfaEdge(
            self.current_cfa_node,
            self.current_loop_head,
        )
        self.current_cfa_node = None

    def annotated_statement(
        self,
        inner,
        tags,
        all_attributes,
        expanded_attributes,
        scope,
        resolve,
    ):
        self.properties |= set(
            (elem[0], resolve(scope, elem[1]))
            for elem in list(expanded_attributes) + list(all_attributes)
            if len(elem) == 2 and elem[0] != "tag"
        ).union(elem for elem in expanded_attributes if len(elem) != 2)
        self.tags |= set(tags)
        if self.current_resolve_function is not None:
            if isinstance(inner, Sequence) and len(inner.statements) == 0:
                # Special case: skip statements can be annotated multiple times,
                # so we allow overwriting the resolve function in this case
                # This is possible, since the resolve function does not
                # change for skip statements
                pass
            elif isinstance(self.current_cfa_node, MutableFunctionEntryNode):
                # Special case: function entry nodes can be annotated multiple times,
                # so we allow overwriting the resolve function in this case
                # This is possible, since the resolve function does not
                # change for function entry nodes
                pass
            else:
                raise ValueError("CFA node already has a resolve function")
        self.current_resolve_function = resolve
        self.current_annotation_scope = scope

        self.statement(inner)

    def assume(self, formula):
        # Just create an assume edge in the CFA
        self._add_annotations_to_node(self.current_cfa_node)
        new_node = self._new_node(set(), set(), False, None)
        AssumeCfaEdge(self.current_cfa_node, new_node, formula)
        self.current_cfa_node = new_node

    def assign(self, pairs):
        # The CFA builder does not need to do anything special for assignments
        self._add_annotations_to_node(self.current_cfa_node)
        new_node = self._new_node(set(), set(), False, None)
        StatementCfaEdge(self.current_cfa_node, new_node, Assign(pairs))
        self.current_cfa_node = new_node

    def havoc(self, vars):
        # The CFA builder does not need to do anything special for havoc statements
        self._add_annotations_to_node(self.current_cfa_node)
        new_node = self._new_node(set(), set(), False, None)
        StatementCfaEdge(self.current_cfa_node, new_node, Havoc(vars))
        self.current_cfa_node = new_node

    def choice(self, statements):
        # Do a nondeterministic choice by creating a new CFA node for each choice
        self._add_annotations_to_node(self.current_cfa_node)

        previous_cfa_node = self.current_cfa_node
        after_choice_node = self._new_node(set(), set(), False, None)
        for statement in statements:
            choice_node = self._new_node(set(), set(), False, None)
            BlankCfaEdge(
                previous_cfa_node,
                choice_node,
            )
            self.current_cfa_node = choice_node
            self.statement(statement)
            BlankCfaEdge(
                self.current_cfa_node,
                after_choice_node,
            )

        self.current_cfa_node = after_choice_node

    def sequence(self, statements):
        self._add_annotations_to_node(self.current_cfa_node)
        start_cfa_node = self.current_cfa_node
        for statement in statements:
            self.statement(statement)
            if self.current_cfa_node is None:
                # The current CFA node is None, meaning that we have reached a
                # terminal state (e.g., after a continue statement)
                return

        self.current_cfa_node.end_node_of_statement = start_cfa_node

    def call(self, name, arguments, receiver):
        self._add_annotations_to_node(self.current_cfa_node)
        # We model calls by just connecting the CFA nodes with a call edge
        # the analysis needs to figure out what to do with it
        new_cfa_node = self._new_node(set(), set(), False, None)
        StatementCfaEdge(self.current_cfa_node, new_cfa_node, Call(name, arguments, receiver))
        self.current_cfa_node = new_cfa_node

    def ifs(self, condition, if_true, if_false):
        self._add_annotations_to_node(self.current_cfa_node)

        previous_cfa_node = self.current_cfa_node

        # Create the nodes for the if-true and if-false branches
        if_true_node = self._new_node(set(), set(), False, None)
        if_false_node = self._new_node(set(), set(), False, None)
        after_if_node = self._new_node(set(), set(), False, None)

        # Now handle the conditions
        AssumeCfaEdge(
            previous_cfa_node,
            if_true_node,
            condition,
        )
        AssumeCfaEdge(
            previous_cfa_node,
            if_false_node,
            Application("not", tuple([condition])),
        )

        one_branch_returned = False
        # Now parse the if-true branch
        self.current_cfa_node = if_true_node
        self.statement(if_true)
        if self.current_cfa_node is not None:
            # Connect the end of the if-true branch to the after-if node
            BlankCfaEdge(
                self.current_cfa_node,
                after_if_node,
            )
            one_branch_returned = True

        # Now parse the if-false branch
        self.current_cfa_node = if_false_node
        self.statement(if_false)
        # Connect the end of the if-false branch to the after-if node
        if self.current_cfa_node is not None:
            BlankCfaEdge(
                self.current_cfa_node,
                after_if_node,
            )
            one_branch_returned = True

        # Finally, set the current node to the after-if node
        if one_branch_returned:
            self.current_cfa_node = after_if_node

    def whiles(self, condition, body):
        previous_loop_head = self.current_loop_head
        # TODO: Compute modified variables here

        self.current_loop_head = self._new_node(set(), set(), True, None)

        # Connect loop to previous node
        BlankCfaEdge(
            self.current_cfa_node,
            self.current_loop_head,
        )

        self._add_annotations_to_node(self.current_loop_head)

        previous_loop_exit_node = self.current_loop_exit
        self.current_loop_exit = self._new_node(set(), set(), False, None)
        loop_body_start_node = self._new_node(set(), set(), False, None)

        # Now handle the conditions
        AssumeCfaEdge(
            self.current_loop_head,
            loop_body_start_node,
            condition,
        )
        AssumeCfaEdge(
            self.current_loop_head,
            self.current_loop_exit,
            Application("not", (condition,)),
        )

        # Now parse the loop body
        self.current_cfa_node = loop_body_start_node

        current_modified_vars = self.modified_vars
        self.modified_vars = set()

        self.statement(body)

        self.current_loop_head.variables_modified_in_strongly_connected_component = copy(current_modified_vars)

        # Finally, connect the end of the loop body back to the loop head
        # This can be None, for example for a break immediately in the loop body
        if self.current_cfa_node is not None:
            BlankCfaEdge(
                self.current_cfa_node,
                self.current_loop_head,
            )

        # Now set the current node to the loop exit node and restore the previous loop head
        self.current_loop_head = previous_loop_head
        self.current_cfa_node = self.current_loop_exit
        self.current_loop_exit = previous_loop_exit_node
        self.modified_vars.update(current_modified_vars)

    def set_logic(self, logic):
        pass

    def get_assertions(self):
        pass

    def get_witness(self):
        pass

    def get_option(self, keyword, argument):
        pass

    def set_option(self, keyword, argument):
        pass

    def get_info(self, keyword, argument):
        pass

    def set_info(self, keyword, argument):
        pass

    def asserts(self, formula):
        self.assertions.add(formula)

    def declare_sort(self, name, params):
        pass

    def define_sort(self, name, params, body):
        pass

    def declare_datatypes(self, sorts, datatypes):
        pass

    def declare_fun(self, name, arguments, result):
        self.function_name_to_io_sorts[name] = (arguments, result)

    def define_fun(self, name, arguments, result, body):
        self.function_name_to_io_sorts[name] = (arguments, result)
        self.functions[name] = (arguments, body)

    def declare_var(self, name, sort):
        new_var = Variable(name, None, sort)
        self.globals.add(new_var)
        self.variables_in_scope.add(new_var)

    def define_proc(self, name, inputs, outputs, locals, body):
        current_vars = self.variables_in_scope.copy()
        self.variables_in_scope.update(set(inputs).union(set(outputs)).union(set(locals)))

        self.modified_vars = set()

        procedure_exit_node = self._new_node(set(), set(), False, None)
        procedure_entry_node = MutableFunctionEntryNode(
            set(),
            set(),
            set(),
            set(),
            False,
            None,
            self.variables_in_scope,
            None,
            None,
            procedure_exit_node,
            name,
            tuple(inputs),
            tuple(outputs),
            tuple(locals),
            procedure_exit_node,
        )
        self.nodes.append(procedure_entry_node)
        self.procedure_entry_nodes[name] = procedure_entry_node
        self.current_cfa_node = procedure_entry_node

        self.currently_parsing_procedure = name

        self.statement(body)

        # Add a blank edge to the exit node if we are not already there
        if self.current_cfa_node is not None and self.current_cfa_node != procedure_exit_node:
            BlankCfaEdge(
                self.current_cfa_node,
                procedure_exit_node,
            )

        procedure_entry_node.variables_modified_in_strongly_connected_component = copy(self.modified_vars)

        self.currently_parsing_procedure = None
        self.variables_in_scope = current_vars

    def define_procs_rec(self, procs, bodies):
        for proc, body in zip(procs, bodies, strict=True):
            self.define_proc(proc.name, proc.inputs, proc.outputs, proc.locals, body)

    def annotate_tag(self, tag, attributes):
        if tag in self.tag_to_cfa_node:
            cfa_node = self.tag_to_cfa_node[tag]

            for attribute in attributes:
                property_name = attribute[0]
                property_value = attribute[1]
                if property_value is not None:
                    property_value = cfa_node.resolve(cfa_node.scope, property_value)

                cfa_node.properties.add((property_name, property_value))

    def select_trace(self, *trace):
        pass

    def verify_call(self, name, arguments):
        # The CFA does not care about which function call is verified, it just builds the CFA
        pass


def build_cfa(program: str | list[Command]) -> ImmutableCfa:
    ast = parse_svlib(program) if isinstance(program, str) else program

    builder = CfaBuilderFactory()
    for command in ast:
        builder.command(command)

    # First create a mutable CFA from the builder's nodes
    mutable_cfa = MutableCfa(
        builder.nodes,
        builder.procedure_entry_nodes,
        builder.globals,
        builder.function_name_to_io_sorts,
        builder.assertions,
    )

    # Now create an immutable CFA from the mutable CFA
    immutable_cfa = mutable_cfa.immutable_copy()
    return immutable_cfa
