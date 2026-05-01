#!/usr/bin/env python3

# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path

file_path = Path(__file__).absolute().parent

all_wheels = list(file_path.glob("*.whl"))

for wheel in all_wheels:
    sys.path.append(str(wheel))

# ruff: noqa: E402

from pysvlib.pysvlib_cli import pysvlib_main

if __name__ == "__main__":
    pysvlib_main()
