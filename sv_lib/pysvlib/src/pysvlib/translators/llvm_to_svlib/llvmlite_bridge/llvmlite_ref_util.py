# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from llvmlite.binding import TypeKind, ValueKind, ValueRef

from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref import InstructionRef


class LlvmLiteRefUtil:
    # ValueRef checks
    #
    # see https://llvmlite.readthedocs.io/en/latest/user-guide/binding/value-references.html#llvmlite.binding.ValueRef
    # for possible attributes on the ValueRef binding

    @staticmethod
    def check_is_global(variable: ValueRef):
        if not variable.is_global:
            raise ValueError(f"The given parameter is not global {variable}, but a {type(variable)}")
        if not variable.value_kind == ValueKind.global_variable:
            raise ValueError(f"The given parameters ValueKind is not global_variable, but {variable.value_kind}")

    @staticmethod
    def check_is_function(function: ValueRef):
        if not function.is_function:
            raise ValueError(f"The given parameter is not a function {function}, but a {type(function)}")
        if not function.value_kind == ValueKind.function:
            raise ValueError(f"The given parameters ValueKind is not function, but {function.value_kind}")

    @staticmethod
    def check_is_argument(argument: ValueRef):
        if not argument.is_argument:
            raise ValueError(f"The given parameter is not an argument {argument}, but a {type(argument)}")
        if not argument.value_kind == ValueKind.argument:
            raise ValueError(f"The given parameters ValueKind is not argument, but {argument.value_kind}")

    @staticmethod
    def check_is_block(block: ValueRef):
        if not block.is_block:
            raise ValueError(f"The given parameter is not a block {block}, but a {type(block)}")
        if not block.value_kind == ValueKind.basic_block:
            raise ValueError(f"The given parameters ValueKind is not basic_block, but {block.value_kind}")

    @staticmethod
    def check_is_instruction(instruction: ValueRef):
        if not instruction.is_instruction:
            raise ValueError(f"The given parameter is not an instruction: {instruction}, but a {type(instruction)}")
        if not instruction.value_kind == ValueKind.instruction:
            raise ValueError(f"The given parameters ValueKind is not instruction, but {instruction.value_kind}")

    @staticmethod
    def check_is_variable(variable: ValueRef):
        # if the name of ValueRef is empty, e.g. in 'store i32 %x0, i32* %x', then there is no variable
        if len(variable.name) == 0:
            raise ValueError(f"The given parameter is not a variable {variable}, but a {type(variable)}")
        # instructions with registers that store results such as %result = add i32 %a, %b are treated as variables
        if not variable.value_kind == ValueKind.instruction:
            raise ValueError(f"The given parameters ValueKind is not instruction, but {variable.value_kind}")

    @staticmethod
    def check_is_constant(constant: ValueRef):
        if not constant.is_constant:
            raise ValueError(f"The given parameter is not a constant {constant}, but a {type(constant)}")

    @staticmethod
    def check_is_operand(operand: ValueRef):
        if not operand.is_operand:
            raise ValueError(f"The given parameter is not an operand {operand}, but a {type(operand)}")

    # LlvmLiteRef checks

    @staticmethod
    def check_len_operands(instruction: InstructionRef, expected_len: int):
        if len(instruction.operands) != expected_len:
            raise ValueError(
                f"Expected {expected_len} operands, but got {len(instruction.operands)} for instruction {instruction}"
            )

    # Custom checks

    @staticmethod
    def check_str_not_empty(string: str):
        if len(string) == 0:
            raise ValueError("The string is empty.")

    # boolean helpers

    @staticmethod
    def is_float_type(llvm_type_kind: TypeKind) -> bool:
        return llvm_type_kind == TypeKind.half or llvm_type_kind == TypeKind.float or llvm_type_kind == TypeKind.double
