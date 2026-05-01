# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from pysvlib.sexpr import Binary, Hexadecimal, Keyword
from pysvlib.svlib import Sort
from pysvlib.svlib.factory import Factory
from pysvlib.svlib.syntax import (
    Annotated,
    Application,
    Assign,
    BitVec,
    Command,
    DeclareVar,
    DefineFun,
    DefineProc,
    Function,
    GetWitness,
    Literal,
    Procedure,
    SetLogic,
    Statement,
    Term,
    Type,
    Variable,
    VerifyCall,
    While,
)
from pysvlib.translators.btor2.antlr.Btor2Parser import Btor2Parser
from pysvlib.translators.btor2.antlr.Btor2Visitor import Btor2Visitor
from pysvlib.translators.btor2.errors import Btor2TranslationException


class LineNumber(int):
    pass


class Btor2ToCommandsVisitor(Btor2Visitor):
    # constants à la Python3
    @staticmethod
    def __smtlib_array_bitvec_logic():
        return "QF_AUFBV"

    @staticmethod
    def __proc_name():
        return "btor2_proc"

    @staticmethod
    def __btor2_op_to_svlib_op_map():
        return {
            "eq": "bvomp",
            "iff": "bvcomp",
            "srl": "bvlshr",
            "sll": "bvshl",
            "sra": "bvashr",
        }

    def __init__(self):
        super().__init__()
        self._sorts: dict[LineNumber, Type] = {}

        self._inputs: dict[LineNumber, Variable] = {}
        self._inputs_local: dict[LineNumber, Variable] = {}

        self._outputs: dict[LineNumber, Variable] = {}
        self._locals: dict[LineNumber, Variable] = {}

        self._constants: list[DefineFun] = []

        # all assigns that need to happen before going into the while loop
        # this is later wrapped in Assign to avoid having one assign per assignment
        # list of tuples(variable name to assign, assign value or variable name
        self._init_tuples_list: list[tuple[Variable, Term]] = []

        # shadow proc formals: (local, param) pairs, wrapped in one Assign before init_assign
        self._inputs_local_assign_tuples_list: list[tuple[Variable, Variable]] = []

        self._statements_head: list[Statement] = []
        self._statements_tail: list[Statement] = []

        # needed if another operation node references an operation node
        self._operations: dict[LineNumber, Variable] = {}

        # Needed to concatenate all assignment tuples in one assign statement
        self._tail_next_assigns: list[tuple[Variable, Term]] = []

        self._literals: dict[LineNumber, Literal] = {}

        self._current_line_num = LineNumber(0)
        self._factory = Factory()

    def visitBtor2_file(self, ctx: Btor2Parser.Btor2_fileContext):
        commands: list[Command] = [SetLogic(self.__smtlib_array_bitvec_logic())]

        for line in ctx.line():
            self.visit(line)

        # after set-logic we declare the constants globally
        commands = commands + self._constants

        proc = Procedure(
            self.__proc_name(),
            self._to_proc_param(self._inputs),
            self._to_proc_param(self._outputs),
            self._to_proc_param(self._get_proc_locals()),
        )

        body = self._prepare_proc_body()
        define_proc = DefineProc(proc, body)
        commands.append(define_proc)

        if len(self._inputs) > 0:
            for var in self._inputs.values():
                # skip constants as they are already declared above (globally) and they are not inputs
                if var.name in self._constants:
                    continue
                commands.append(DeclareVar(var))

        commands.append(VerifyCall(self.__proc_name(), self._to_proc_param(self._inputs)))

        commands.append(GetWitness())

        return commands

    @staticmethod
    def _to_proc_param(inputs: dict[LineNumber, Variable]) -> tuple[Variable, ...]:
        return tuple(var for var in inputs.values())

    def _prepare_proc_body(self):
        inputs_local_assign = Assign(tuple(self._inputs_local_assign_tuples_list))
        init_assign = Assign(tuple(self._init_tuples_list))

        if len(self._tail_next_assigns) > 0:
            self._statements_tail.append(Assign(tuple(self._tail_next_assigns)))

        statements = self._statements_head + self._statements_tail
        while_true = While(self._factory.boolean(True), self._factory.sequence(statements))

        tag = [("tag", Keyword("btor2_proc_while_loop"))]
        while_true = self._factory.annotate_statement(while_true, tag, [], [])

        body_statements = [init_assign, while_true] if len(self._init_tuples_list) > 0 else [while_true]

        if len(self._inputs_local_assign_tuples_list) > 0:
            body_statements = [inputs_local_assign] + body_statements

        proc_body = self._factory.annotate_statement(
            self._factory.sequence(body_statements),
            [("tag", Keyword("btor2_proc_body"))],
            [],
            [],
        )

        return proc_body

    def visitLine(self, ctx: Btor2Parser.LineContext):
        self._current_line_num = LineNumber(self._token_to_int(ctx.NUM()))
        self.visit(ctx.node())

    def visitNode(self, ctx: Btor2Parser.NodeContext):
        self.visitChildren(ctx)

    def visitInput(self, ctx: Btor2Parser.InputContext):
        proc_input = self.visitChildren(ctx)
        if proc_input is None:
            return

        if isinstance(proc_input, Literal):
            self._literals[self._get_line_num()] = proc_input
        elif isinstance(proc_input, Variable):
            self._add_input_and_local(self._get_line_num(), proc_input)

    def visitInputLiteral(self, ctx: Btor2Parser.InputLiteralContext):
        var_name = self._unique_var_name("input", "")

        symbol = ctx.SYMBOL()
        if symbol is not None:
            var_name = symbol.getText()

        sid = LineNumber(self._token_to_int(ctx.NUM()))
        sort = self._get_sort(sid)
        var = Variable(var_name, None, sort)

        if ctx.INPUT() is not None:
            return var

        assert isinstance(sort, BitVec)
        width = sort.bits

        value = 0
        match self._operator_name(ctx):
            case "one":
                value = 1
            case "ones":
                value = (1 << width) - 1
            case "zero":
                value = 0
            case _:
                raise Btor2TranslationException(f"missed one parser token type: {self._operator_name(ctx)}")

        return Literal(value, sort)

    def visitStateNode(self, ctx: Btor2Parser.StateNodeContext):
        sid = LineNumber(self._token_to_int(ctx.NUM()))
        sort = self._get_sort(sid)
        symbol = ctx.SYMBOL()

        var_name = self._unique_var_name("state", "")

        if symbol is not None:
            var_name = (
                symbol.getText()
                if not self._var_name_exists(symbol.getText())
                else self._unique_var_name(symbol.getText(), "_")
            )

        var = Variable(var_name, None, sort)
        self._add_input_and_local(self._get_line_num(), var)

    def visitConstNode(self, ctx: Btor2Parser.ConstNodeContext):
        line = LineNumber(self._token_to_int(ctx.NUM()))
        sort = self._get_sort(line)

        literal = None
        match self._operator_name(ctx):
            case "const":
                binary_val = ctx.binaryValue().getText()
                binary = Binary(binary_val)
                literal = Literal(binary, sort)

            case "constd":
                int_value = self._token_to_int(ctx.uint())
                if ctx.NEG_SYM() is not None:
                    int_value = -int_value

                literal = Literal(int_value, sort)

            case "consth":
                hex_value = ctx.HEX().getText()
                literal = Literal(Hexadecimal(hex_value), sort)
            case _:
                raise Btor2TranslationException(f"missed one parser token type: {self._operator_name(ctx)}")

        const_name = self._unique_var_name("const", "")

        declare_const = DefineFun(Function(const_name, tuple([]), sort), literal)
        self._constants.append(declare_const)

        param = Variable(const_name, None, sort)
        self._add_input_and_local(self._get_line_num(), param)

    def visitIndexedOpNode(self, ctx: Btor2Parser.IndexedOpNodeContext):
        line = LineNumber(self._token_to_int(ctx.NUM(0)))
        sort = self._get_sort(line)
        sort = self._ensure_bitvector_sort(sort)

        reference_1 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(1))))
        index_1 = self._token_to_int(ctx.uint(0))

        application = None

        match self._operator_name(ctx):
            case "slice":
                low = index_1
                high = self._token_to_int(ctx.uint(1))

                application = Application(self._get_extract_name(low, high), (reference_1,))

            case "uext":
                # concat [0]^index_1 reference_1
                application = Application("concat", (Literal(0, BitVec(index_1)), reference_1))

            case "sext":
                # extract MSB and repeat index_1 times to the left
                width = sort.bits
                last_index = width - 1

                msb_extract_application = Application(self._get_extract_name(last_index, last_index), (reference_1,))
                repeat_msb_application = Application(f"(_ repeat {index_1})", (msb_extract_application,))

                application = Application("concat", (repeat_msb_application, reference_1))
            case _:
                raise Btor2TranslationException(f"missed one parser token type: {self._operator_name(ctx)}")

        self._add_to_statements_locals_operations(application, sort)

    def visitUnaryOpNode(self, ctx: Btor2Parser.UnaryOpNodeContext):
        line = LineNumber(self._token_to_int(ctx.NUM(0)))
        sort = self._get_sort(line)
        reference_id = LineNumber(self._token_to_int(ctx.NUM(1)))

        referenced_term: Variable | Literal = self._get_reference(reference_id)

        if referenced_term is None:
            raise Btor2TranslationException(
                f"referenced node not found: {reference_id} line num: {self._get_line_num()}"
            )

        application = None
        operator_name = self._operator_name(ctx)

        operator_name_bv = f"bv{operator_name}"

        match operator_name:
            case "not" | "neg":
                application = Application(operator_name_bv, (referenced_term,))

            case "inc":
                # maps to just adding bv1 to referenced term
                application = Application(
                    "bvadd",
                    (
                        referenced_term,
                        Literal(1, BitVec(1)),
                    ),
                )

            case "dec":
                # maps to just subtracting bv1 of referenced term
                application = Application(
                    "bvsub",
                    (
                        referenced_term,
                        Literal(1, BitVec(1)),
                    ),
                )

            case "redand" | "redor" | "redxor":
                application = Application(operator_name, (referenced_term,))

            case _:
                raise Btor2TranslationException(f"missed one parser token type: {self._operator_name(ctx)}")

        self._add_to_statements_locals_operations(application, sort)

    def visitBinaryOpNode(self, ctx: Btor2Parser.BinaryOpNodeContext):
        self.visitChildren(ctx)

    def visitBinaryOpNodeFixed(self, ctx: Btor2Parser.BinaryOpNodeFixedContext):
        operator_name = self._operator_name(ctx)
        line = LineNumber(self._token_to_int(ctx.NUM(0)))
        return_type = self._get_sort(line)

        if isinstance(return_type, Sort) and return_type.name == "Array":
            raise Btor2TranslationException("encountered array return type on non array function")
        if not isinstance(return_type, BitVec):
            raise Btor2TranslationException(f"Encountered unknown type: {return_type}")
        # At this point sort can only be bitvec

        reference_id_left = LineNumber(self._token_to_int(ctx.NUM(1)))
        reference_id_right = LineNumber(self._token_to_int(ctx.NUM(2)))

        referenced_term_left: Variable | Literal = self._get_reference(reference_id_left)
        referenced_term_right: Variable | Literal = self._get_reference(reference_id_right)

        application = None

        # handle array early and return
        if self._is_reference_array_sort(referenced_term_left) and self._is_reference_array_sort(referenced_term_right):
            # only possible binary ops for arrays
            match operator_name:
                case "eq":
                    application = Application("=", (referenced_term_left, referenced_term_right))
                case "neq":
                    application = Application("distinct", (referenced_term_left, referenced_term_right))
                case _:
                    raise Btor2TranslationException(
                        f"unknown binary operator for array input type: {operator_name};"
                        f" line_num: {self._get_line_num()}"
                    )

            self._add_to_statements_locals_operations(application, return_type)
            return

        # raises if sort is not bv
        _ = self._get_bitvector_sort_from_any_recursive(referenced_term_left).bits
        _ = self._get_bitvector_sort_from_any_recursive(referenced_term_right).bits

        operator_name_bv = f"bv{operator_name}"

        match operator_name:
            case "eq" | "iff" | "srl" | "sll" | "sra":
                application = Application(
                    self.__btor2_op_to_svlib_op_map()[operator_name], (referenced_term_left, referenced_term_right)
                )
            case "neq":
                application = self._bitvector_negate(
                    Application("bvcomp", (referenced_term_left, referenced_term_right))
                )
            case "sgte" | "ugte" | "slte" | "ulte":
                operator_name_sliced = operator_name_bv.replace("t", "")
                application = Application(operator_name_sliced, (referenced_term_left, referenced_term_right))
            case "implies":
                application = Application(
                    "bvor", (Application("bvnot", (referenced_term_left,)), referenced_term_right)
                )
            case "rol":
                # ((_ rotate_left i) x) means rotate bits of x to the left i times
                # ROL x y ; x->x, y->i
                application = Application(f"(_ rotate_left {referenced_term_right})", (referenced_term_left,))
            case "ror":
                application = Application(f"(_ rotate_right {referenced_term_right})", (referenced_term_left,))
            case (
                "and"
                | "or"
                | "xor"
                | "sgt"
                | "ugt"
                | "slt"
                | "ult"
                | "sdivo"
                | "sdiv"
                | "saddo"
                | "uaddo"
                | "smulo"
                | "umulo"
                | "udiv"
                | "add"
                | "sub"
                | "ssubo"
                | "usubo"
                | "mul"
                | "nand"
                | "nor"
                | "xnor"
                | "smod"
                | "urem"
                | "srem"
            ):
                application = Application(
                    operator_name_bv,
                    (referenced_term_left, referenced_term_right),
                )
            case _:
                raise Btor2TranslationException(f"operator not implemented or missed: {operator_name}")

        self._add_to_statements_locals_operations(application, return_type)

    def visitBinaryOpNodeVar(self, ctx: Btor2Parser.BinaryOpNodeVarContext):
        line = LineNumber(self._token_to_int(ctx.NUM(0)))
        sort = self._get_sort(line)

        reference_1 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(1))))
        reference_2 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(2))))

        application = None

        operator_name = self._operator_name(ctx)
        match operator_name:
            case "read":
                referenced_array = reference_1
                index = reference_2

                application = Application("select", (referenced_array, index))
            case "concat":
                elements = ctx.children[3:]
                input_1 = reference_1
                input_2 = reference_2

                application = Application("concat", (input_1, input_2))

                if len(elements) > 0:
                    for child in elements:
                        reference = self._get_reference(LineNumber(self._token_to_int(child)))
                        application = Application("concat", (application, reference))
            case _:
                raise Btor2TranslationException(f"operator not implemented or missed: {operator_name}")

        self._add_to_statements_locals_operations(application, sort)

    def visitTernaryOpNode(self, ctx: Btor2Parser.TernaryOpNodeContext):
        line = LineNumber(self._token_to_int(ctx.NUM(0)))
        sort = self._get_sort(line)

        reference_1 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(1))))
        reference_2 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(2))))
        reference_3 = self._get_reference(LineNumber(self._token_to_int(ctx.NUM(3))))

        application = None

        operator_name = self._operator_name(ctx)
        match operator_name:
            case "write":
                referenced_array = reference_1
                index = reference_2
                referenced_write_value = reference_3

                application = Application("store", (referenced_array, index, referenced_write_value))

            case "ite":
                application = Application(
                    "ite", (Application("bvcomp", (reference_1, Literal(1, BitVec(1)))), reference_2, reference_3)
                )
            case _:
                raise Btor2TranslationException(f"operator not implemented or missed: {operator_name}")

        var_to_assign = self._get_assign_var(sort)
        assign = Assign(((var_to_assign, application),))

        self._statements_head.append(assign)
        self._operations[self._get_line_num()] = var_to_assign
        self._locals[self._get_line_num()] = var_to_assign

    @staticmethod
    def _bitvector_negate(term: Term) -> Application:
        return Application("bvnot", (term,))

    def visitNextNode(self, ctx: Btor2Parser.NextNodeContext):
        params = self._num_params_to_int(ctx)

        var = self._get_input(params[1])
        var_next = Variable(self._unique_var_name(f"{var.name}_next", ""), None, var.sort)
        value = self._get_reference(params[2])

        self._locals[self._get_line_num()] = var_next

        # self.head_next_assigns.append((var_next, value))
        assign = Assign(((var_next, value),))
        self._statements_head.append(assign)
        self._tail_next_assigns.append((var, var_next))

    def visitInitNode(self, ctx: Btor2Parser.InitNodeContext):
        params = self._num_params_to_int(ctx)
        var_id = params[1]
        var_or_literal_id = params[2]

        var = self._get_input(var_id)
        var_or_literal = self._get_literal(var_or_literal_id) or self._get_input(var_or_literal_id)

        self._init_tuples_list.append((var, var_or_literal))

    def visitPropNode(self, ctx: Btor2Parser.PropNodeContext):
        # bad -> check-true
        # constraint -> global invariant -> while loop :tag :assume op
        # output -> add to outputs

        reference_id = LineNumber(self._token_to_int(ctx.NUM()))
        reference = self._get_reference(reference_id)

        operator_name = self._operator_name(ctx)
        match operator_name:
            case "bad":
                negated_op = self._bitvector_negate(reference)
                sequence = self._empty_seq_with_condition(
                    f"bad_state_{self._get_line_num()}",
                    "check-true",
                    negated_op,
                )

                self._statements_head.append(sequence)
            case "constraint":
                assume_statement = self._factory.assume(reference)
                self._statements_head.append(assume_statement)
            case "output":
                optional_symbol = ctx.symbol().getChild(0)

                output_var_name = optional_symbol.getText() if optional_symbol else self._unique_var_name("output", "")

                output_var = Variable(output_var_name, None, reference.sort)
                self._outputs[reference_id] = output_var
            case "fair":
                raise Btor2TranslationException("fair property is not implemented yet")
            case _:
                raise Btor2TranslationException(f"operator not implemented or missed: {operator_name}")

    def visitJusticeNode(self, ctx: Btor2Parser.JusticeNodeContext):
        raise Btor2TranslationException("justice property is not implemented yet")

    def visitSortNode(self, ctx: Btor2Parser.SortNodeContext):
        return self.visitChildren(ctx)

    def visitBitvec(self, ctx: Btor2Parser.BitvecContext):
        bits = self._token_to_int(ctx.NUM())
        bitvec = self._factory.bitvec(bits)
        self._sorts[self._get_line_num()] = bitvec

    def visitArray(self, ctx: Btor2Parser.ArrayContext):
        index_sort = self._get_sort(LineNumber(self._token_to_int(ctx.NUM(0))))
        element_sort = self._get_sort(LineNumber(self._token_to_int(ctx.NUM(1))))
        array = self._factory.array(index_sort, element_sort)
        self._sorts[self._get_line_num()] = array

    def _get_sort(self, sid: LineNumber) -> Type | None:
        if sid in self._sorts:
            return self._sorts[sid]
        else:
            return None

    def _add_input_and_local(self, line: LineNumber, param: Variable) -> None:
        self._inputs[line] = param
        local = self._input_to_local(param)
        self._inputs_local[line] = local
        self._inputs_local_assign_tuples_list.append((local, param))

    def _add_to_statements_locals_operations(self, application: Application, sort: Type) -> None:
        var_to_assign = self._get_assign_var(sort)
        assign = Assign(((var_to_assign, application),))
        self._statements_head.append(assign)
        self._operations[self._get_line_num()] = var_to_assign
        self._locals[self._get_line_num()] = var_to_assign

    def _get_input(self, line_num: LineNumber) -> Variable | None:
        if line_num in self._inputs_local:
            return self._inputs_local[line_num]
        else:
            return None

    def _get_literal(self, line_num: LineNumber) -> Literal | None:
        if line_num in self._literals:
            return self._literals[line_num]
        else:
            return None

    def _get_op_var(self, line_num: LineNumber) -> Variable | None:
        if line_num in self._operations:
            return self._operations[line_num]
        else:
            return None

    def _get_reference(self, reference_id: LineNumber) -> Variable | Literal | Term:
        if reference_id < 0:
            unsigned_reference_id = LineNumber(abs(reference_id))
            reference = (
                self._get_input(unsigned_reference_id)
                or self._get_literal(unsigned_reference_id)
                or self._get_op_var(unsigned_reference_id)
            )
            assert reference is not None

            return Application("bvnot", (reference,))

        return self._get_input(reference_id) or self._get_literal(reference_id) or self._get_op_var(reference_id)

    def _get_line_num(self) -> LineNumber:
        return self._current_line_num

    def _get_assign_var(self, sort: Type):
        return Variable(self._unique_var_name("op", ""), None, sort)

    @staticmethod
    def _get_extract_name(index1, index2) -> str:
        return f"(_ extract {index1} {index2})"

    _unique_counter = 0

    def _unique_var_name(self, prefix: str, postfix: str) -> str:
        var_name = f"{prefix}{postfix}{self._get_line_num()}"

        if self._var_name_exists(var_name):
            self._unique_counter += 1
            return self._unique_var_name(prefix, f"{postfix}_unique{self._unique_counter}_")
        return var_name

    def _var_name_exists(self, var_name: str) -> bool:
        vars_dict = (self._inputs,) + (self._inputs_local,) + (self._locals,) + (self._outputs,) + (self._operations,)
        for var_dict in vars_dict:
            for var in var_dict.values():
                if var_name == var.name:
                    return True
        return False

    @staticmethod
    def _operator_name(ctx) -> str:
        return ctx.getChild(0).getText().lower()

    def _token_to_int(self, token) -> int:
        if token is None:
            raise Btor2TranslationException(f"Empty token: line_num: {self._get_line_num()}")
        return int(token.getText())

    def _empty_seq_with_condition(self, tag_name: str, property_name: str, condition_value: Term) -> Annotated:
        return Annotated(
            self._factory.sequence([]),
            (
                ("tag", Keyword(tag_name)),
                (property_name, condition_value),
            ),
            [],
            [],
        )

    def _num_params_to_int(self, ctx) -> list[LineNumber]:
        params: list[LineNumber] = []
        for num in ctx.NUM():
            params.append(LineNumber(self._token_to_int(num)))
        return params

    def _input_to_local(self, param: Variable) -> Variable:
        var_local_name = f"{param.name}_local"
        if self._var_name_exists(var_local_name):
            var_local_name = self._unique_var_name(param.name, "_local")
        return Variable(var_local_name, None, param.sort)

    def _get_proc_locals(self) -> dict[LineNumber, Variable]:
        ordered_locals: dict[LineNumber, Variable] = {}

        for line_num in sorted(self._inputs_local.keys()):
            ordered_locals[line_num] = self._inputs_local[line_num]

        for line_num in sorted(self._locals.keys()):
            ordered_locals[line_num] = self._locals[line_num]

        return ordered_locals

    def _get_bitvector_sort_from_any_recursive(self, var: Variable | Literal | Application | Term) -> BitVec:
        # mainly because negated nid -> bvnot application term,
        # so for e.g. rotate where we need bv width we need to recursively find the width
        if isinstance(var, Application):
            return self._get_bitvector_sort_from_any_recursive(var.args[0])
        if var is None or not hasattr(var, "sort") or not isinstance(var.sort, BitVec):
            raise Btor2TranslationException(
                f"Tried to get bitvector sort from non bitvector sort; var: {var} line_num: {self._get_line_num()}"
            )
        return var.sort

    def _ensure_bitvector_sort(self, sort: Type) -> BitVec:
        if isinstance(sort, BitVec):
            return sort
        raise Btor2TranslationException(
            f"encountered non bitvector sort on bitvector only node, sort: {sort} line_num: {self._get_line_num()}"
        )

    @staticmethod
    def _is_sort_array_sort(sort: Type):
        return isinstance(sort, Sort) and sort.name == "Array"

    def _is_reference_array_sort(self, term: Term):
        match term:
            case Application():
                return self._is_reference_array_sort(term.args[0])
            case Variable() | Literal():
                return self._is_sort_array_sort(term.sort)
            case _:
                return False
