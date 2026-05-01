# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from pysvlib.sexpr.syntax import Symbol


def inline_let(sexpr, env):
    match sexpr:
        case Symbol(name):
            if name in env:
                return env[name]
            else:
                return sexpr

        case (Symbol("let"), pairs, body):
            env_ = env.copy()

            for entry in pairs:
                match entry:
                    case (Symbol(x), arg):
                        arg_ = inline_let(arg, env)
                        env_[x] = arg_

                    case _:
                        raise ValueError(f"not a let binding: {entry}")

            return inline_let(body, env_)

        case tuple() as sexpr:
            return tuple(inline_let(arg, env) for arg in sexpr)

        case _:
            return sexpr
