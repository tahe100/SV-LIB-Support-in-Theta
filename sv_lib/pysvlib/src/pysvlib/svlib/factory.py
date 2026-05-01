# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

# Allow star imports in this file, since we need to import all
# syntax elements for the visitor pattern.
# ruff: noqa: F405

from fractions import Fraction

from pysvlib.sexpr import Symbol
from pysvlib.svlib.syntax import *  # noqa: F403


class Factory:
    # scoping
    def _make_scope(self, variables, proc_name):
        scope_ = {name: Variable(name, proc_name, type_) for name, type_ in variables}
        vars_ = [Variable(name, proc_name, type_) for name, type_ in variables]
        return scope_, vars_

    def empty_scope(self):
        return dict()

    def init_formals(self, variables, proc_name=None):
        scope_, vars_ = self._make_scope(variables, proc_name)
        return scope_, vars_

    def with_formals(self, scope, variables, proc_name=None):
        scope_, vars_ = self._make_scope(variables, proc_name)
        return (scope | scope_), vars_

    def with_assignables(self, scope, variables, proc_name=None):
        scope_, vars_ = self._make_scope(variables, proc_name)
        return (scope | scope_), vars_

    # SMT-LIB sort constructors
    def bool(self):
        return self.sort("Bool", tuple([]))

    def int(self):
        return self.sort("Int", tuple([]))

    def real(self):
        return self.sort("Real", tuple([]))

    def str(self):
        return self.sort("String", tuple([]))

    def array(self, dom, ran):
        return self.sort("Array", tuple([dom, ran]))

    def bitvec(self, bits):
        return BitVec(bits)

    def floating_point(self, exponent, significand):
        """
        Creates and returns a new FloatingPoint. The significand includes the hidden bit.
        """
        return FloatingPoint(exponent, significand)

    def sort(self, name, args):
        return Sort(name, tuple(args))

    def _make_annotated(self, term_or_statement, attributes_, scope, resolve_):
        match term_or_statement:
            case Annotated(inner, attributes, _resolve):
                # note, both resolve functions should be the same, but probably not the same object
                return Annotated(inner, tuple(attributes) + tuple(attributes_), scope, resolve_)

            case _:
                return Annotated(term_or_statement, tuple(attributes_), scope, resolve_)

    # annotation constructors
    def annotate_term(self, term, attributes, scope, resolve):
        return self._make_annotated(term, attributes, scope, resolve)

    def annotate_statement(self, statement, attributes, scope, resolve):
        return self._make_annotated(statement, attributes, scope, resolve)

    # SMT-LIB term constructors
    def numeral(self, value):
        return Literal(int(value, 10), self.int())

    def decimal(self, value):
        return Literal(Fraction(value), self.real())

    def hexadecimal(self, value):
        return Literal(int(value, 16), self.int())

    def boolean(self, value: bool):
        return Literal(value, self.bool())

    def bitvector_literal(self, value, width):
        return Literal(value, self.bitvec(width))

    def at(self, term, label):
        return At(term, label)

    def final(self, term):
        return Final(term)

    def const(self, name):
        return self.apply(name, [])

    def apply(self, name, args):
        return Application(name, tuple(args))

    def paramaterized_apply(self, name: str, args: list, terms: list):
        args_string = ""
        for arg in args:
            args_string += f" {arg.value}" if not isinstance(arg, Symbol) else f"{arg.name}"
        identifier = f"(_ {name} {args_string})"

        return Application(identifier, terms)

    def forall(self, bound, body):
        return Binder("forall", bound, body)

    def exists(self, bound, body):
        return Binder("exists", bound, body)

    # SV-LIB statement constructors
    def skip(self):
        return self.sequence(tuple([]))

    def returns(self):
        return Return()

    def breaks(self):
        return Break()

    def continues(self):
        return Continue()

    def assume(self, condition):
        return Assume(condition)

    def assign(self, pairs):
        return Assign(tuple(pairs))

    def havoc(self, vars):
        return Havoc(vars)

    def label(self, name):
        return Label(name)

    def goto(self, name):
        return Goto(name)

    def call(self, name, inputs, outputs):
        return Call(name, tuple(inputs), tuple(outputs))

    def ifs(self, condition, iftrue, iffalse):
        return If(condition, iftrue, iffalse)

    def whiles(self, condition, body):
        return While(condition, body)

    def sequence(self, statements):
        return Sequence(tuple(statements))

    def choice(self, statements):
        return Choice(tuple(statements))

    # SV-LIB trace elements
    def havoc_step(self, updates):
        return HavocStep(tuple(updates))

    def choice_step(self, index):
        return ChoiceStep(index)

    def leap(self, tag, updates):
        return Leap(tag, tuple(updates))

    def init_proc_vars(self, proc_name, updates):
        return InitProcVars(proc_name, tuple(updates))

    def invalid_step(self, step):
        return Invalid(step)

    def incorrect_annotation(self, tag, attributes):
        return Incorrect(tag, tuple(attributes))

    # SMT-LIB command constructors
    def set_logic(self, logic):
        return SetLogic(logic)

    def get_option(self, keyword):
        return GetOption(keyword)

    def set_option(self, keyword, argument=None):
        return SetOption(keyword, argument)

    def get_info(self, keyword):
        return GetInfo(keyword)

    def set_info(self, keyword, argument=None):
        return SetInfo(keyword, argument)

    def declare_sort(self, name, arity):
        params = [Param(f"a{index}") for index in range(arity)]
        sort = Sort(name, tuple(params))
        return DeclareSort(sort)

    def define_sort(self, name, args, typ):
        sort = Sort(name, tuple(args))
        return DefineSort(sort, typ)

    def declare_datatypes(self, decls, datatypes):
        raise NotImplementedError()

    def declare_const(self, name, res):
        return self.declare_fun(name, tuple([]), res)

    def declare_fun(self, name, args, res):
        fun = Function(name, tuple(args), res)
        return DeclareFun(fun)

    def define_fun(self, name, args, res, body):
        fun = Function(name, args, res)
        return DefineFun(fun, body)

    def asserts(self, constraint):
        return Assert(constraint)

    # SV-LIB command constructors
    def declare_var(self, name, sort):
        var = Variable(name, None, sort)
        return DeclareVar(var)

    def define_proc(self, name, inputs, outputs, locals, body):
        proc = Procedure(name, inputs, outputs, locals)
        return DefineProc(proc, body)

    def define_procs_rec(self, procs, bodies):
        return DefineProcsRec(procs, bodies)

    def select_trace(self, model, globals, proc_name, steps, violation, using):
        trace = Trace(model, globals, proc_name, steps, violation, using)
        return SelectTrace(trace)

    def tag_annotation(self, tag, attributes):
        return AnnotateTag(tag, tuple(attributes))

    def verify_call(self, name, inputs):
        return VerifyCall(name, tuple(inputs))

    def get_witness(self):
        return GetWitness()
