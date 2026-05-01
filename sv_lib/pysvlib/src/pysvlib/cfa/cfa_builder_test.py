# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from pysvlib.cfa import build_cfa
from pysvlib.utils.test_utils import examples_dir


@pytest.mark.parametrize("path", examples_dir().rglob("*.svlib"))
def test_parse_svlib(path: Path):
    if path.name.endswith(".witness.svlib"):
        return

    build_cfa(path.read_text())
