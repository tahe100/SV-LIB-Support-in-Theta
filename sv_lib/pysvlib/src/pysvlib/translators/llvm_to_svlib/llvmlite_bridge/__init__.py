# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from .llvmlite_ref import (
    BlockRef,
    ConstantRef,
    FunctionRef,
    InstructionRef,
    LabelRef,
    LlvmLiteRef,
    LlvmModuleRef,
    OperandRef,
    VariableRef,
)
from .llvmlite_ref_visitor import LlvmLiteRefVisitor

# Export only the visit_module function. Users should never be able to create ValueRef by themselves but only ModuleRef
# by parsing LLVM IR, so all other visit functions that work on ValueRef should remain hidden.
visit_module = LlvmLiteRefVisitor.visit_module

__all__ = [
    "BlockRef",
    "ConstantRef",
    "FunctionRef",
    "InstructionRef",
    "LabelRef",
    "LlvmLiteRef",
    "LlvmModuleRef",
    "OperandRef",
    "VariableRef",
    "visit_module",
]
