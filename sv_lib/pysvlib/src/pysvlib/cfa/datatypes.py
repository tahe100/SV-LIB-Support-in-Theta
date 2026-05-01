# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable, ClassVar

from pysvlib.svlib.syntax import Sort, Statement, Term, Variable


class NodeWithUniqueId:
    _id_counter: ClassVar[int] = 0
    id: int = field(init=False)

    def __post_init__(self):
        NodeWithUniqueId._id_counter += 1
        object.__setattr__(self, "id", NodeWithUniqueId._id_counter)


@dataclass(frozen=False, eq=False, repr=True, unsafe_hash=False, slots=True)
class MutableCfaNode(NodeWithUniqueId):
    tags: set[object]
    properties: set[str]
    entering_edges: set["CfaEdge"]
    leaving_edges: set["CfaEdge"]
    is_loop_head: bool
    variables_modified_in_strongly_connected_component: set[Variable] | None
    variables_in_scope: set[Variable]
    resolve: Callable[[Term], Term] | None
    scope: dict[str, Variable] | None
    end_node_of_statement: "MutableCfaNode | None"

    def immutable_copy(self) -> "CfaNode":
        return CfaNode(
            tags=frozenset(self.tags),
            properties=frozenset(self.properties),
            entering_edges=frozenset(self.entering_edges),
            leaving_edges=frozenset(self.leaving_edges),
            is_loop_head=self.is_loop_head,
            variables_modified_in_strongly_connected_component=(
                frozenset(self.variables_modified_in_strongly_connected_component)
                if self.variables_modified_in_strongly_connected_component is not None
                else None
            ),
            variables_in_scope=frozenset(self.variables_in_scope),
            end_node_of_statement=self.end_node_of_statement,
        )

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        # The only way to uniquely identify a node is by its id
        return self.id == other.id

    def __str__(self):
        return (
            f"MutableCfaNode(id={self.id}, tags={set(self.tags)}, "
            f"properties={set((k, str(v)) for k, v in self.properties)})"
        )


@dataclass(frozen=True, eq=False, repr=True, unsafe_hash=False, slots=True)
class CfaNode(NodeWithUniqueId):
    tags: frozenset[object]
    properties: frozenset[str]
    entering_edges: frozenset["CfaEdge"]
    leaving_edges: frozenset["CfaEdge"]
    is_loop_head: bool
    variables_modified_in_strongly_connected_component: frozenset[Variable] | None
    variables_in_scope: frozenset[Variable] | None
    end_node_of_statement: MutableCfaNode | None

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        # The only way to uniquely identify a node is by its id
        return self.id == other.id

    def __str__(self):
        return (
            f"CfaNode(id={self.id}, tags={set(self.tags)}, properties={set((k, str(v)) for k, v in self.properties)})"
        )


@dataclass(frozen=False, eq=True, repr=True, unsafe_hash=False, slots=True)
class MutableFunctionEntryNode(MutableCfaNode):
    function_name: str
    input_variables: tuple[Variable]
    output_variables: tuple[Variable]
    local_variables: tuple[Variable]
    function_exit_node: MutableCfaNode

    def immutable_copy(self) -> "FunctionEntryNode":
        base_copy = super(MutableFunctionEntryNode, self).immutable_copy()
        return FunctionEntryNode(
            tags=base_copy.tags,
            properties=base_copy.properties,
            entering_edges=base_copy.entering_edges,
            leaving_edges=base_copy.leaving_edges,
            is_loop_head=base_copy.is_loop_head,
            variables_modified_in_strongly_connected_component=base_copy.variables_modified_in_strongly_connected_component,
            variables_in_scope=base_copy.variables_in_scope,
            function_name=self.function_name,
            input_variables=self.input_variables,
            output_variables=self.output_variables,
            local_variables=self.local_variables,
            function_exit_node=self.function_exit_node,
            end_node_of_statement=self.end_node_of_statement,
        )

    def __hash__(self):
        # We can't do better since the node is mutable
        return 42

    def __str__(self):
        return (
            f"MutableFunctionEntryNode(id={self.id}, function_name={self.function_name}, "
            f"tags={set(self.tags)}, properties={set((k, str(v)) for k, v in self.properties)})"
        )


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class FunctionEntryNode(CfaNode):
    function_name: str
    input_variables: tuple[Variable]
    output_variables: tuple[Variable]
    local_variables: tuple[Variable]
    function_exit_node: CfaNode

    def __hash__(self):
        # Ignore the edges in the hash to avoid recursion
        return hash(
            (
                self.tags,
                self.properties,
                self.is_loop_head,
                self.function_name,
                self.input_variables,
                self.output_variables,
                self.local_variables,
                self.function_exit_node,
            )
        )

    def __str__(self):
        return (
            f"FunctionEntryNode(id={self.id}, function_name={self.function_name}, "
            f"tags={set(self.tags)}, properties={set((k, str(v)) for k, v in self.properties)})"
        )


# We need to keep the edges mutable to be able to build the immutable CFA
# at the end
@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class CfaEdge(ABC):
    predecessor: CfaNode | MutableCfaNode
    successor: CfaNode | MutableCfaNode

    def copy_with(
        self,
        new_predecessor: CfaNode | MutableCfaNode,
        new_successor: CfaNode | MutableCfaNode,
    ) -> "CfaEdge":
        raise NotImplementedError("Subclasses must implement this method.")

    def __post_init__(self):
        self.predecessor.leaving_edges.add(self)
        self.successor.entering_edges.add(self)

    def __hash__(self):
        return hash((self.predecessor, self.successor))


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class StatementCfaEdge(CfaEdge):
    statement: Statement

    def copy_with(
        self,
        new_predecessor: CfaNode | MutableCfaNode,
        new_successor: CfaNode | MutableCfaNode,
    ) -> "StatementCfaEdge":
        return StatementCfaEdge(
            predecessor=new_predecessor,
            successor=new_successor,
            statement=self.statement,
        )

    def __hash__(self):
        return super(StatementCfaEdge, self).__hash__()

    def __str__(self):
        return f"{self.predecessor.id} -- {str(self.statement)}--> {self.successor.id}"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class GhostStatementEdge(StatementCfaEdge):
    def __post_init__(self):
        pass


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class AssumeCfaEdge(CfaEdge):
    assumption: Term

    def copy_with(
        self,
        new_predecessor: CfaNode | MutableCfaNode,
        new_successor: CfaNode | MutableCfaNode,
    ) -> "AssumeCfaEdge":
        return AssumeCfaEdge(
            predecessor=new_predecessor,
            successor=new_successor,
            assumption=self.assumption,
        )

    def __hash__(self):
        return super(AssumeCfaEdge, self).__hash__()

    def __str__(self):
        return f"{self.predecessor.id} --[{str(self.assumption)}]--> {self.successor.id}"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class GhostAssumeCfaEdge(AssumeCfaEdge):
    def __post_init__(self):
        pass


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class BlankCfaEdge(CfaEdge):
    def copy_with(
        self,
        new_predecessor: CfaNode | MutableCfaNode,
        new_successor: CfaNode | MutableCfaNode,
    ) -> "BlankCfaEdge":
        return BlankCfaEdge(
            predecessor=new_predecessor,
            successor=new_successor,
        )

    def __hash__(self):
        return super(BlankCfaEdge, self).__hash__()

    def __str__(self):
        return f"{self.predecessor.id} ----> {self.successor.id}"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=False, slots=True)
class GhostBlankEdge(BlankCfaEdge):
    def __post_init__(self):
        pass


class ImmutableCfa:
    def __init__(
        self,
        nodes: frozenset[CfaNode],
        edges: frozenset[CfaEdge],
        procedure_entry_nodes: dict[str, FunctionEntryNode],
        global_variables: frozenset[Variable],
        function_name_to_io_sorts: dict[str, tuple[Sort, Sort]],
        assertions: frozenset[Statement],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.procedure_entry_nodes = procedure_entry_nodes
        self.global_variables = global_variables
        self.function_name_to_io_sorts = function_name_to_io_sorts
        self.assertions = assertions

        self._exit_to_entry_nodes: dict[CfaNode, FunctionEntryNode] = {
            entry_node.function_exit_node: entry_node for entry_node in self.procedure_entry_nodes.values()
        }

    def procedure_entry_node_for_exit_node(self, exit_node: CfaNode) -> FunctionEntryNode | None:
        return self._exit_to_entry_nodes.get(exit_node, None)


class MutableCfa:
    def __init__(
        self,
        nodes: list[MutableCfaNode],
        procedure_entry_nodes: dict[str, MutableFunctionEntryNode],
        global_variables: set[Variable],
        function_name_to_io_sorts: dict[str, tuple[Sort, Sort]],
        assertions: set[Statement],
    ) -> None:
        # Mutable nodes are not hashable, so we use a list here
        self.nodes: list[MutableCfaNode] = nodes
        self.procedure_entry_nodes: dict[str, MutableFunctionEntryNode] = procedure_entry_nodes
        self.global_variables: set[Variable] = global_variables
        self.assertions = assertions
        self.function_name_to_io_sorts = function_name_to_io_sorts

    def immutable_copy(self) -> ImmutableCfa:
        # Copy all the edges but now for the immutable nodes
        node_mapping = {mutable_node: mutable_node.immutable_copy() for mutable_node in self.nodes}

        # Now replace the procedure exit nodes in the procedure entry nodes
        for mutable_entry_node in self.procedure_entry_nodes.values():
            immutable_entry_node = node_mapping[mutable_entry_node]
            immutable_exit_node = node_mapping[mutable_entry_node.function_exit_node]
            object.__setattr__(immutable_entry_node, "function_exit_node", immutable_exit_node)

        # Now replace the statement end nodes in the immutable nodes
        for mutable_node in self.nodes:
            if mutable_node.end_node_of_statement is not None:
                immutable_node = node_mapping[mutable_node]
                immutable_end_node = node_mapping[mutable_node.end_node_of_statement]
                object.__setattr__(immutable_node, "end_node_of_statement", immutable_end_node)

        # Make the nodes forget their edges temporarily, to make the copies
        for immutable_node in node_mapping.values():
            object.__setattr__(immutable_node, "entering_edges", set())
            object.__setattr__(immutable_node, "leaving_edges", set())

        edges = set()
        for mutable_node in self.nodes:
            immutable_node = node_mapping[mutable_node]
            for edge in mutable_node.leaving_edges:
                immutable_successor = node_mapping[edge.successor]
                edges.add(edge.copy_with(immutable_node, immutable_successor))

        for immutable_node in node_mapping.values():
            object.__setattr__(
                immutable_node,
                "entering_edges",
                frozenset(immutable_node.entering_edges),
            )
            object.__setattr__(
                immutable_node,
                "leaving_edges",
                frozenset(immutable_node.leaving_edges),
            )

        procedure_entry_nodes: dict[str, FunctionEntryNode] = {}
        for name, mutable_entry_node in self.procedure_entry_nodes.items():
            procedure_entry_nodes[name] = node_mapping[mutable_entry_node]

        return ImmutableCfa(
            frozenset(node_mapping.values()),
            frozenset(edges),
            procedure_entry_nodes,
            frozenset(self.global_variables),
            self.function_name_to_io_sorts,
            frozenset(self.assertions),
        )
