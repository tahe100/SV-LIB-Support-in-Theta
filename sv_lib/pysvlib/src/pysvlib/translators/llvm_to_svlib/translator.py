# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from llvmlite import binding
from llvmlite.binding import ModuleRef

from pysvlib.svlib import parse_svlib, print_svlib
from pysvlib.svlib.syntax import Command
from pysvlib.translators.llvm_to_svlib.llvm_to_svlib_visitor import LlvmToSvLibVisitor
from pysvlib.translators.llvm_to_svlib.llvmlite_bridge.llvmlite_ref_visitor import LlvmLiteRefVisitor


class LlvmToSvLibTranslator:
    @staticmethod
    def translate(llvm_program_paths: list[Path]) -> str:
        svlib_program: list[Command] = []

        # translate each LLVM file into SV-LIB commands
        for i, path in enumerate(llvm_program_paths):
            module_ref = LlvmToSvLibTranslator.init_llvm_module_ref(path)

            llvm_module_ref = LlvmLiteRefVisitor.visit_module(module_ref, f"file{i}_")
            svlib_program += LlvmToSvLibVisitor.visit_module(llvm_module_ref)

        # create a single SV-LIB file from all LLVM files
        svlib_program: str = print_svlib(svlib_program)
        _ = parse_svlib(svlib_program)

        return svlib_program

    @staticmethod
    def init_llvm_module_ref(llvm_program_path: Path) -> ModuleRef:
        # initialize LLVM binding
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        # load LLVM IR from file, open as UTF-8 explicitly, and parse
        llvm_ir = llvm_program_path.read_text(encoding="utf-8")
        module_ref: ModuleRef = binding.parse_assembly(llvm_ir)
        module_ref.verify()

        return module_ref
