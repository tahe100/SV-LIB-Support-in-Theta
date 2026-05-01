# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from enum import Enum

from pysvlib.sexpr import parse_sexprs, print_sexprs


class Solvers(Enum):
    Z3 = "z3"
    CVC5 = "cvc5"
    Golem = "golem"
    Eldarica = "eldarica"

    @staticmethod
    def from_string(solver_name: str) -> "Solvers":
        for solver in Solvers:
            if solver.value == solver_name:
                return solver
        raise ValueError(f"Unknown solver: {solver_name}")


class Solver:
    def __init__(self, solver_name: Solvers, timeout_ms: int | None = None):
        match solver_name:
            case Solvers.Z3:
                self.cmdline = ["z3", "-in", "pp.min-alias-size=1000000"]
                self.require_get_model = True
                self.require_tempfile = False
                if timeout_ms:
                    self.cmdline.append(f"-t:{timeout_ms}")

            case Solvers.CVC5:
                self.cmdline = ["cvc5"]
                self.require_tempfile = False
                if timeout_ms:
                    self.cmdline.append(f"-tlimit-per={timeout_ms}")

            case Solvers.Golem:
                self.cmdline = ["golem", "--print-witness", "--logic", "QF_LIA"]
                self.require_get_model = False
                self.require_tempfile = True
                if timeout_ms:
                    raise ValueError(f"unsupported timeout for solver: {solver_name}")

            case Solvers.Eldarica:
                self.cmdline = ["eld", "-ssol"]
                self.require_get_model = False
                self.require_tempfile = True
                if timeout_ms:
                    if timeout_ms < 1000:
                        raise ValueError(f"unsupported timeout for solver: {solver_name}, requires at least one second")
                    self.cmdline.append(f"-t:{timeout_ms // 1000}")

            case _:
                raise ValueError(f"unsupported solver: {solver_name}")

    def run_solver(self, script, get_model=False):
        input = print_sexprs(script)

        if get_model and self.require_get_model:
            input = input + "(get-model)\n"

        if self.require_tempfile:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="wt", suffix=".smt2") as file:
                file.write(input)
                file.flush()
                status = subprocess.run(self.cmdline + [file.name], capture_output=True, text=True)
                output = status.stdout
        else:
            status = subprocess.run(self.cmdline, capture_output=True, input=input, text=True)
            output = status.stdout

        result = parse_sexprs(output)
        return result
