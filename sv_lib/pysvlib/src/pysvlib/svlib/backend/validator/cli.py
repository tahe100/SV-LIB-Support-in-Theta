# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path
from typing import Optional

from pysvlib.svlib import validate
from pysvlib.svlib.backend.cli import BackendCLI
from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.solver import Solver, Solvers
from pysvlib.svlib.syntax import Command


class ValidatorCLI(BackendCLI):
    def command_name(self) -> str:
        return "validate"

    def command_help(self) -> str:
        return "Validate a verification result against a witness"

    def add_backend_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--solver",
            required=False,
            type=str,
            choices=[solver.value for solver in Solvers],
            help="The SMT solver to use for validation (if applicable)",
        )

    def run_backend(
        self, commands: list[Command], output_dir: Path | None, other_args: argparse.Namespace
    ) -> tuple[BackendResult, Optional[str]]:
        solver = Solver(Solvers.from_string(other_args.solver))
        return validate(commands, solver)
