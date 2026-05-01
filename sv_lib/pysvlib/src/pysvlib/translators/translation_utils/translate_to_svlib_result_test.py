# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path

from llvmlite.binding import ModuleRef

from pysvlib.translators.llvm_to_svlib.llvm_to_svlib_visitor import LlvmToSvLibVisitor
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref import LlvmModuleRef
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref_visitor import LlvmLiteRefVisitor
from pysvlib.translators.llvm_to_svlib.translator import LlvmToSvLibTranslator
from pysvlib.translators.llvm_to_svlib.translator_test import TranslatorTest
from pysvlib.translators.translation_utils.translate_to_svlib_result import TranslateToProcedureResult


class ToSvLibVisitResultsTest(unittest.TestCase):
    def test_procedure_pools(self):
        llvm_file_path: Path = TranslatorTest.get_translation_test_programs_path() / "recursion.ll"
        module_ref: ModuleRef = LlvmToSvLibTranslator.init_llvm_module_ref(llvm_file_path)

        name_prefix: str = "file0_"

        llvm_module_ref: LlvmModuleRef = LlvmLiteRefVisitor.visit_module(module_ref, name_prefix)
        sorted_procedure_pools, recursive_pool_names = LlvmToSvLibVisitor.visit_function_pools(llvm_module_ref, tuple())

        self.assertEqual(len(recursive_pool_names), 3)

        self.assertIn(frozenset({name_prefix + "direct_recursion"}), recursive_pool_names)
        self.assertIn(
            frozenset({name_prefix + "indirect_recursion_pairA", name_prefix + "indirect_recursion_pairB"}),
            recursive_pool_names,
        )
        self.assertIn(
            frozenset(
                {
                    name_prefix + "indirect_recursion_triangle1",
                    name_prefix + "indirect_recursion_triangle2",
                    name_prefix + "indirect_recursion_triangle3",
                }
            ),
            recursive_pool_names,
        )

        # The procedure pool graph looks as follows with node -> {targeted_nodes}:
        # main -> {direct_recursion, recursive_pair, recursive_triangle, no_recursion}
        # direct_recursion -> {direct_recursion}
        # recursive_pair -> {recursive_triangle}
        # recursive_triangle -> {}
        # no_recursion -> {}

        # test topological sort order (called_proc_name index < caller index)
        idx_main = ToSvLibVisitResultsTest.get_pool_index(name_prefix + "main", sorted_procedure_pools)
        idx_direct = ToSvLibVisitResultsTest.get_pool_index(name_prefix + "direct_recursion", sorted_procedure_pools)
        idx_pair = ToSvLibVisitResultsTest.get_pool_index(
            name_prefix + "indirect_recursion_pairA", sorted_procedure_pools
        )
        idx_triangle = ToSvLibVisitResultsTest.get_pool_index(
            name_prefix + "indirect_recursion_triangle1", sorted_procedure_pools
        )
        idx_none = ToSvLibVisitResultsTest.get_pool_index(name_prefix + "no_recursion", sorted_procedure_pools)

        # Main calls everything, so it must be last (highest index)
        self.assertGreater(idx_main, idx_direct)
        self.assertGreater(idx_main, idx_pair)
        self.assertGreater(idx_main, idx_triangle)
        self.assertGreater(idx_main, idx_none)

        # recursive_pair calls recursive_triangle, so triangle must come first
        self.assertGreater(idx_pair, idx_triangle)

    @staticmethod
    def get_pool_index(
        proc_name: str, sorted_procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...]
    ) -> int:
        for i, pool in enumerate(sorted_procedure_pools):
            if any(proc.name == proc_name for proc in pool):
                return i

        raise ValueError(f"Procedure {proc_name} not found in any pool")
