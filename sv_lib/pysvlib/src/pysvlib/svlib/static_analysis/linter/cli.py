# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import itertools
from _sha2 import sha256
from pathlib import Path

from pysvlib.svlib import AnnotateTag, SelectTrace, parse_svlib_without_linting
from pysvlib.svlib.parser import SvLibParsingFailedException
from pysvlib.svlib.static_analysis.cli import StaticAnalysisCLI
from pysvlib.svlib.static_analysis.data import StaticAnalysisError
from pysvlib.svlib.static_analysis.linter.error import ParserError
from pysvlib.svlib.static_analysis.linter.linter import Linter


class LinterCLI(StaticAnalysisCLI):
    def command_name(self) -> str:
        return "lint"

    def command_help(self) -> str:
        return "Lint SV-LIB files and report any issues found."

    def add_analysis_arguments(self, parser: argparse._SubParsersAction) -> None:
        parser.add_argument(
            "--print-file-metadata",
            action="store_true",
            default=False,
            required=False,
            help=(
                "Print file metadata during linting such as what file is being linted, "
                "its hash, if it is a witness, etc."
            ),
        )

    def run_analysis(self, path: Path, args: argparse.Namespace) -> list[StaticAnalysisError]:
        try:
            ast_without_linting = parse_svlib_without_linting(path.read_text(), None)
        except SvLibParsingFailedException as e:
            # Parser crashed completely
            return [ParserError(f"Parsing failed due to which linting could not be performed: {e}")]

        linter = Linter()

        is_witness = isinstance(ast_without_linting, list) and all(
            isinstance(sublist, list) for sublist in ast_without_linting
        )

        if args.print_file_metadata:
            # In this case we are looking at a witness which has type list[list[Command]]
            file_type = "Witness" if is_witness else "Verification task"

            print("")
            print("-" * 60)
            print(f"Linting {file_type}: {path}")
            print(f"{file_type} File hash: {sha256(path.read_text().encode('utf-8')).hexdigest()}")
            print(f"{file_type} File bytes: {len(path.read_text().encode('utf-8'))}")
            print(f"{file_type} File lines of code: {len(path.read_text().splitlines())}")

            if is_witness:
                # If we can determine the type of the witness uniquely we
                # print it out
                if all(isinstance(command, AnnotateTag) for command in itertools.chain(*ast_without_linting)):
                    print("Witness type: correctness")
                elif all(isinstance(command, SelectTrace) for command in itertools.chain(*ast_without_linting)):
                    print("Witness type: violation")
                else:
                    print("Witness type: unknown")

        if is_witness:
            # We can only lint witnesses together with the main program,
            # so in this case we currently skip linting.
            return []

        errors = linter._lint_without_errors(ast_without_linting)
        return errors
