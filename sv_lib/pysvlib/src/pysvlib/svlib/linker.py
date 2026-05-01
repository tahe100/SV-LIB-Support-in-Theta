# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pysvlib.sexpr.syntax import Symbol
from pysvlib.svlib.printer import print_svlib
from pysvlib.svlib.static_analysis.linter.parse import parse_svlib
from pysvlib.svlib.syntax import Command, VerifyCall


def link_witness_to_script(script: str, witness: str) -> str:
    commands = parse_svlib(script)
    extra = parse_svlib(witness)
    commands_ = link_witness(commands, extra)

    text = print_svlib(commands_)
    return text


def link_witness(script: list[Command], witness: list[list[Command]]) -> list[Command]:
    result = []

    for command in script:
        match command:
            case VerifyCall(_, _):
                entries, witness = _shift_witness(witness)
                result.extend(entries)
                result.append(command)

            case _:
                result.append(command)

    return result


def _shift_witness(witness: list[list[Command]]):
    match witness:
        case ((Symbol("correct") | Symbol("incorrect")), entries, *rest):
            return entries, rest

        case entries, *rest:
            return entries, rest

        case _:
            raise ValueError(f"invalid witness: {witness}")
