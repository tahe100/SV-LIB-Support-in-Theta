# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0


from typing import Optional

from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.backend.validator.correctness_validation import validate_correctness
from pysvlib.svlib.solver import Solver
from pysvlib.svlib.syntax import Command, SelectTrace


def validate(commands: list[Command], solver: Optional[Solver] = None) -> tuple[BackendResult, str]:
    contains_select_trace = any(isinstance(cmd, SelectTrace) for cmd in commands)
    if contains_select_trace:
        return BackendResult.Error, "violation witness validation is not supported yet"
    else:
        return validate_correctness(commands, solver)
