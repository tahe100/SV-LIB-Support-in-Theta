# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path

from llvmlite.binding import ModuleRef

from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref import BlockRef, FunctionRef, InstructionRef
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref_visitor import LlvmLiteRefVisitor
from pysvlib.translators.llvm_to_svlib.translator import LlvmToSvLibTranslator
from pysvlib.translators.llvm_to_svlib.translator_test import TranslatorTest


class LlvmLiteRefVisitorTest(unittest.TestCase):
    def test_array_insertvalue_extractvalue(self):
        llvm_file_path: Path = TranslatorTest.get_translation_test_programs_path() / "array-insertvalue-extractvalue.ll"
        module_ref: ModuleRef = LlvmToSvLibTranslator.init_llvm_module_ref(llvm_file_path)

        functions: list[FunctionRef] = [
            LlvmLiteRefVisitor.visit_function(function, "file0") for function in module_ref.functions
        ]
        self.assertEqual(len(functions), 1)

        function: FunctionRef = functions[0]
        self.assertEqual(len(function.blocks), 1)

        block: BlockRef = function.blocks[0]
        self.assertEqual(len(block.instructions), 4)

        insertvalue_instruction_1: InstructionRef = block.instructions[0]
        self.assertEqual(insertvalue_instruction_1.indices, tuple([0]))

        insertvalue_instruction_2: InstructionRef = block.instructions[1]
        self.assertEqual(insertvalue_instruction_2.indices, tuple([1]))

        extractvalue_instruction: InstructionRef = block.instructions[2]
        self.assertEqual(extractvalue_instruction.indices, tuple([0]))

    def test_function_return_value(self):
        llvm_file_path: Path = TranslatorTest.get_translation_test_programs_path() / "function-return-value.ll"
        module_ref: ModuleRef = LlvmToSvLibTranslator.init_llvm_module_ref(llvm_file_path)

        functions: list[FunctionRef] = [
            LlvmLiteRefVisitor.visit_function(function, "file0_") for function in module_ref.functions
        ]
        self.assertEqual(len(functions), 5)

        one_param_no_ret_function: FunctionRef = functions[0]
        self.assertEqual(len(one_param_no_ret_function.blocks), 1)
        self.assertEqual(len(one_param_no_ret_function.arguments), 1)
        one_param_no_ret_block: BlockRef = one_param_no_ret_function.blocks[0]
        self.assertEqual(len(one_param_no_ret_block.instructions), 2)
        one_param_no_ret_instr1: InstructionRef = one_param_no_ret_block.instructions[0]
        self.assertIsNotNone(one_param_no_ret_instr1.local_variable)
        one_param_no_ret_instr2: InstructionRef = one_param_no_ret_block.instructions[1]
        self.assertIsNone(one_param_no_ret_instr2.local_variable)

        main_function: FunctionRef = functions[4]
        self.assertEqual(len(main_function.blocks), 1)
        self.assertEqual(len(main_function.arguments), 0)
        main_block: BlockRef = main_function.blocks[0]
        self.assertEqual(len(main_block.instructions), 5)
        main_instr1: InstructionRef = main_block.instructions[0]
        self.assertIsNotNone(main_instr1.local_variable)
        main_instr2: InstructionRef = main_block.instructions[1]
        self.assertIsNone(main_instr2.local_variable)

    def test_numbers_as_identifiers(self):
        llvm_file_path: Path = TranslatorTest.get_translation_test_programs_path() / "numbers-as-identifiers.ll"
        module_ref: ModuleRef = LlvmToSvLibTranslator.init_llvm_module_ref(llvm_file_path)

        functions: list[FunctionRef] = [
            LlvmLiteRefVisitor.visit_function(function, "file0_") for function in module_ref.functions
        ]
        self.assertEqual(len(functions), 1)

        function: FunctionRef = functions[0]
        self.assertEqual(len(function.blocks), 2)
        self.assertEqual(len(function.arguments), 2)
        block1: BlockRef = function.blocks[0]
        self.assertNotIn("2", block1.label.name)
        self.assertEqual(len(block1.instructions), 3)

        # %3 = add i32 %0, %1
        instr1: InstructionRef = block1.instructions[0]
        self.assertIsNotNone(instr1.local_variable)
        self.assertEqual(len(instr1.operands), 2)
        self.assertTrue(instr1.operands[0].is_argument)
        self.assertTrue(instr1.operands[1].is_argument)

        # %4 = mul i32 %3, 2
        instr2: InstructionRef = block1.instructions[1]
        self.assertIsNotNone(instr2.local_variable)
        self.assertEqual(len(instr2.operands), 2)
        self.assertFalse(instr2.operands[0].is_argument)
        self.assertEqual(instr2.operands[1].constant_value, 2)

        # branch instruction has no return register: br label %5
        instr3: InstructionRef = block1.instructions[2]
        self.assertIsNone(instr3.local_variable)
