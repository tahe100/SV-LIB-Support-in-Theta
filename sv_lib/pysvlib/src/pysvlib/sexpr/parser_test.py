# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from pysvlib.sexpr import parse_sexprs, print_sexprs
from pysvlib.utils.test_utils import examples_dir


@pytest.mark.parametrize("path", examples_dir().rglob("*.svlib"))
def test_parse_sexprs(path: Path):
    parse_sexprs(path.read_text())


@pytest.mark.parametrize("path", examples_dir().rglob("*.svlib"))
def test_parse_print_sexprs(path: Path):
    text = path.read_text()
    sexprs = parse_sexprs(text)
    text_ = print_sexprs(sexprs)
    sexprs_ = parse_sexprs(text_)

    assert len(sexprs) == len(sexprs_)
    for sexpr, sexpr_ in zip(sexprs, sexprs_, strict=True):
        assert sexpr == sexpr_
