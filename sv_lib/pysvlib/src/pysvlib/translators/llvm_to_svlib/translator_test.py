# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path

from pysvlib.svlib import parse_svlib
from pysvlib.translators.llvm_to_svlib.translator import LlvmToSvLibTranslator


class TranslatorTest(unittest.TestCase):
    def test_array_insertvalue(self):
        self.llvm_translation_test_file("array-insertvalue-extractvalue")

    def test_function_return_value(self):
        self.llvm_translation_test_file("function-return-value")

    def test_math_operations(self):
        self.llvm_translation_test_file("math-operations")

    def test_math_operations_float(self):
        self.llvm_translation_test_file("math-operations-float")

    def test_numbers_as_identifiers(self):
        self.llvm_translation_test_file("numbers-as-identifiers")

    def test_recursion(self):
        self.llvm_translation_test_file("recursion")

    def test_simple_branch(self):
        self.llvm_translation_test_file("simple-branch")

    def test_function_arguments(self):
        self.llvm_translation_test_file("simple_function_arguments")

    @staticmethod
    def get_translation_test_programs_path():
        return Path(__file__).parent.absolute() / "test/translation"

    def llvm_translation_test_file(self, file_name: str):
        llvm_file_path: Path = TranslatorTest.get_translation_test_programs_path() / f"{file_name}.ll"
        svlib_program: str = LlvmToSvLibTranslator.translate([llvm_file_path])
        # ensure the resulting string is not empty
        self.assertTrue(svlib_program)
        # ensure that parsing the resulting string to SV-LIB returns a non-empty list of SV-LIB statements
        self.assertTrue(parse_svlib(svlib_program))
