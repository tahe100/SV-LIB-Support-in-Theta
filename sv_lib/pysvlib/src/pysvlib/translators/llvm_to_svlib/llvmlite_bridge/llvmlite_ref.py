# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

# necessary so that ModuleRef can have GlobalVariableRef (which is declared below) as parameter
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from llvmlite.binding import TypeRef, ValueKind

from pysvlib.translators.llvm_to_svlib.llvm_opcode import LlvmOpCode


class LlvmLiteRef(ABC):  # noqa B024
    pass


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class LlvmModuleRef(LlvmLiteRef):
    """
    Represents an LLVMModuleRef: https://llvm.org/doxygen/classllvm_1_1Module.html
    """

    name: str
    global_variables: tuple[VariableRef, ...] = field(default_factory=tuple)
    functions: tuple[FunctionRef, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for global_variable in self.global_variables:
            if not global_variable.is_global:
                raise ValueError(f"is_global is False for global_variable {global_variable}.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class OperandRef(LlvmLiteRef, ABC):
    """
    Abstract base for an operand with a type used in an instruction, e.g., 'a' and  '42' in '%sum = add i32 %a, 42'.

    Represents an operand LLVMValueRef: https://llvm.org/doxygen/classllvm_1_1Value.html

    Note:
         FunctionRef, BlockRef and InstructionRef are not OperandRef even though they are LLVMValueRef and can be used
         as operands in the LLVM standard. The exclusion of FunctionRef, BlockRef and InstructionRef is done to prevent
         circular references.
    """

    operand_type: TypeRef
    value_kind: ValueKind
    name: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class VariableRef(OperandRef):
    """
    A global, local, or argument variable that always has a name, e.g., 'sum' and 'a' in '%sum = add i32 %a, 42'
    Local variables are 'declared' in instructions, e.g. '%a = or i1 0, 0' corresponds to 'bool a = 0'.
    Argument for a function are declared in the signature, e.g. 'arg' in 'define i32 @func(i32 %arg)'.
    """

    is_global: bool
    is_argument: bool
    function_name: str | None

    def __post_init__(self):
        if len(self.name) == 0:
            raise ValueError("The name of a VariableRef cannot be empty.")

        if self.function_name is not None and len(self.function_name) == 0:
            raise ValueError("VariableRef function_name is empty.")

        if self.is_global:
            if self.is_argument:
                raise ValueError("If is_argument is True, then is_global cannot be True.")
            if self.function_name is not None:
                raise ValueError("If is_global is True, then function_name must be None.")

        if self.is_argument:
            if self.is_global:
                raise ValueError("If is_argument is True, then is_global cannot be True.")
            if self.function_name is None:
                raise ValueError("If is_argument is True, then function_name cannot be None.")

        if not self.is_global and self.function_name is None:
            raise ValueError("If is_global is False (= a local variable), then function_name cannot be None.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class ConstantRef(OperandRef):
    """
    A constant operand, e.g., '42' in '%sum = add i32 %a, 42'.
    """

    constant_value: str | int

    def __post_init__(self):
        if len(self.name) > 0 and not self.value_kind == ValueKind.function:
            raise ValueError("If ConstantRef has a name, then its ValueKind must be a function.")

        if isinstance(self.constant_value, str) and len(self.constant_value) == 0:
            raise ValueError("ConstantRef constant_value is empty.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class LabelRef(OperandRef):
    """
    A label operand, e.g., '%if' and '%else' in 'br i1 %cond, label %if, label %else'
    """

    function_name: str

    def __post_init__(self):
        if len(self.name) == 0:
            raise ValueError("The name of a LabelRef cannot be empty.")

        if len(self.function_name) == 0:
            raise ValueError("LabelRef function_name is empty.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class FunctionRef(LlvmLiteRef):
    """
    A function with name, return type, arguments, blocks (must be non-empty) and local variables.

    Represents a function LLVMValueRef: https://llvm.org/doxygen/classllvm_1_1Value.html
    """

    name: str
    return_type: TypeRef
    arguments: tuple[VariableRef, ...] = field(default_factory=tuple)
    blocks: tuple[BlockRef, ...] = field(default_factory=tuple)
    local_variables: tuple[VariableRef, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if len(self.blocks) == 0:
            raise ValueError("FunctionRef blocks is empty.")

        for argument in self.arguments:
            if not argument.is_argument:
                raise ValueError(f"is_argument is False for argument {argument}.")

        for local_variable in self.local_variables:
            if local_variable.is_global:
                raise ValueError(f"is_global is True for local_variable {local_variable}.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class BlockRef(LlvmLiteRef):
    """
    A block that always starts with a label, followed by a non-empty tuple of instructions.

    Represents a block LLVMValueRef: https://llvm.org/doxygen/classllvm_1_1Value.html
    """

    label: LabelRef
    instructions: tuple[InstructionRef, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if len(self.instructions) == 0:
            raise ValueError("BlockRef instructions is empty.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class InstructionRef(LlvmLiteRef):
    """
    Represents an instruction LLVMValueRef: https://llvm.org/doxygen/classllvm_1_1Value.html
    """

    original_instruction: str
    local_variable: VariableRef | None
    instruction_type: TypeRef | None
    opcode: LlvmOpCode
    is_constant: bool | None
    condition_code: str | None
    operands: tuple[OperandRef, ...] = field(default_factory=tuple)
    indices: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.opcode.has_condition_code:
            if self.condition_code is None:
                raise ValueError(f"LlvmOpCode {self.opcode} requires a condition_code, but got None.")
        else:
            if self.condition_code is not None:
                raise ValueError(
                    f"LlvmOpCode {self.opcode} has_condition_code is False, "
                    f"but condition_code is not None: {self.condition_code}."
                )

        if self.opcode.has_indices:
            if len(self.indices) == 0:
                raise ValueError(f"LlvmOpCode {self.opcode} requires indices, but indices are empty.")
        else:
            if len(self.indices) > 0:
                raise ValueError(
                    f"LlvmOpCode {self.opcode} has_indices is False, but indices are not empty: {self.indices}."
                )
