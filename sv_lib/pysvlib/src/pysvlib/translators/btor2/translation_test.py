# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from pysvlib.svlib import parse_svlib, print_svlib
from pysvlib.translators import btor2_to_svlib


def btor2_examples_dir() -> Path:
    return Path(__file__).absolute().parent / "test-examples-dir" / "test-examples"


def btor2_large_examples_dir() -> Path:
    return Path(__file__).absolute().parent / "test-examples-dir" / "large-test-examples"


def get_large_btor2_examples() -> list[Path]:
    return list(btor2_large_examples_dir().rglob("*.btor2"))


def get_btor2_examples() -> list[Path]:
    return list(btor2_examples_dir().rglob("*.btor2"))


@pytest.mark.parametrize("path", get_btor2_examples(), ids=[p.stem for p in get_btor2_examples()])
def test_transform_btor2_to_svlib(path: Path):
    commands = btor2_to_svlib(path.read_text())
    text = print_svlib(list(commands))
    parse_svlib(text)


@pytest.mark.parametrize("path", get_large_btor2_examples(), ids=[p.stem for p in get_large_btor2_examples()])
def test_transform_large_btor2_to_svlib(path: Path):
    commands = btor2_to_svlib(path.read_text())
    text = print_svlib(list(commands))
    parse_svlib(text)
