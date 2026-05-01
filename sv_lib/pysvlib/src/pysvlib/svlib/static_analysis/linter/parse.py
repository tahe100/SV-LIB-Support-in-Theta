# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from pysvlib.svlib.factory import Factory
from pysvlib.svlib.parser import SvLibParsingFailedException, parse_svlib_without_linting
from pysvlib.svlib.static_analysis.linter.error import LinterException, ParserError
from pysvlib.svlib.static_analysis.linter.linter import Linter
from pysvlib.svlib.syntax import Command


def parse_svlib(text: str, factory: Optional[Factory] = None) -> list[Command] | list[list[Command]]:
    """
    Parse the given SV-LIB text, including the linting checks for annotations and return the corresponding AST.
    :param text: SV-LIB text to parse
    :param factory: Optional factory to use for creating AST nodes
    :return: AST representation of the SV-LIB file which is either a program (list[Command])
            or a witness (list[list[Command])
    """
    try:
        ast_without_linting = parse_svlib_without_linting(text, factory)
    except SvLibParsingFailedException as e:
        # Parser crashed completely
        raise LinterException((ParserError(f"Parsing failed due to which linting could not be performed: {e}"),)) from e

    linter = Linter()

    is_witness = isinstance(ast_without_linting, list) and all(
        isinstance(sublist, list) for sublist in ast_without_linting
    )
    if is_witness:
        # We can only lint witnesses together with the main program,
        # so in this case we currently skip linting.
        return ast_without_linting

    linter.lint(ast_without_linting)
    return ast_without_linting
