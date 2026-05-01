# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import itertools
from collections import Counter
from pathlib import Path

import pytest

from pysvlib.pysvlib_cli import pysvlib
from pysvlib.svlib.parser import parse_svlib_without_linting
from pysvlib.svlib.static_analysis.linter.error import LinterError
from pysvlib.svlib.static_analysis.linter.linter import Linter
from pysvlib.utils.test_utils import (
    dir_with_test_programs_linter_fail,
    examples_dir,
    examples_validation_dir,
    expected_linter_errors_for_test_programs,
)


@pytest.mark.parametrize("path", examples_dir().rglob("*.svlib"))
def test_lint_files(path: Path):
    return_code = pysvlib(["--debug", "lint", str(path)])
    if return_code != 0:
        print(f"Linting failed for file: {path}")
    assert return_code == 0


def test_lint_dir():
    return_code = pysvlib(["--debug", "lint", str(examples_dir())])
    assert return_code == 0


@pytest.mark.parametrize(
    "path",
    itertools.chain(
        dir_with_test_programs_linter_fail().rglob("*.svlib"),
        dir_with_test_programs_linter_fail().rglob("*.smtlib"),
    ),
)
def test_lint_expect_fail_programs(path: Path) -> None:
    if path.name != "define_fun.smtlib":
        return

    linter = Linter()
    ast = parse_svlib_without_linting(path.read_text())
    errors: list[LinterError] = linter._lint_without_errors(ast)
    error_class_with_amount = set(Counter(e.__class__.__name__ for e in errors).items())

    expected_errors = expected_linter_errors_for_test_programs()[path.name]
    assert error_class_with_amount == expected_errors


@pytest.mark.parametrize("path", examples_validation_dir().rglob("*.svlib"))
def test_validate_files(path: Path):
    try:
        return_code = pysvlib(["--debug", "validate", str(path), "--solver", "z3"])
        assert return_code == 0

        return_code = pysvlib(["--debug", "validate", str(path), "--solver", "cvc5"])
        assert return_code == 0
    except NotImplementedError as e:
        pytest.skip(f"Skipping test for {path} due to NotImplementedError: {e}")


@pytest.mark.parametrize("path", examples_dir().rglob("*.svlib"))
def test_validate_files_with_witnesses(path: Path):
    witness_path = path.with_suffix(".witness.svlib")
    if not witness_path.exists():
        pytest.skip(f"No witness file found for {path}")
    else:
        print(f"Using witness file: {witness_path}")

    return_code = pysvlib(
        [
            "--debug",
            "validate",
            str(path),
            "--witness",
            str(witness_path),
            "--solver",
            "z3",
        ]
    )
    assert return_code == 0

    return_code = pysvlib(
        [
            "--debug",
            "validate",
            str(path),
            "--witness",
            str(witness_path),
            "--solver",
            "cvc5",
        ]
    )
    assert return_code == 0
