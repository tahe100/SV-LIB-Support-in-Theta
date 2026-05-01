# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.linker import link_witness
from pysvlib.svlib.static_analysis.linter.parse import parse_svlib
from pysvlib.svlib.syntax import Command
from pysvlib.utils.cli import PySvLibCLI


class BackendCLI(PySvLibCLI, ABC):
    """
    Abstract base class for backend-specific CLI implementations.
    These include:
    - Verifiers
    - Validators
    - Test-case generators
    """

    @abstractmethod
    def command_name(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the name of the command")

    @abstractmethod
    def command_help(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the help message for the command")

    @abstractmethod
    def add_backend_arguments(self, parser: argparse.ArgumentParser) -> None:
        raise NotImplementedError(
            "Subclasses should implement this method to add their specific verification arguments to the parser"
        )

    def add_subparser(self, current_parser: argparse._SubParsersAction) -> None:
        subparser = current_parser.add_parser(
            self.command_name(),
            help=self.command_help(),
        )
        # Add the common CLI for verification taks, which means arbitrary many files and
        # an optional witness, which is the most general case. Subclasses can then add additional arguments as needed.
        subparser.add_argument(
            "programs",
            nargs="+",
            type=lambda x: None if x is None else Path(x),
            help="Files containing the verification task(s) to verify",
        )
        subparser.add_argument(
            "--witness",
            required=False,
            type=lambda x: None if x is None else Path(x),
            help="File containing the witness information (if applicable)",
        )
        subparser.add_argument(
            "--output-dir",
            required=False,
            default=Path("output"),
            type=lambda x: None if x is None else Path(x),
            help="Directory to store intermediate information (if applicable)",
        )

        self.add_backend_arguments(subparser)

    def report_backend_result(self, verification_verdict: BackendResult, reason: Optional[str]) -> None:
        match verification_verdict:
            case BackendResult.Correct:
                print("correct")
            case BackendResult.Incorrect:
                print("incorrect")
            case BackendResult.Unknown:
                unknown_string = "unknown" + (f"({reason})" if reason is not None else "")
                print(unknown_string)
            case BackendResult.Error:
                error_string = "error" + (f"({reason})" if reason is not None else "")
                print(error_string)
            case BackendResult.Timeout:
                timeout_string = "timeout" + (f"({reason})" if reason is not None else "")
                print(timeout_string)
            case _:
                raise ValueError(f"Unknown verification verdict: {verification_verdict}")

    def run(self, args: argparse.Namespace) -> Any:
        # First create the verification task from the given arguments
        witness = args.witness
        program_text = os.linesep.join([program.read_text() for program in args.programs])

        witness_commands = None
        try:
            if witness is not None:
                witness_commands = parse_svlib(
                    witness.read_text(),
                )
        except Exception as e:
            print(f"Error parsing witness file: {e}")
            return None

        try:
            program_commands = parse_svlib(program_text)
        except Exception as e:
            print(f"Error parsing program files: {e}")
            return None

        commands = program_commands if witness_commands is None else link_witness(program_commands, witness_commands)

        output_path = args.output_dir
        output_path.mkdir(parents=True, exist_ok=True) if output_path is not None else None
        try:
            verification_verdict, reason = self.run_backend(commands, output_path, args)
        except Exception as e:
            print(f"Error during backend execution: {e}")
            raise e

        self.report_backend_result(verification_verdict, reason)
        return None

    @abstractmethod
    def run_backend(
        self, commands: list[Command], output_dir: Path | None, other_args: argparse.Namespace
    ) -> tuple[BackendResult, Optional[str]]:
        """
        calls the backend-specific verification procedure with the given commands and other arguments,
        and returns the verification result and an optional message (e.g., error message in case of failure)

        :param commands: the commands to verify, which are obtained from the
            program files and optionally linked with the witness
        :param other_args: other arguments that are needed for the verification,
            which are obtained from the command-line arguments

        :return: a tuple containing the verification result and an
            optional message (e.g., error message in case of failure)
        """
        raise NotImplementedError(
            "Subclasses should implement this method to run verification with the given arguments"
        )
