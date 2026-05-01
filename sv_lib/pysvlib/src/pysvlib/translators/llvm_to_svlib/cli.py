# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path

from pysvlib.translators.cli import ProjectTranslatorCLI
from pysvlib.translators.llvm_to_svlib.translator import LlvmToSvLibTranslator


class LlvmToSvLibCLI(ProjectTranslatorCLI):
    def add_translation_arguments(self, parser: argparse.ArgumentParser) -> None:
        # Currently no LLVM translation specific arguments are needed.
        pass

    def command_name(self) -> str:
        return "llvm_to_svlib"

    def command_help(self) -> str:
        return "Translate LLVM programs to SV-LIB programs."

    def get_file_extension(self) -> str:
        return ".svlib"

    def run_translation(self, input_paths: list[Path], args: argparse.Namespace) -> str:
        if len(input_paths) > 1:
            raise NotImplementedError("Translating multiple targets is currently not supported.")

        return LlvmToSvLibTranslator.translate(input_paths)
