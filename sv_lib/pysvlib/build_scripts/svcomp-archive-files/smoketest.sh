#!/bin/bash
# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PYSVLIB_DIR=$SCRIPT_DIR/pysvlib

echo $SCRIPT_DIR

echo "Running smoketest for PySvLib"

echo "Version currently running $($PYSVLIB_DIR/pysvlib_cli.py --version)"

echo "Running validation examples with Z3 solver"
# ./pysvlib_cli.py validate --solver z3 examples/core-validation/loop-add-incorrect-ensures.svlib
$PYSVLIB_DIR/pysvlib_cli.py validate --solver z3 $SCRIPT_DIR/examples/core-validation/loop-add.svlib
$PYSVLIB_DIR/pysvlib_cli.py validate --solver z3 $SCRIPT_DIR/examples/core-validation/call-mul-add.svlib

echo "Linting examples"
$PYSVLIB_DIR/pysvlib_cli.py lint $SCRIPT_DIR/examples
echo "All examples linted successfully"

echo "Verifying and validating example with CHC translation and Z3 solver"
$PYSVLIB_DIR/pysvlib_cli.py chc      --solver z3 --witness-file witness.svlib $SCRIPT_DIR/examples/core-verification/loop-add-main.svlib
$PYSVLIB_DIR/pysvlib_cli.py validate --solver z3 --witness      output/witness.svlib $SCRIPT_DIR/examples/core-verification/loop-add-main.svlib

echo "Smoketest completed successfully"
