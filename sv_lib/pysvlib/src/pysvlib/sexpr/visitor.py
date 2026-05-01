# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pysvlib.sexpr.syntax import (
    Binary,
    Decimal,
    Hexadecimal,
    Keyword,
    Numeral,
    String,
    Symbol,
)


class Visitor:
    def sexpr(self, sexpr, *args, **kwargs):
        match sexpr:
            case Numeral(num):
                return self.numeral(num, *args, **kwargs)

            case Decimal(num):
                return self.decimal(num, *args, **kwargs)

            case Hexadecimal(num):
                return self.hexadecimal(num, *args, **kwargs)

            case Binary(num):
                return self.binary(num, *args, **kwargs)

            case String(text):
                return self.string(text, *args, **kwargs)

            case Keyword(name):
                return self.keyword(name, *args, **kwargs)

            case Symbol(name):
                return self.symbol(name, *args, **kwargs)

            case tuple() as sexpr:
                return self.list(sexpr, *args, **kwargs)
