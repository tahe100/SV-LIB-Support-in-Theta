# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path
from typing import Optional

from pysvlib.sexpr import print_sexprs
from pysvlib.svlib import verify_chc
from pysvlib.svlib.backend.cli import BackendCLI
from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.solver import Solver, Solvers
from pysvlib.svlib.syntax import Command


class ChcCli(BackendCLI):
    def command_name(self) -> str:
        return "chc"

    def command_help(self) -> str:
        return "Verify a verification task with an optional witness using Constrained Horn Clauses (CHC)"

    def add_backend_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--solver",
            required=False,
            type=str,
            choices=[solver.value for solver in Solvers],
            help="The SMT solver to use for validation (if applicable)",
        )

        parser.add_argument(
            "--timeout",
            required=False,
            type=int,
            help="The timeout in miliseconds for the solver (if applicable)",
        )

        parser.add_argument(
            "--witness-file",
            required=False,
            type=str,
            default="witness.svlib",
            help="The file name to write the witness to (if applicable)",
        )

    def run_backend(
        self, commands: list[Command], output_dir: Path | None, other_args: argparse.Namespace
    ) -> tuple[BackendResult, Optional[str]]:
        solver = (
            Solver(Solvers.from_string(other_args.solver), other_args.timeout)
            if other_args.solver is not None
            else None
        )
        result, reason, witness = verify_chc(commands, solver)
        if witness is not None:
            witness_path = other_args.output_dir / "witness.svlib"
            witness_path.write_text(print_sexprs((witness,)))

        return result, reason
