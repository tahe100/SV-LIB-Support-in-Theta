# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

# necessary so that the Visit...Result classes can have each other as parameter
from __future__ import annotations

from dataclasses import dataclass

from pysvlib.svlib.syntax import Statement, Variable


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class TranslateToProcedureResult:
    """
    The result when translating to an SV-LIB Procedure.
    """

    name: str
    inputs: tuple[Variable, ...]
    outputs: tuple[Variable, ...]
    local_variables: tuple[Variable, ...]
    body: Statement
    translated_annotated: tuple[TranslateToAnnotatedResult, ...]

    def __post_init__(self):
        if len(self.name) == 0:
            raise ValueError("TranslateToProcedureResult cannot have an empty name.")

        if len(self.translated_annotated) == 0:
            raise ValueError("TranslateToProcedureResult must contain at least one TranslateToAnnotatedResult.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class TranslateToAnnotatedResult:
    """
    The result when translating to an SV-LIB Annotated.
    """

    annotated: Statement
    translated_statements: tuple[TranslateToStatementsResult, ...]

    @property
    def all_statements(self) -> tuple[Statement, ...]:
        return self.annotated, *(s for res in self.translated_statements for s in res.statements)

    def __post_init__(self):
        if len(self.translated_statements) == 0:
            raise ValueError("TranslateToAnnotatedResult must contain at least one TranslateToStatementsResult.")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class TranslateToStatementsResult:
    """
    The result when translating to SV-LIB Statements to store the name of the Procedure called within the statement(s).
    """

    statements: tuple[Statement, ...]
    called_proc_name: str | None = None

    def __post_init__(self):
        if len(self.statements) == 0:
            raise ValueError("TranslateToStatementsResult must contain at least one Statement.")
