# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from abc import ABC

from llvmlite.binding import TypeRef

from pysvlib.translators.llvm_to_svlib.llvm_opcode import LlvmOpCode
from pysvlib.translators.translation_exception import TranslationException


class LlvmToSvLibException(TranslationException, ABC):
    def __init__(self, message):
        super().__init__(message)


class UnsupportedLlvmOpcodeException(LlvmToSvLibException):
    def __init__(self, llvm_opcode: LlvmOpCode):
        super().__init__(f"The following LLVM opcode is unsupported: {llvm_opcode}")


class UnsupportedLlvmTypeKindException(LlvmToSvLibException):
    def __init__(self, llvm_type: TypeRef):
        super().__init__(f"The following LLVM type kind is unsupported: {llvm_type}")
