# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

# necessary so that LlvmOpCode can be used in @staticmethod
from __future__ import annotations

from enum import Enum


class LlvmOpCode(Enum):
    """
    An enumeration of LLVM opcodes.
    Overview of LLVM instructions: https://llvm.org/docs/LangRef.html#instruction-reference
    """

    ADD = ("add", False, False, 2, 2)
    ALLOCATE = ("alloca", False, False, 1, 1)
    BRANCH = ("br", False, False, 1, 3, tuple([2]))
    # function calls require at least the name of the function or a function pointer as operand.
    CALL = ("call", False, False, 1)
    EXTRACT_VALUE = ("extractvalue", False, True, 1, 1)
    FLOAT_ADD = ("fadd", False, False, 2, 2)
    FLOAT_COMPARISON = ("fcmp", True, False, 2, 2)
    FLOAT_DIVISION = ("fdiv", False, False, 2, 2)
    FLOAT_MULTIPLY = ("fmul", False, False, 2, 2)
    FLOAT_REMAINDER = ("frem", False, False, 2, 2)
    FLOAT_SUBTRACT = ("fsub", False, False, 2, 2)
    INSERT_VALUE = ("insertvalue", False, True, 2, 2)
    INTEGER_COMPARISON = ("icmp", True, False, 2, 2)
    LOAD = ("load", False, False, 1, 1)
    MULTIPLY = ("mul", False, False, 2, 2)
    PHI = ("phi", False, False, 2, 2)
    RETURN = ("ret", False, False, 0, 1)
    SIGNED_DIVISION = ("sdiv", False, False, 2, 2)
    SIGNED_REMAINDER = ("srem", False, False, 2, 2)
    STORE = ("store", False, False, 2, 2)
    SUBTRACT = ("sub", False, False, 2, 2)
    UNSIGNED_REMAINDER = ("urem", False, False, 2, 2)

    def __init__(
        self,
        opcode: str,
        has_condition_code: bool,
        has_indices: bool,
        min_operands: int,
        max_operands: int | None = None,
        excluded_operands: tuple[int, ...] | None = None,
    ):
        """
        Parameters:
            opcode: The string opcode as it appears in the LLVM source code.
            has_condition_code: Whether the opcode has a condition code, e.g., 'eq' for equality in integer comparisons.
            has_indices: Whether the opcode has a list of integer indices as suffix, e.g., in array insertions.
            min_operands: Defines the minimum amount of operands that the opcode must have.
            max_operands: Defines the maximum amount of operands that the opcode can have, optional because some opcodes
                can have any amount of operands.
            excluded_operands: Defines the excluded amount of operands between min_operands and max_operands. All
                elements must be strictly greater than min_operands and strictly less than max_operands (if max_operands
                is not None). This parameter is optional because most opcodes allow all amounts within
                [min_operands; max_operands].
        """
        if max_operands is not None and min_operands > max_operands:
            raise ValueError(f"min_operands {min_operands} cannot be greater than max_operands {max_operands}.")

        if excluded_operands is not None:
            for excluded_operand in excluded_operands:
                if excluded_operand <= min_operands:
                    raise ValueError(
                        f"All excluded_operands {excluded_operands} must be greater than min_operands {min_operands}."
                    )
                if max_operands is not None and excluded_operand >= max_operands:
                    raise ValueError(
                        f"All excluded_operands {excluded_operands} must be smaller than max_operands {min_operands}."
                    )

        self.opcode = opcode
        self.has_condition_code = has_condition_code
        self.has_indices = has_indices
        self.min_operands = min_operands
        self.max_operands = max_operands
        self.excluded_operands = excluded_operands

    @classmethod
    def _missing_(cls, value):
        """A helper method to match LlvmOpCodes by string via LlvmOpCode(opcode_string)."""
        for member in cls:
            if member.opcode == value:
                return member
        return super()._missing_(value)

    @staticmethod
    def check_is_allowed_num_operands(llvm_opcode: LlvmOpCode, num_operands: int):
        if num_operands < llvm_opcode.min_operands:
            raise ValueError(
                f"The amount of operands {num_operands} is smaller than the minimum for {llvm_opcode}: "
                f"{llvm_opcode.min_operands}."
            )

        if llvm_opcode.max_operands is not None and num_operands > llvm_opcode.max_operands:
            raise ValueError(
                f"The amount of operands {num_operands} is higher than the maximum for {llvm_opcode}: "
                f"{llvm_opcode.max_operands}."
            )

        if llvm_opcode.excluded_operands is not None and num_operands in llvm_opcode.excluded_operands:
            raise ValueError(f"The amount of operands {num_operands} is excluded {llvm_opcode.excluded_operands}.")
