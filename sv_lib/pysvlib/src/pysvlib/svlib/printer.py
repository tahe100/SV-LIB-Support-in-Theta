# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

# Allow star imports only in this file, since we need to import all
# syntax elements for the visitor pattern.
# ruff: noqa: F405

from fractions import Fraction

from pysvlib.sexpr import print_sexprs
from pysvlib.sexpr.syntax import *  # noqa: F403
from pysvlib.svlib.syntax import *  # noqa: F403


def print_svlib(commands: list[Command]):
    sexpr = format_list(commands)
    text = print_sexprs(sexpr)
    return text


def format_list(data):
    return [format_syntax(arg) for arg in data]


def format_formals(variables):
    return [(Symbol(var.name), format_syntax(var.sort)) for var in variables]


def format_pairs(pairs):
    return [(Symbol(var.name), format_syntax(arg)) for var, arg in pairs]


def format_attributes(attributes):
    result = []
    for key, value in attributes:
        result.append(Keyword(key))
        if value is not None:
            result.append(format_syntax(value))
    return result


def format_syntax(data):
    match data:
        case Annotated(inner, attributes, _resolve):
            return (Symbol("!"), format_syntax(inner), *format_attributes(attributes))

        case Param(name):
            return Symbol(name)

        case Keyword(name):
            return Symbol(name)

        case BitVec(bits):
            return (Symbol("_"), Symbol("BitVec"), Numeral(str(bits)))

        case FloatingPoint(exponent, significand):
            return (Symbol("_"), Symbol("FloatingPoint"), Numeral(str(exponent)), Numeral(str(significand)))

        case Sort(name, []):
            return Symbol(name)

        case Sort(name, args):
            return (Symbol(name), *format_list(args))

        case Literal(True, _):
            return Binary("true")

        case Literal(False, _):
            return Binary("false")

        case Literal(int() as value, BitVec(width)):
            return (Symbol("_"), Symbol(f"bv{value}"), Numeral(str(width)))

        case Literal(Binary(value), BitVec(width)):
            return (Symbol("_"), Binary(f"#b{value}"), Numeral(str(width)))

        case Literal(Hexadecimal(value), BitVec(width)):
            return (Symbol("_"), Hexadecimal(f"#x{value}"), Numeral(str(width)))

        case Literal(int() as value, _):
            if value < 0:  # CVC does not accept negative literals
                return (Symbol("-"), Numeral(str(-value)))
            else:
                return Numeral(str(value))

        case Literal(Fraction() as value, _):
            return Decimal("(/ " + str(value.numerator) + " " + str(value.denominator) + ")")

        case Literal(str() as value, _):
            return String(value)

        case Variable(name, _sort):
            return Symbol(name)

        case At(term, label):
            return (Symbol("at"), format_syntax(term), Symbol(label))

        case Final(term):
            return (Symbol("final"), format_syntax(term))

        case Application(name, args):
            if len(args) == 0:
                return Symbol(name)

            return (Symbol(name), *format_list(args))

        case Binder(quantifier, bound, body):
            return (Symbol(quantifier), format_formals(bound), format_syntax(body))

        case Return():
            return (Symbol("return"),)

        case Break():
            return (Symbol("break"),)

        case Continue():
            return (Symbol("continue"),)

        case Assume(formula):
            return (Symbol("assume"), format_syntax(formula))

        case Assign(pairs):
            return (Symbol("assign"), *format_pairs(pairs))

        case Havoc(variables):
            return (Symbol("havoc"), *format_list(variables))

        case Label(name):
            return (Symbol("label"), Symbol(name))

        case Goto(name):
            return (Symbol("goto"), Symbol(name))

        case Call(name, inputs, outputs):
            return (
                Symbol("call"),
                Symbol(name),
                format_list(inputs),
                format_list(outputs),
            )

        case If(condition, if_true, Sequence([])):
            return (Symbol("if"), format_syntax(condition), format_syntax(if_true))

        case If(condition, if_true, if_false):
            return (
                Symbol("if"),
                format_syntax(condition),
                format_syntax(if_true),
                format_syntax(if_false),
            )

        case While(condition, body):
            return (Symbol("while"), format_syntax(condition), format_syntax(body))

        case Sequence(statements):
            return (Symbol("sequence"), *format_list(statements))

        case Choice(statements):
            return (Symbol("choice"), *format_list(statements))

        case SetLogic(logic):
            return (Symbol("set-logic"), Symbol(logic))

        case GetAssertions():
            return (Symbol("get-assertions"),)

        case GetInfo(keyword):
            return (Symbol("get-info"), Keyword(keyword))

        case SetInfo(keyword, argument):
            # no format_syntax(...) around the argument here, assuming it is not parsed in the first place
            return (Symbol("set-info"), Keyword(keyword), argument)

        case GetOption(keyword):
            return (Symbol("get-option"), Keyword(keyword))

        case SetOption(keyword, argument):
            # no format_syntax(...) around the argument here, assuming it is not parsed in the first place
            return (Symbol("set-option"), Keyword(keyword), argument)

        case Assert(formula):
            return (Symbol("assert"), format_syntax(formula))

        case DeclareSort(Sort(name, args)):
            return (Symbol("declare-sort"), Symbol(name), Numeral(str(len(args))))

        case DefineSort(Sort(name, args), body):
            return (
                Symbol("declare-sort"),
                Symbol(name),
                format_list(args),
                format_syntax(body),
            )

        case DeclareDatatypes(_sorts, _datatypes):
            raise NotImplementedError

        case DeclareVar(Variable(name, _, sort)):
            return (Symbol("declare-var"), Symbol(name), format_syntax(sort))

        # some CHC solvers don't like this
        # case DeclareFun(Function(name, [], result)):
        #     return (Symbol("declare-const"), Symbol(name), format_syntax(result))

        case DeclareFun(Function(name, arguments, result)):
            return (
                Symbol("declare-fun"),
                Symbol(name),
                format_list([arg.sort for arg in arguments]),
                format_syntax(result),
            )

        case DefineFun(Function(name, arguments, result), body):
            return (
                Symbol("define-fun"),
                Symbol(name),
                format_formals(arguments),
                format_syntax(result),
                format_syntax(body),
            )

        case DefineFunsRec(_funs, _bodies):
            raise NotImplementedError()

        case DefineProc(Procedure(name, inputs, outputs, locals), body):
            return (
                Symbol("define-proc"),
                Symbol(name),
                format_formals(inputs),
                format_formals(outputs),
                format_formals(locals),
                format_syntax(body),
            )

        case DefineProcsRec(procs, bodies):
            return (
                Symbol("define-procs-rec"),
                [
                    (
                        Symbol(proc.name),
                        format_formals(proc.inputs),
                        format_formals(proc.outputs),
                        format_formals(proc.locals),
                    )
                    for proc in procs
                ],
                [format_syntax(body) for body in bodies],
            )

        case AnnotateTag(tag, attributes):
            return (Symbol("annotate-tag"), Symbol(tag), *format_attributes(attributes))

        case SelectTrace(Trace(_model, _globals, _proc_name, _steps, _violation, _using)):
            return (
                Symbol("select-trace"),
                (Symbol("model"), *format_list(_model)),
                (Symbol("init-global-vars"), *format_pairs(_globals)),
                (Symbol("entry-proc"), Symbol(_proc_name)),
                (Symbol("steps"), *format_list(_steps)),
                format_syntax(_violation),
                *format_list(_using),
            )

        case VerifyCall(name, inputs):
            return (Symbol("verify-call"), Symbol(name), format_list(inputs))

        case GetWitness():
            return (Symbol("get-witness"),)

        case InitProcVars(proc_name, assignments):
            return (
                Symbol("init-proc-vars"),
                Symbol(proc_name),
                *format_pairs(assignments),
            )

        case Incorrect(tag, attributes):
            return (
                Symbol("incorrect-annotation"),
                Symbol(tag),
                *format_list(attributes),
            )

        case HavocStep(assignments):
            return (Symbol("havoc"), format_pairs(assignments))

        case Leap(tag, assignments):
            return (Symbol("leap"), Symbol(tag), format_pairs(assignments))

        case Symbol(name):
            return Symbol(name)

        case string if isinstance(string, str):
            # For keywords like `check-true`
            # TODO: Fix by making a class for attributes of this kind
            return Keyword(string)

        # Can appear on the right hand-side of key-value assignments,
        # so we handle it, even though it should never appear here
        # TODO: Refactor this
        case Numeral(_) as numeral:
            return numeral

        case _:
            raise ValueError(f"unknown syntax {data}")
