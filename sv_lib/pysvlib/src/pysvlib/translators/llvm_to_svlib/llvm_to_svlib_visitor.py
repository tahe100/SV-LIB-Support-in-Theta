# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from fractions import Fraction
from itertools import chain
from typing import Optional

from llvmlite.binding import TypeKind as LlvmTypeKind
from llvmlite.binding import TypeRef, ValueKind

from pysvlib.sexpr.syntax import Symbol
from pysvlib.svlib import Goto
from pysvlib.svlib.factory import Factory as SvLibFactory
from pysvlib.svlib.syntax import (
    Application,
    BitVec,
    Command,
    DeclareVar,
    DefineProc,
    DefineProcsRec,
    FloatingPoint,
    Label,
    Literal,
    Procedure,
    Sequence,
    Sort,
    Statement,
    Term,
    Type,
    Variable,
)
from pysvlib.translators.llvm_to_svlib.exceptions.llvm_to_svlib_exceptions import (
    UnsupportedLlvmOpcodeException,
    UnsupportedLlvmTypeKindException,
)
from pysvlib.translators.llvm_to_svlib.llvm_opcode import LlvmOpCode
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref import (
    BlockRef,
    ConstantRef,
    FunctionRef,
    InstructionRef,
    LabelRef,
    LlvmModuleRef,
    OperandRef,
    VariableRef,
)
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref_util import LlvmLiteRefUtil
from pysvlib.translators.translation_utils.translate_to_svlib_result import (
    TranslateToAnnotatedResult,
    TranslateToProcedureResult,
    TranslateToStatementsResult,
)
from pysvlib.translators.translation_utils.translate_to_svlib_result_util import TranslateToSvLibResultUtil


class LlvmToSvLibVisitor:
    @staticmethod
    def visit_module(module: LlvmModuleRef) -> tuple[Command, ...]:
        """
        Visits the given LlvmModuleRef and returns an immutable tuple of SV-LIB commands.
        """
        global_variables: tuple[VariableRef, ...] = module.global_variables
        svlib_global_variables: tuple[DeclareVar, ...] = tuple(
            LlvmToSvLibVisitor.visit_global_variable(global_variable) for global_variable in global_variables
        )

        sorted_function_pools, recursive_pool_names = LlvmToSvLibVisitor.visit_function_pools(
            module, svlib_global_variables
        )

        svlib_procs: list[Command] = []
        for function_pool in sorted_function_pools:
            # check if the function pool is recursive, via name equality
            function_pool_names: frozenset[str] = frozenset(function_pool.name for function_pool in function_pool)
            if function_pool_names in recursive_pool_names:
                procedures: list[Procedure] = [
                    Procedure(
                        function.name, tuple(function.inputs), tuple(function.outputs), tuple(function.local_variables)
                    )
                    for function in function_pool
                ]
                bodies: list[Statement] = [function.body for function in function_pool]
                svlib_procs_rec: DefineProcsRec = SvLibFactory().define_procs_rec(procedures, bodies)
                svlib_procs.append(svlib_procs_rec)

            else:
                function: TranslateToProcedureResult = function_pool[0]
                svlib_proc: DefineProc = SvLibFactory().define_proc(
                    function.name, function.inputs, function.outputs, function.local_variables, function.body
                )
                svlib_procs.append(svlib_proc)

        return svlib_global_variables + tuple(svlib_procs)

    @staticmethod
    def visit_global_variable(global_variable: VariableRef) -> DeclareVar:
        # use .global_value_type (e.g. 'i32'), since .type is always 'ptr' for global variables in LLVM
        svlib_sort: Sort = LlvmToSvLibVisitor.visit_type(global_variable.operand_type)
        return SvLibFactory().declare_var(global_variable.name, svlib_sort)

    @staticmethod
    def visit_function_pools(
        module: LlvmModuleRef, global_variables: tuple[DeclareVar, ...]
    ) -> tuple[tuple[tuple[TranslateToProcedureResult, ...], ...], frozenset[frozenset[str]]]:
        # iterate over functions and translate from LLVM to SV-LIB
        visit_function_results: tuple[TranslateToProcedureResult, ...] = tuple(
            LlvmToSvLibVisitor.visit_function(llvm_function, global_variables) for llvm_function in module.functions
        )

        # find recursive pools and sort accordingly based on their dependencies
        recursive_function_pools: tuple[tuple[TranslateToProcedureResult, ...], ...] = (
            TranslateToSvLibResultUtil.find_recursive_pools(visit_function_results)
        )
        sorted_procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...] = (
            TranslateToSvLibResultUtil.sort_procedure_pools_by_dependencies(
                visit_function_results, recursive_function_pools
            )
        )

        recursive_pool_names: frozenset[frozenset[str]] = TranslateToSvLibResultUtil.get_procedure_pool_names(
            recursive_function_pools
        )

        return sorted_procedure_pools, recursive_pool_names

    @staticmethod
    def visit_function(function: FunctionRef, global_variables: tuple[DeclareVar, ...]) -> TranslateToProcedureResult:
        proc_name: str = function.name
        # arguments are always variables
        proc_inputs: tuple[Variable, ...] = tuple(
            LlvmToSvLibVisitor.visit_variable(argument, function) for argument in function.arguments
        )

        proc_output: Variable | None = None
        if function.return_type.type_kind is not LlvmTypeKind.void:
            # if the LLVM return type is not 'void', e.g., 'ret void', then use a single ghost variable
            output_sort: Sort = LlvmToSvLibVisitor.visit_type(function.return_type)
            output_name: str = "__llvm_translated_retval__" + function.name
            output_variable: Variable = Variable(output_name, function.name, output_sort)
            proc_output = output_variable

        proc_locals: tuple[Variable, ...] = tuple(
            LlvmToSvLibVisitor.visit_variable(local_variable, function) for local_variable in function.local_variables
        )

        # combine inputs and locals of the procedure to convert the block
        local_variables: tuple[Variable, ...] = proc_inputs + proc_locals

        visit_block_results: tuple[TranslateToAnnotatedResult, ...] = tuple(
            LlvmToSvLibVisitor.visit_block(block, proc_output, local_variables, global_variables, function)
            for block in function.blocks
        )

        all_statements = list(chain.from_iterable(result.all_statements for result in visit_block_results))
        proc_sequence: Sequence = SvLibFactory().sequence(all_statements)

        proc_tag = [("tag", Symbol(f"proc-{function.name}"))]
        proc_annotated: Statement = SvLibFactory().annotate_statement(proc_sequence, proc_tag, proc_sequence, None)

        return TranslateToProcedureResult(
            proc_name,
            proc_inputs,
            tuple([] if proc_output is None else [proc_output]),
            proc_locals,
            proc_annotated,
            visit_block_results,
        )

    @staticmethod
    def visit_block(
        block: BlockRef,
        return_variable: Variable | None,
        local_variables: tuple[Variable, ...],
        global_variables: tuple[DeclareVar, ...],
        function: FunctionRef,
    ) -> TranslateToAnnotatedResult:
        # convert the LLVM label (each LLVM block has a label at its start) to an SV-LIB label and tag it
        svlib_label: Label = SvLibFactory().label(block.label.name)
        svlib_tag = [("tag", Symbol(f"proc-{function.name}-{svlib_label.name}"))]
        svlib_annotated: Statement = SvLibFactory().annotate_statement(svlib_label, svlib_tag, svlib_label, None)

        visit_instruction_results: tuple[TranslateToStatementsResult, ...] = tuple(
            LlvmToSvLibVisitor.visit_instruction(instruction, return_variable, local_variables, function)
            for instruction in block.instructions
        )

        return TranslateToAnnotatedResult(svlib_annotated, visit_instruction_results)

    @staticmethod
    def visit_instruction(
        instruction: InstructionRef,
        return_variable: Variable | None,
        local_variables: tuple[Variable, ...],
        function: FunctionRef,
    ) -> TranslateToStatementsResult:
        LlvmOpCode.check_is_allowed_num_operands(instruction.opcode, len(instruction.operands))

        match instruction.opcode:
            # integer and float arithmetic
            case (
                LlvmOpCode.ADD
                | LlvmOpCode.FLOAT_ADD
                | LlvmOpCode.SUBTRACT
                | LlvmOpCode.FLOAT_SUBTRACT
                | LlvmOpCode.MULTIPLY
                | LlvmOpCode.FLOAT_MULTIPLY
                | LlvmOpCode.SIGNED_DIVISION
                | LlvmOpCode.FLOAT_DIVISION
                | LlvmOpCode.SIGNED_REMAINDER
                | LlvmOpCode.UNSIGNED_REMAINDER
                | LlvmOpCode.FLOAT_REMAINDER
            ):
                return TranslateToStatementsResult(
                    tuple([LlvmToSvLibVisitor.visit_binary_instruction(instruction, local_variables, function)])
                )

            # branches (if-else statements and loops)
            case LlvmOpCode.BRANCH:
                return TranslateToStatementsResult(
                    tuple([LlvmToSvLibVisitor.visit_branch_instruction(instruction, local_variables)])
                )

            case LlvmOpCode.CALL:
                return LlvmToSvLibVisitor.visit_call_instruction(instruction, local_variables, function)

            case LlvmOpCode.FLOAT_COMPARISON | LlvmOpCode.INTEGER_COMPARISON:
                return TranslateToStatementsResult(
                    tuple([LlvmToSvLibVisitor.visit_comparison_instruction(instruction, local_variables, function)])
                )

            # array extractions and insertions
            case LlvmOpCode.EXTRACT_VALUE:
                return TranslateToStatementsResult(
                    LlvmToSvLibVisitor.visit_extractvalue_instruction(instruction, local_variables, function)
                )
            case LlvmOpCode.INSERT_VALUE:
                return TranslateToStatementsResult(
                    LlvmToSvLibVisitor.visit_insertvalue_instruction(instruction, local_variables, function)
                )

            # function return instruction
            case LlvmOpCode.RETURN:
                return TranslateToStatementsResult(
                    LlvmToSvLibVisitor.visit_ret_instruction(instruction, return_variable, local_variables)
                )

        raise UnsupportedLlvmOpcodeException(instruction.opcode)

    @staticmethod
    def visit_binary_instruction(
        instruction: InstructionRef, local_variables: tuple[Variable, ...], function: FunctionRef
    ) -> Statement:
        LlvmLiteRefUtil.check_len_operands(instruction, 2)

        # binary instructions always have two operands
        left_operand, right_operand = instruction.operands

        # extract the svlib Terms, which can e.g. be Literals such as '0' or Variables such as 'x'
        svlib_left, left_type = LlvmToSvLibVisitor.visit_operand_with_type(left_operand, local_variables)
        svlib_right, right_type = LlvmToSvLibVisitor.visit_operand_with_type(right_operand, local_variables)

        if left_type != right_type:
            raise ValueError(f"Both operands of a binary operator must be of the same type: {left_type}, {right_type}")

        # create the Application of the operator, e.g. '(+ x y)'
        operator: str = LlvmToSvLibVisitor.visit_binary_operator(instruction.opcode, left_type)
        svlib_term: Application = Application(operator, tuple([svlib_left, svlib_right]))
        local_variable: VariableRef = LlvmToSvLibVisitor.visit_local_variable(instruction, function)

        # complete the assign statement, e.g. '(assign (z (+ x 42)))'
        left_hand_side: Term = LlvmToSvLibVisitor.visit_operand(local_variable, local_variables)
        return SvLibFactory().assign([(left_hand_side, svlib_term)])

    @staticmethod
    def visit_binary_operator(llvm_opcode: LlvmOpCode, svlib_type: Type) -> str:
        if isinstance(svlib_type, BitVec):
            # Reference: https://smt-lib.org/theories-FixedSizeBitVectors.shtml
            match llvm_opcode:
                case LlvmOpCode.ADD:
                    return "bvadd"
                case LlvmOpCode.SUBTRACT:
                    return "bvsub"
                case LlvmOpCode.MULTIPLY:
                    return "bvmul"
                case LlvmOpCode.SIGNED_DIVISION:
                    return "bvsdiv"
                # Reference: https://smt-lib.org/logics-all.shtml
                case LlvmOpCode.SIGNED_REMAINDER:
                    return "bvsrem"
                case LlvmOpCode.UNSIGNED_REMAINDER:
                    return "bvurem"

        elif isinstance(svlib_type, FloatingPoint):
            # Reference: https://smt-lib.org/theories-FloatingPoint.shtml
            match llvm_opcode:
                case LlvmOpCode.FLOAT_ADD:
                    return "fp.add"
                case LlvmOpCode.FLOAT_SUBTRACT:
                    return "fp.sub"
                case LlvmOpCode.FLOAT_MULTIPLY:
                    return "fp.mul"
                case LlvmOpCode.FLOAT_DIVISION:
                    return "fp.div"
                case LlvmOpCode.FLOAT_REMAINDER:
                    return "fp.rem"

        elif isinstance(svlib_type, Sort) and (svlib_type.name == "Int" or svlib_type.name == "Real"):
            # For Ints and Reals
            match llvm_opcode:
                case LlvmOpCode.ADD | LlvmOpCode.FLOAT_ADD:
                    return "+"
                case LlvmOpCode.SUBTRACT | LlvmOpCode.FLOAT_SUBTRACT:
                    return "-"
                case LlvmOpCode.MULTIPLY | LlvmOpCode.FLOAT_MULTIPLY:
                    return "*"
                # for division of integers, use 'div' (cf. https://smt-lib.org/theories-Ints.shtml)
                case LlvmOpCode.SIGNED_DIVISION:
                    if svlib_type.name == "Int":
                        return "div"
                # for division of floats, use '/' (cf. https://smt-lib.org/theories-Reals.shtml)
                case LlvmOpCode.FLOAT_DIVISION:
                    if svlib_type.name == "Real":
                        return "/"
                case LlvmOpCode.SIGNED_REMAINDER | LlvmOpCode.UNSIGNED_REMAINDER:
                    # note that there is no standard modulo or remainder operator for Reals
                    if svlib_type.name == "Int":
                        return "mod"

        raise ValueError(
            f"The binary operator from the following opcode could not be translated: {llvm_opcode}\n"
            f"SV-LIB Type: {svlib_type}"
        )

    @staticmethod
    def visit_branch_instruction(
        instruction: InstructionRef,
        local_variables: tuple[Variable, ...],
    ) -> Statement:
        """
        Converts an LLVM 'br' instruction, e.g., 'br i1 %cond, label %if, label %else' to an SV-LIB Statement.
        The branch instruction consists of either:
        - 1 operand = 1 label (corresponds to a goto in C)
        - 3 operands = 1 condition and 2 labels (corresponds to an if-else in C with 2 gotos)
        """
        if len(instruction.operands) == LlvmOpCode.BRANCH.min_operands:
            label = instruction.operands[0]
            svlib_label: Label = LlvmToSvLibVisitor.visit_operand(label, local_variables)

            return SvLibFactory().goto(svlib_label.name)

        elif len(instruction.operands) == LlvmOpCode.BRANCH.max_operands:
            # the labels are reversed
            cond_operand, else_label, if_label = instruction.operands

            svlib_cond: Term = LlvmToSvLibVisitor.visit_operand(cond_operand, local_variables)
            svlib_if_label: Label = LlvmToSvLibVisitor.visit_operand(if_label, local_variables)
            svlib_else_label: Label = LlvmToSvLibVisitor.visit_operand(else_label, local_variables)

            svlib_goto_if: Goto = SvLibFactory().goto(svlib_if_label.name)
            svlib_goto_else: Goto = SvLibFactory().goto(svlib_else_label.name)

            return SvLibFactory().ifs(svlib_cond, svlib_goto_if, svlib_goto_else)

        else:
            raise ValueError(
                f"The following br instruction has an unexpected amount of operands: {instruction.original_instruction}"
            )

    @staticmethod
    def visit_call_instruction(
        instruction: InstructionRef, local_variables: tuple[Variable, ...], function: FunctionRef
    ) -> TranslateToStatementsResult:
        # the function name operand is always the last one
        called_function: OperandRef = instruction.operands[-1]

        function_inputs: list[Term] = [
            LlvmToSvLibVisitor.visit_operand(operand, local_variables) for operand in instruction.operands[:-1]
        ]

        function_output: list[Variable] = []
        if instruction.local_variable is not None:
            local_variable: VariableRef = LlvmToSvLibVisitor.visit_local_variable(instruction, function)
            svlib_variable: Variable = LlvmToSvLibVisitor.visit_variable(local_variable, function)
            function_output.append(svlib_variable)

        call: Statement = SvLibFactory().call(called_function.name, function_inputs, function_output)

        return TranslateToStatementsResult(tuple([call]), called_function.name)

    @staticmethod
    def visit_comparison_instruction(
        instruction: InstructionRef, local_variables: tuple[Variable, ...], function: FunctionRef
    ) -> Statement:
        LlvmLiteRefUtil.check_len_operands(instruction, 2)

        left_operand, right_operand = instruction.operands

        svlib_left, left_type = LlvmToSvLibVisitor.visit_operand_with_type(left_operand, local_variables)
        svlib_right, right_type = LlvmToSvLibVisitor.visit_operand_with_type(right_operand, local_variables)

        if left_type != right_type:
            raise ValueError(f"Both operands of a comparison must be of the same type: {left_type}, {right_type}")

        svlib_fun: str = LlvmToSvLibVisitor.visit_comparison_condition_code(instruction.condition_code, left_type)
        application: Application = Application(svlib_fun, tuple([svlib_left, svlib_right]))

        local_variable: VariableRef = LlvmToSvLibVisitor.visit_local_variable(instruction, function)
        svlib_variable: Variable = LlvmToSvLibVisitor.visit_variable(local_variable, function)

        return SvLibFactory().assign([(svlib_variable, application)])

    @staticmethod
    def visit_comparison_condition_code(condition_code: str, svlib_type: Type) -> str:
        if isinstance(svlib_type, BitVec):
            match condition_code:
                case "eq":
                    return "="
                case "ne":
                    return "distinct"
                # signed comparisons
                case "slt":
                    return "bvslt"
                case "sle":
                    return "bvsle"
                case "sgt":
                    return "bvsgt"
                case "sge":
                    return "bvsge"
                # unsigned comparisons
                case "ult":
                    return "bvult"
                case "ule":
                    return "bvule"
                case "ugt":
                    return "bvugt"
                case "uge":
                    return "bvuge"

        elif isinstance(svlib_type, FloatingPoint):
            match condition_code:
                case "oeq" | "ueq":
                    return "fp.eq"
                case "one" | "une":
                    return "fp.ne"
                case "olt" | "ult":
                    return "fp.lt"
                case "ole" | "ule":
                    return "fp.leq"
                case "ogt" | "ugt":
                    return "fp.gt"
                case "oge" | "uge":
                    return "fp.geq"
                # handle special predicates
                case "ord":
                    return "fp.isNormal"
                case "uno":
                    return "fp.isNaN"

        elif isinstance(svlib_type, Sort) and (svlib_type.name in {"Int", "Real"}):
            match condition_code:
                case "eq":
                    return "="
                case "ne":
                    return "distinct"
                case "lt":
                    return "<"
                case "le":
                    return "<="
                case "gt":
                    return ">"
                case "ge":
                    return ">="

        raise ValueError(
            f"The following comparison condition code could not be translated: {condition_code}\n"
            f"SV-LIB Type: {svlib_type}"
        )

    @staticmethod
    def visit_extractvalue_instruction(
        instruction: InstructionRef, local_variables: tuple[Variable, ...], function: FunctionRef
    ) -> tuple[Statement, ...]:
        local_variable: VariableRef = LlvmToSvLibVisitor.visit_local_variable(instruction, function)
        left_hand_side: Term = LlvmToSvLibVisitor.visit_operand(local_variable, local_variables)

        aggregate_value: OperandRef = instruction.operands[0]

        svlib_left: Term = LlvmToSvLibVisitor.visit_operand(aggregate_value, local_variables)

        # in SMT-LIB: (select array index) for each index
        select_assigns: list[Statement] = []
        for index in instruction.indices:
            svlib_index_term: Term = Literal(index, SvLibFactory().int())
            store: Application = Application("select", (svlib_left, svlib_index_term))
            select_assigns.append(SvLibFactory().assign([(left_hand_side, store)]))

        return tuple(select_assigns)

    @staticmethod
    def visit_insertvalue_instruction(
        instruction: InstructionRef, local_variables: tuple[Variable, ...], function: FunctionRef
    ) -> tuple[Statement, ...]:
        local_variable: VariableRef = LlvmToSvLibVisitor.visit_local_variable(instruction, function)
        left_hand_side: Term = LlvmToSvLibVisitor.visit_operand(local_variable, local_variables)

        aggregate_value, inserted_value = instruction.operands

        # The aggregate value may be undef, e.g. '[2 x i32] undef' in '%arr = insertvalue [2 x i32] undef, i32 1, 0'.
        # In this case the left_hand_side should be used, because the array is "initialized" in SV-LIB.
        if aggregate_value.value_kind == ValueKind.undef_value:
            svlib_left: Term = left_hand_side
        else:
            svlib_left: Term = LlvmToSvLibVisitor.visit_operand(aggregate_value, local_variables)

        svlib_right: Term = LlvmToSvLibVisitor.visit_operand(inserted_value, local_variables)

        # in SMT-LIB: (store array index element) for each index
        store_assigns: list[Statement] = []
        for index in instruction.indices:
            svlib_index_term: Term = Literal(index, SvLibFactory().int())
            store: Application = Application("store", (svlib_left, svlib_index_term, svlib_right))
            store_assigns.append(SvLibFactory().assign([(left_hand_side, store)]))

        return tuple(store_assigns)

    @staticmethod
    def visit_ret_instruction(
        instruction: InstructionRef,
        return_variable: Variable | None,
        local_variables: tuple[Variable, ...],
    ) -> tuple[Statement, ...]:
        # if there are no operands, then the instruction is 'ret void' -> just 'return'
        if len(instruction.operands) == 0:
            assert return_variable is None
            return tuple([SvLibFactory().returns()])

        # if there is an operand, create the return variable assignment and append 'return'
        LlvmLiteRefUtil.check_len_operands(instruction, 1)
        return_value: Term = LlvmToSvLibVisitor.visit_operand(instruction.operands[0], local_variables)
        return tuple([SvLibFactory().assign([(return_variable, return_value)]), SvLibFactory().returns()])

    @staticmethod
    def visit_operand_with_type(
        operand: OperandRef,
        local_variables: tuple[Variable, ...],
    ) -> tuple[Term | Label, Optional[Type]]:
        """
        Converts the given LLVM instruction operand into an SV-LIB Term, and optionally returns the Type of the Term,
        if applicable. If the type is not required by the caller, use 'visit_operand' instead.
        """
        match operand:
            case ConstantRef():
                svlib_sort = LlvmToSvLibVisitor.visit_type(operand.operand_type)
                value: str = operand.constant_value
                return Literal(
                    Fraction(value) if LlvmLiteRefUtil.is_float_type(operand.operand_type.type_kind) else value,
                    svlib_sort,
                ), svlib_sort

            case VariableRef():
                # search proc_locals for the name of the operand
                for local_variable in local_variables:
                    if local_variable.name == operand.name:
                        return local_variable, local_variable.sort

            case LabelRef():
                return Label(operand.name), None

        raise ValueError(f"Cannot extract operand: {operand}")

    @staticmethod
    def visit_operand(
        operand: OperandRef,
        local_variables: tuple[Variable, ...],
    ) -> Term | Label:
        operand, _ = LlvmToSvLibVisitor.visit_operand_with_type(operand, local_variables)
        return operand

    @staticmethod
    def visit_variable(llvm_variable: VariableRef, llvm_function: FunctionRef = None) -> Variable:
        svlib_sort = LlvmToSvLibVisitor.visit_type(llvm_variable.operand_type)
        svlib_procedure_name = llvm_function.name if llvm_function else None

        return Variable(llvm_variable.name, svlib_procedure_name, svlib_sort)

    @staticmethod
    def visit_local_variable(instruction: InstructionRef, function: FunctionRef) -> VariableRef:
        for local_variable in function.local_variables:
            if local_variable.name == instruction.local_variable.name:
                return local_variable

        raise RuntimeError(f"Cannot extract local variable from instruction {instruction}, function {function}")

    @staticmethod
    def visit_type(llvm_type: TypeRef) -> Sort | None:
        """
        Converts the given LLVM type to an appropriate SV-LIB Sort, or None if there is no corresponding SV-LIB Sort.
        For an overview of LLVMTypeKinds, see https://llvm.org/doxygen/group__LLVMCCoreTypes.html.
        """
        match llvm_type.type_kind:
            case LlvmTypeKind.void:
                return None

            # Floating point numbers as per IEEE 754. The hidden bit is included in the significand.
            # Reference: https://smt-lib.org/theories-FloatingPoint.shtml
            case LlvmTypeKind.half:
                return SvLibFactory().floating_point(5, 11)
            case LlvmTypeKind.float:
                return SvLibFactory().floating_point(8, 24)
            case LlvmTypeKind.double:
                return SvLibFactory().floating_point(11, 53)

            case LlvmTypeKind.integer:
                return SvLibFactory().bitvec(llvm_type.type_width)
            case LlvmTypeKind.array:
                element_type: TypeRef = next(llvm_type.elements)
                return SvLibFactory().array(SvLibFactory().int(), LlvmToSvLibVisitor.visit_type(element_type))
            case LlvmTypeKind.pointer:
                raise UnsupportedLlvmTypeKindException(llvm_type)

        raise ValueError(f"The following LLVMTypeKind is not handled by the implementation: {llvm_type}")
