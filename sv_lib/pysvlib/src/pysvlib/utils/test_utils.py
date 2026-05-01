# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from pysvlib.svlib.static_analysis.linter.error import (
    DuplicateDeclaredSortError,
    DuplicateFunNameError,
    DuplicateVariableError,
    InvalidSortError,
    LogicNotFoundError,
    UndefinedFunctionError,
)


def examples_dir() -> Path:
    return Path(__file__).absolute().parent.parent.parent.parent.parent / "examples"


def examples_validation_dir() -> Path:
    return examples_dir() / "core-validation"


def dir_with_test_programs() -> Path:
    return Path(__file__).absolute().parent.parent.parent.parent / "test-programs"


def dir_with_test_programs_linter_fail() -> Path:
    return dir_with_test_programs() / "expect-linter-fail"


def expected_linter_errors_for_test_programs() -> dict[str, set[tuple[str, int]]]:
    return {
        "declare_var.svlib": {
            (DuplicateVariableError.__name__, 1),
            (InvalidSortError.__name__, 1),
        },
        "define_proc.svlib": {
            (InvalidSortError.__name__, 4),
        },
        "set_logic.smtlib": {
            (LogicNotFoundError.__name__, 1),
        },
        "define_fun.smtlib": {
            (DuplicateFunNameError.__name__, 1),
            (DuplicateVariableError.__name__, 1),
            (InvalidSortError.__name__, 1),
            (UndefinedFunctionError.__name__, 1),
        },
        "declare_fun.smtlib": {
            (InvalidSortError.__name__, 2),
        },
        "declare_sort.smtlib": {
            (DuplicateDeclaredSortError.__name__, 1),
        },
    }


def dir_with_programs_linter_sucess() -> Path:
    return dir_with_test_programs() / "expect-linter-sucess"
