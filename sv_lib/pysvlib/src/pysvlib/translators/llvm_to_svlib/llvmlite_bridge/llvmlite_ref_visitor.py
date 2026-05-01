# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import re
from itertools import chain

from llvmlite.binding import ModuleRef, TypeKind, TypeRef, ValueKind, ValueRef

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


class LlvmLiteRefVisitor:
    @staticmethod
    def visit_module(module_ref: ModuleRef, name_prefix: str) -> LlvmModuleRef:
        """
        Visits the given llvmlite ModuleRef and returns an LlvmModuleRef that unpacks all ValueRefs to ensure:

        - There are no circular references between operands.
        - Block label and instruction names that are empty (e.g. because they consisted only of numbers such as '%1')
          which are empty strings in llvmlite) are assigned a unique name that is used consistently across references.
        - Instructions with trailing constant integer indices such as 'insertvalue' are parsed, because these are not
          available as operands in llvmlite.

        Parameters:
            module_ref: The ModuleRef instance as returned by the llvmlite binding after parsing LLVM IR.
            name_prefix: The prefix given to global variable and function names to prevent naming collisions between
            different modules.
        """
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        global_variables: tuple[VariableRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_global_variable(global_variable, name_prefix)
            for global_variable in module_ref.global_variables
        )
        functions: tuple[FunctionRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_function(function, name_prefix) for function in module_ref.functions
        )
        return LlvmModuleRef(module_ref.name, global_variables, functions)

    @staticmethod
    def visit_global_variable(global_variable: ValueRef, name_prefix: str) -> VariableRef:
        LlvmLiteRefUtil.check_is_global(global_variable)
        LlvmLiteRefUtil.check_is_variable(global_variable)
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        return LlvmLiteRefVisitor.build_global_variable_ref(
            global_variable.type, global_variable.value_kind, name_prefix, global_variable.name
        )

    @staticmethod
    def visit_function(function: ValueRef, name_prefix: str) -> FunctionRef:
        LlvmLiteRefUtil.check_is_function(function)
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        function_type: TypeRef = function.global_value_type.get_function_return()

        arguments: tuple[VariableRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_argument(argument, function) for argument in function.arguments
        )
        blocks: tuple[BlockRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_block(block, function, name_prefix) for block in function.blocks
        )

        local_variables: list[VariableRef] = []
        for block in blocks:
            for instruction in block.instructions:
                if instruction.local_variable is not None:
                    local_variables.append(instruction.local_variable)

        return FunctionRef(
            LlvmLiteRefVisitor.build_prefixed_name(name_prefix, function.name),
            function_type,
            arguments,
            blocks,
            tuple(local_variables),
        )

    @staticmethod
    def visit_argument(argument: ValueRef, function: ValueRef) -> VariableRef:
        LlvmLiteRefUtil.check_is_argument(argument)
        LlvmLiteRefUtil.check_is_function(function)

        return LlvmLiteRefVisitor.build_argument_variable_ref(argument, function)

    @staticmethod
    def visit_block(block: ValueRef, function: ValueRef, name_prefix: str) -> BlockRef:
        LlvmLiteRefUtil.check_is_block(block)
        LlvmLiteRefUtil.check_is_function(function)
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        label: LabelRef = LlvmLiteRefVisitor.build_label_ref(block, function)
        instructions: tuple[InstructionRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_instruction(instruction, function, name_prefix)
            for instruction in block.instructions
        )
        return BlockRef(label, instructions)

    @staticmethod
    def visit_instruction(instruction: ValueRef, function: ValueRef, name_prefix: str) -> InstructionRef:
        LlvmLiteRefUtil.check_is_instruction(instruction)
        LlvmLiteRefUtil.check_is_function(function)
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        local_variable: VariableRef | None = LlvmLiteRefVisitor.try_build_local_variable_ref(instruction, function)

        llvm_opcode: LlvmOpCode = LlvmOpCode(instruction.opcode)
        condition_code: str | None = LlvmLiteRefVisitor.visit_instruction_condition_code(instruction, llvm_opcode)
        operands: tuple[OperandRef, ...] = tuple(
            LlvmLiteRefVisitor.visit_operand(operand, function, name_prefix) for operand in instruction.operands
        )
        indices: tuple[int, ...] = LlvmLiteRefVisitor.visit_instruction_indices(instruction, llvm_opcode)

        return InstructionRef(
            instruction.__str__(),
            local_variable,
            instruction.type,
            llvm_opcode,
            instruction.is_constant,
            condition_code,
            tuple(operands),
            indices,
        )

    @staticmethod
    def visit_instruction_condition_code(instruction: ValueRef, llvm_opcode: LlvmOpCode) -> str | None:
        """
        Returns the str condition code used to define the type of comparison to perform.
        Example: for '%cond = icmp eq i32 %a, 0' it returns 'eq'
        """
        LlvmLiteRefUtil.check_is_instruction(instruction)

        if not llvm_opcode.has_condition_code:
            return None

        return str(instruction).split()[3]

    @staticmethod
    def visit_operand(operand: ValueRef, function: ValueRef, name_prefix: str) -> OperandRef:
        LlvmLiteRefUtil.check_is_operand(operand)
        LlvmLiteRefUtil.check_is_function(function)
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        if operand.is_constant:
            return ConstantRef(
                operand.type,
                operand.value_kind,
                LlvmLiteRefVisitor.build_prefixed_name(name_prefix, operand.name)
                if operand.value_kind == ValueKind.function
                else operand.name,
                operand.get_constant_value(),
            )

        if operand.is_global:
            return LlvmLiteRefVisitor.build_global_variable_ref(
                operand.type, operand.value_kind, name_prefix, operand.name
            )

        # using operand.is_argument does not work here, so we check if it is inside the functions arguments
        if operand in function.arguments:
            return LlvmLiteRefVisitor.build_argument_variable_ref(operand, function)

        # operands can be labels, e.g., in 'br i1 %cond, label %if, label %else'
        if operand.type.type_kind == TypeKind.label:
            return LlvmLiteRefVisitor.build_label_ref(operand, function)

        local_variable: VariableRef | None = LlvmLiteRefVisitor.try_build_local_variable_ref(operand, function)

        if local_variable is None:
            raise ValueError(f"The following operand ValueRef could not be resolved to an OperandRef: {operand}")

        return local_variable

    @staticmethod
    def visit_instruction_indices(instruction: ValueRef, llvm_opcode: LlvmOpCode) -> tuple[int, ...]:
        """
        Returns the tuple of trailing indices in 'insertvalue' and 'extractvalue' instructions. The trailing indices are
        not part of the operands, or the ValueRef binding in general, so they have to be parsed here.

        Reference: https://llvm.org/docs/LangRef.html#insertvalue-instruction

        Example:
            For '%arr1 = insertvalue [2 x i32] undef, i32 1, 0' it returns [0].
        """
        LlvmLiteRefUtil.check_is_instruction(instruction)

        if not llvm_opcode.has_indices:
            return tuple()

        # this regex looks for trailing comma-separated integers at the end of the IR line
        matches = re.findall(r", (\d+)(?=\s*$|\s*;)", str(instruction))
        return tuple(int(m) for m in matches)

    # VariableRef Builder Methods

    @staticmethod
    def try_build_local_variable_ref(value_ref: ValueRef, function: ValueRef) -> VariableRef | None:
        LlvmLiteRefUtil.check_is_function(function)

        if len(value_ref.name) > 0:
            return VariableRef(value_ref.type, value_ref.value_kind, value_ref.name, False, False, function.name)

        # if the instruction has no "=" as the second token, then it has no register that stores the local_variable
        if value_ref.__str__().split()[1] != "=":
            return None

        # if the variable has no name, then it can be a number '%3 = add i32 %0, %1' -> try to create a unique name
        for i, instr in enumerate(chain.from_iterable(block.instructions for block in function.blocks)):
            if instr == value_ref:
                instruction_index = i
                break
        else:
            raise ValueError(f"Instruction {value_ref} not found in function {function}.")

        variable_name: str = f"{function.name}_variable{instruction_index}"
        return VariableRef(value_ref.type, value_ref.value_kind, variable_name, False, False, function.name)

    @staticmethod
    def build_global_variable_ref(type_ref: TypeRef, value_kind: ValueKind, name_prefix: str, name: str) -> VariableRef:
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        return VariableRef(
            type_ref, value_kind, LlvmLiteRefVisitor.build_prefixed_name(name_prefix, name), True, False, None
        )

    @staticmethod
    def build_argument_variable_ref(value_ref: ValueRef, function: ValueRef) -> VariableRef:
        LlvmLiteRefUtil.check_is_function(function)

        if len(value_ref.name) > 0:
            return VariableRef(value_ref.type, value_ref.value_kind, value_ref.name, False, True, function.name)

        # if the argument has no name, then it is e.g. a number 'i32 %0' -> create a unique name
        for i, arg in enumerate(function.arguments):
            if arg == value_ref:
                argument_index = i
                break
        else:
            raise ValueError(f"Argument {value_ref} not found in function {function}.")

        argument_name: str = f"{function.name}_argument{argument_index}"
        return VariableRef(value_ref.type, value_ref.value_kind, argument_name, False, True, function.name)

    # LabelRef Builder Methods

    @staticmethod
    def build_label_ref(label: ValueRef, function: ValueRef) -> LabelRef:
        LlvmLiteRefUtil.check_is_function(function)

        if len(label.name) > 0:
            return LabelRef(label.type, label.value_kind, label.name, function.name)

        # if the label has no name, then it is e.g. a number '0:' -> create a unique name
        for i, block in enumerate(function.blocks):
            if block == label:
                label_index = i
                break
        else:
            raise ValueError(f"Label {label} not found in function {function}.")

        label_name: str = f"{function.name}_label{label_index}"
        return LabelRef(label.type, label.value_kind, label_name, function.name)

    # Name Methods

    @staticmethod
    def build_prefixed_name(name_prefix: str, name: str):
        LlvmLiteRefUtil.check_str_not_empty(name_prefix)

        return name_prefix + name
