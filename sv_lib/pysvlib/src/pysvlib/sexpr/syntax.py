# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from abc import ABC
from dataclasses import dataclass


class Token(ABC):  # noqa: B024
    def __init__(self):
        # TODO: add file and line number information here
        raise NotImplementedError("Abstract base class")


class Literal(Token, ABC):
    pass


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Numeral(Literal):
    value: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Hexadecimal(Literal):
    value: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Decimal(Literal):
    value: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Binary(Literal):
    value: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class String(Literal):
    value: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Symbol(Token):
    name: str


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Keyword(Token):
    name: str


type SExpr = tuple[Symbol | Keyword | Literal, ...]
