# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import re

from pysvlib.sexpr.parser import t_SYMBOL
from pysvlib.sexpr.syntax import (
    Binary,
    Decimal,
    Hexadecimal,
    Keyword,
    Numeral,
    SExpr,
    String,
    Symbol,
)

PLAIN_SYMBOL = re.compile(t_SYMBOL)


def needs_quotes(sym):
    return (
        PLAIN_SYMBOL.fullmatch(sym) is None
        # needed for Identifier Application names like (_ extract 1 1)
        and not (sym.startswith("(") and sym.endswith(")"))
    )


def print_sexprs(exprs: list[SExpr]) -> str:
    import os

    lines = [line for expr in exprs for line in format_sexpr(expr)]
    return os.linesep.join(lines)


def _flatten(operator, neutral, arg):
    match arg:
        case [Symbol(fun), *args] if fun == operator:
            return _flatten_list(operator, neutral, args)
        case Symbol("true"):
            return []
        case _:
            return [arg]


def _flatten_list(operator, neutral, args):
    return [res for arg in args for res in _flatten(operator, neutral, arg)]


def format_sexprs(exprs):
    return format_application([line for expr in exprs for line in format_sexpr(expr)])


def format_sexpr(expr):
    match expr:
        case Numeral(num) | Decimal(num) | Hexadecimal(num) | Binary(num):
            return [num]

        case String(text):
            return ['"' + text + '"']

        case Keyword(name):
            return [":" + name]

        case Symbol(name):
            if needs_quotes(name):
                return ["|" + name + "|"]
            else:
                return [name]

        case [Symbol("and"), *args]:
            exprs = _flatten_list("and", "true", args)
            return format_sexprs([Symbol("and")] + exprs)

        case [Symbol("or"), *args]:
            exprs = _flatten_list("or", "false", args)
            return format_sexprs([Symbol("or")] + exprs)

        case tuple() | list() as exprs:
            return format_sexprs(exprs)

        case _:
            raise ValueError(f"not an s-expr: {expr}")


def format_application(args):
    if not args:
        return ["()"]

    m = max(len(arg) for arg in args)
    s = sum(len(arg) for arg in args)

    b = len(args) >= 2 and (m >= 40 or s >= 80)

    if b:
        x = "(" + args[0]
        ys = ["  " + arg for arg in args[1:-1]]
        z = "  " + args[-1] + ")"
        return [x, *ys, z]
    else:
        x = " ".join(args)
        return ["(" + x + ")"]
