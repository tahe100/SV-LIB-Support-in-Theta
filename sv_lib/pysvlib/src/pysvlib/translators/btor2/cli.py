# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path

from pysvlib.svlib import parse_svlib, print_svlib
from pysvlib.translators import btor2_to_svlib
from pysvlib.translators.cli import AllFilesStandaloneCLI


class Btor2ToSvLibCLI(AllFilesStandaloneCLI):
    def add_translation_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass

    def command_name(self) -> str:
        return "btor2_to_svlib"

    def command_help(self) -> str:
        return "Translate BTOR2 programs to SV-LIB programs."

    def get_file_extension(self) -> str:
        return ".svlib"

    def valid_input_file_extensions(self) -> list[str]:
        return [".btor2"]

    def run_translation(self, input_file: Path, args: argparse.Namespace) -> str:
        commands = btor2_to_svlib(input_file.read_text())
        text = print_svlib(list(commands))
        parse_svlib(text)
        return text
