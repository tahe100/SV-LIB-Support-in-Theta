# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path

from pysvlib.svlib import parse_svlib, print_svlib
from pysvlib.svlib.static_analysis.cli import StaticAnalysisCLI
from pysvlib.svlib.static_analysis.data import StaticAnalysisError


class FormatterCli(StaticAnalysisCLI):
    def command_name(self) -> str:
        return "format"

    def command_help(self) -> str:
        return "Format SV-LIB files and report any issues found."

    def add_analysis_arguments(self, parser: StaticAnalysisCLI) -> None:
        # No additional arguments needed for the linter at the moment,
        # but this method can be used to add any linter-specific arguments in the future.
        pass

    def run_analysis(self, path: Path, args: argparse.Namespace) -> list[StaticAnalysisError]:
        commands = parse_svlib(path.read_text())
        text = print_svlib(commands)
        path.write_text(text)
