# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field

from pysvlib.svlib.syntax import Application, Term, Variable


@dataclass(eq=True, frozen=True, slots=True, repr=True, unsafe_hash=True)
class HornClause:
    p_from: str
    p_to: str
    condition: Application
    new_args: tuple[Term] | None = None
    is_return: bool = False
    from_kind: str = "cfg"  # cfg | pre
    call_pre_args: tuple[Term] | None = None  # saves vars used in a call as input - relevant for procedures_to_chc


# TODO: Make immutable by using `frozendict` and tuples
@dataclass(eq=True, frozen=False, repr=True, unsafe_hash=False)
class ProcedureContext:
    name: str
    points: tuple[str] = field(default_factory=list)
    clauses: tuple[HornClause] = field(default_factory=list)
    pp_counter: int = field(default_factory=int)

    vars: dict[str, Variable] = field(default_factory=dict)
    inputs: dict[str, Variable] = field(default_factory=dict)
    outputs: dict[str, Variable] = field(default_factory=dict)
    body: Term = field(default_factory=dict)

    entry: str = None
    exit: str = None

    fresh_vars_for_clause: dict[tuple, tuple[Variable]] = field(default_factory=dict)
