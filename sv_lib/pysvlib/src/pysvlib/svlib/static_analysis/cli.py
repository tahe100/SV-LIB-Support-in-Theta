# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import itertools
from abc import ABC, abstractmethod
from pathlib import Path

from pysvlib.svlib.static_analysis.data import StaticAnalysisError, StaticAnalysisResult
from pysvlib.utils.cli import PySvLibCLI
from pysvlib.utils.logging import get_logger


def collect_targets(targets: list[Path]):
    paths = []
    for path in targets:
        if not path.exists():
            get_logger().error(f"target does not exist: {path}")
            continue

        # collect files: single file or all .svlib files recursively from a directory
        paths += [path for path in itertools.chain(path.rglob("*.svlib"), [path]) if path.is_file()]
    return paths


class StaticAnalysisCLI(PySvLibCLI, ABC):
    """
    Abstract base class for static analysis backend-specific CLI implementations.
    For example:
    - Linters
    - Formatters
    """

    @abstractmethod
    def command_name(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the name of the command")

    @abstractmethod
    def command_help(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the help message for the command")

    @abstractmethod
    def add_analysis_arguments(self, parser: argparse.ArgumentParser) -> None:
        raise NotImplementedError(
            "Subclasses should implement this method to add their specific verification arguments to the parser"
        )

    def add_subparser(self, current_parser: argparse._SubParsersAction) -> None:
        subparser = current_parser.add_parser(
            self.command_name(),
            help=self.command_help(),
        )
        # Add the common CLI for static analysis tasks, which means arbitrary
        # many files. Subclasses can then add additional arguments as needed.
        subparser.add_argument(
            "paths",
            nargs="+",
            type=lambda x: None if x is None else Path(x),
            help="Files or directories containing the SV-LIB code to analyze",
        )
        self.add_analysis_arguments(subparser)

    @abstractmethod
    def run_analysis(self, path: Path, args: argparse.Namespace) -> list[StaticAnalysisError]:
        raise NotImplementedError(
            "Subclasses should implement this method to run the static analysis on "
            "the given paths with the provided arguments"
        )

    def run(self, args: argparse.Namespace) -> None:
        paths = collect_targets(args.paths)
        if not paths:
            get_logger().error("No valid targets found to analyze.")
            return

        errors = []
        for path in paths:
            get_logger().debug(f"Analyzing {path}...")
            errors += self.run_analysis(path, args)

        for i, error in enumerate(errors):
            if i > 0:
                print()
            print(error.report())

        print(StaticAnalysisResult.Done.value)
        return None
