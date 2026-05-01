# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path
from typing import Type

from llvmlite.ir import PointerType

from pysvlib.translators.llvm_to_svlib.exceptions.llvm_to_svlib_exceptions import (
    UnsupportedLlvmOpcodeException,
    UnsupportedLlvmTypeKindException,
)
from pysvlib.translators.llvm_to_svlib.llvm_opcode import LlvmOpCode
from pysvlib.translators.llvm_to_svlib.translator import LlvmToSvLibTranslator


class ExceptionTest(unittest.TestCase):
    def test_duplicate_function_name(self):
        self.llvm_translation_test_exception(
            "duplicate-function-name", RuntimeError, "define i32 @function_duplicate()"
        )

    def test_duplicate_register_name(self):
        self.llvm_translation_test_exception("duplicate-register-name", RuntimeError, "%sum = add i32 0, 0")

    def test_undefined_function(self):
        self.llvm_translation_test_exception("undefined-function", RuntimeError, "call void @undefined_function(i32 1)")

    def test_unsupported_opcode_exception(self):
        self.llvm_translation_test_exception("phi-node", UnsupportedLlvmOpcodeException, LlvmOpCode.PHI.__str__())

    def test_unsupported_type_kind_exception(self):
        self.llvm_translation_test_exception(
            "reject-pointer", UnsupportedLlvmTypeKindException, PointerType()._to_string()
        )

    def llvm_translation_test_exception(
        self, file_name: str, expected_exception: Type[Exception], expected_in_message: str
    ):
        # check that calling the translation with this file raises the specific error
        with self.assertRaises(expected_exception) as exception_context:
            llvm_file_path: Path = Path(__file__).parent.absolute() / "../test/exceptions" / f"{file_name}.ll"
            LlvmToSvLibTranslator.translate([llvm_file_path])

        # verify the error message contains the expected substring
        self.assertIn(expected_in_message, str(exception_context.exception))
