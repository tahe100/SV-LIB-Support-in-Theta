# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction

from pysvlib.svlib.syntax import *  # noqa: F403

# Allow star imports only in this file, since we need to import all
# syntax elements for the visitor pattern.
# ruff: noqa: F405


class Visitor:
    def __init__(self):
        self.annotations = {}

    def unknown(self, category, object):
        raise NotImplementedError(f"visit {category}: {object} (please report)")

    def expand_tags(self, attributes):
        tags = tuple(tag.name for k, tag in attributes if k == "tag")
        attributes_ = tuple(entry for tag in tags for entry in (self.annotations.get(tag, [])))

        return tags, attributes_

    def resolve_attributes_as_terms(self, keyword, attributes, scope, resolve):
        result = []
        for k, sexpr in attributes:
            if k == keyword:
                if isinstance(sexpr, Term):
                    result.append(sexpr)
                else:
                    result.append(resolve(scope, sexpr))
        return result

    def param(self, name, *args, **kwargs):
        raise NotImplementedError(f"The function param is not yet implemented for class {self.__class__.__name__}")

    def sort(self, name, arguments, *args, **kwargs):
        raise NotImplementedError(f"The function sort is not yet implemented for class {self.__class__.__name__}")

    def bitvec(self, bits, *args, **kwargs):
        raise NotImplementedError(f"The function bitvec is not yet implemented for class {self.__class__.__name__}")

    def floating_point(self, exponent, significand, *args, **kwargs):
        raise NotImplementedError(
            f"The function floating_point is not yet implemented for class {self.__class__.__name__}"
        )

    def type(self, type_, *args, **kwargs):
        match type_:
            case Param(name):
                return self.param(name, *args, **kwargs)

            case BitVec(bits):
                return self.bitvec(bits, *args, **kwargs)

            case FloatingPoint(exponent, significand):
                return self.floating_point(exponent, significand, *args, **kwargs)

            case Sort(name, arguments):
                return self.sort(name, arguments, *args, **kwargs)

            case _:
                return self.unknown("type", type_)

    def literal(self, literal, sort, *args, **kwargs):
        raise NotImplementedError(f"The function literal is not yet implemented for class {self.__class__.__name__}")

    def variable(self, name, proc, sort, *args, **kwargs):
        raise NotImplementedError(f"The function variable is not yet implemented for class {self.__class__.__name__}")

    def application(self, function, arguments, *args, **kwargs):
        raise NotImplementedError(
            f"The function application is not yet implemented for class {self.__class__.__name__}"
        )

    def binder(self, quantifier, bound, body, *args, **kwargs):
        raise NotImplementedError(f"The function binder is not yet implemented for class {self.__class__.__name__}")

    def at(self, term, label, *args, **kwargs):
        raise NotImplementedError(f"The function at is not yet implemented for class {self.__class__.__name__}")

    def final(self, term, *args, **kwargs):
        raise NotImplementedError(f"The function final is not yet implemented for class {self.__class__.__name__}")

    def term(self, term, *args, **kwargs):
        match term:
            case Literal(value, sort):
                return self.literal(value, sort, *args, **kwargs)

            case Variable(name, proc, sort):
                return self.variable(name, proc, sort, *args, **kwargs)

            case Application(function, arguments):
                return self.application(function, arguments, *args, **kwargs)

            case Binder(quantifier, bound, body):
                return self.binder(quantifier, bound, body, *args, **kwargs)

            case At(term, label):
                return self.at(term, label, *args, **kwargs)

            case Final(term):
                return self.final(term, *args, **kwargs)

            case _:
                self.unknown("term", term)

    def annotated_statement(
        self,
        inner,
        tags,
        inline_attributes,
        linked_attributes,
        scope,
        resolve,
        *args,
        **kwargs,
    ):
        raise NotImplementedError(
            f"The function annotated_statement is not yet implemented for class {self.__class__.__name__}"
        )

    def returns(self, *args, **kwargs):
        raise NotImplementedError(f"The function returns is not yet implemented for class {self.__class__.__name__}")

    def breaks(self, *args, **kwargs):
        raise NotImplementedError(f"The function breaks is not yet implemented for class {self.__class__.__name__}")

    def continues(self, *args, **kwargs):
        raise NotImplementedError(f"The function continues is not yet implemented for class {self.__class__.__name__}")

    def assume(self, formula, *args, **kwargs):
        raise NotImplementedError(f"The function assume is not yet implemented for class {self.__class__.__name__}")

    def assign(self, pairs, *args, **kwargs):
        raise NotImplementedError(f"The function assign is not yet implemented for class {self.__class__.__name__}")

    def havoc(self, vars, *args, **kwargs):
        raise NotImplementedError(f"The function havoc is not yet implemented for class {self.__class__.__name__}")

    def label(self, label, *args, **kwargs):
        raise NotImplementedError(f"The function label is not yet implemented for class {self.__class__.__name__}")

    def goto(self, label, *args, **kwargs):
        raise NotImplementedError(f"The function goto is not yet implemented for class {self.__class__.__name__}")

    def call(self, name, inputs, outputs, *args, **kwargs):
        raise NotImplementedError(f"The function call is not yet implemented for class {self.__class__.__name__}")

    def ifs(self, condition, iftrue, iffalse, *args, **kwargs):
        raise NotImplementedError(f"The function ifs is not yet implemented for class {self.__class__.__name__}")

    def whiles(self, condition, body, *args, **kwargs):
        raise NotImplementedError(f"The function whiles is not yet implemented for class {self.__class__.__name__}")

    def sequence(self, statements, *args, **kwargs):
        raise NotImplementedError(f"The function sequence is not yet implemented for class {self.__class__.__name__}")

    def choice(self, statements, *args, **kwargs):
        raise NotImplementedError(f"The function choice is not yet implemented for class {self.__class__.__name__}")

    def statement(self, statement, *args, **kwargs):
        match statement:
            case Annotated(inner, attributes, scope, resolve):
                tags, attributes_ = self.expand_tags(attributes)
                return self.annotated_statement(
                    inner,
                    tags,
                    attributes,
                    attributes_,
                    scope,
                    resolve,
                    *args,
                    **kwargs,
                )

            case Return():
                return self.returns(*args, **kwargs)

            case Break():
                return self.breaks(*args, **kwargs)

            case Continue():
                return self.continues(*args, **kwargs)

            case Assume(formula):
                return self.assume(formula, *args, **kwargs)

            case Assign(pairs):
                return self.assign(pairs, *args, **kwargs)

            case Havoc(vars):
                return self.havoc(vars, *args, **kwargs)

            case Label(label):
                return self.label(label, *args, **kwargs)

            case Goto(label):
                return self.goto(label, *args, **kwargs)

            case Call(name, inputs, outputs):
                return self.call(name, inputs, outputs, *args, **kwargs)

            case If(condition, iftrue, iffalse):
                return self.ifs(condition, iftrue, iffalse, *args, **kwargs)

            case While(condition, body):
                return self.whiles(condition, body, *args, **kwargs)

            case Sequence(statements):
                return self.sequence(statements, *args, **kwargs)

            case Choice(statements):
                return self.choice(statements, *args, **kwargs)

            case _:
                self.unknown("statement", statement)

    def set_logic(self, logic, *args, **kwargs):
        raise NotImplementedError(f"The function set_logic is not yet implemented for class {self.__class__.__name__}")

    def get_assertions(self, *args, **kwargs):
        raise NotImplementedError(
            f"The function get_assertions is not yet implemented for class {self.__class__.__name__}"
        )

    def get_witness(self, *args, **kwargs):
        raise NotImplementedError(
            f"The function get_witness is not yet implemented for class {self.__class__.__name__}"
        )

    def get_info(self, keyword, *args, **kwargs):
        raise NotImplementedError(f"The function get_info is not yet implemented for class {self.__class__.__name__}")

    def set_info(self, keyword, argument, *args, **kwargs):
        raise NotImplementedError(f"The function set_info is not yet implemented for class {self.__class__.__name__}")

    def get_option(self, keyword, *args, **kwargs):
        raise NotImplementedError(f"The function get_option is not yet implemented for class {self.__class__.__name__}")

    def set_option(self, keyword, argument, *args, **kwargs):
        raise NotImplementedError(f"The function set_option is not yet implemented for class {self.__class__.__name__}")

    def asserts(self, formula, *args, **kwargs):
        raise NotImplementedError(f"The function asserts is not yet implemented for class {self.__class__.__name__}")

    def declare_sort(self, name, params, *args, **kwargs):
        raise NotImplementedError(
            f"The function declare_sort is not yet implemented for class {self.__class__.__name__}"
        )

    def define_sort(self, name, params, body, *args, **kwargs):
        raise NotImplementedError(
            f"The function define_sort is not yet implemented for class {self.__class__.__name__}"
        )

    def declare_datatypes(self, sorts, datatypes, *args, **kwargs):
        raise NotImplementedError(
            f"The function declare_datatypes is not yet implemented for class {self.__class__.__name__}"
        )

    def declare_var(self, name, type, *args, **kwargs):
        raise NotImplementedError(
            f"The function declare_var is not yet implemented for class {self.__class__.__name__}"
        )

    def declare_fun(self, name, arguments, result, *args, **kwargs):
        raise NotImplementedError(
            f"The function declare_fun is not yet implemented for class {self.__class__.__name__}"
        )

    def define_fun(self, name, arguments, result, body, *args, **kwargs):
        raise NotImplementedError(f"The function define_fun is not yet implemented for class {self.__class__.__name__}")

    def define_funs_rec(self, funs, bodies, *args, **kwargs):
        raise NotImplementedError(
            f"The function define_funs_rec is not yet implemented for class {self.__class__.__name__}"
        )

    def define_proc(self, name, inputs, outputs, locals, body, *args, **kwargs):
        raise NotImplementedError(
            f"The function define_proc is not yet implemented for class {self.__class__.__name__}"
        )

    def define_procs_rec(self, procs, bodies, *args, **kwargs):
        raise NotImplementedError(
            f"The function define_procs_rec is not yet implemented for class {self.__class__.__name__}"
        )

    def annotate_tag(self, tag, attributes, *args, **kwargs):
        raise NotImplementedError(
            f"The function annotate_tag is not yet implemented for class {self.__class__.__name__}"
        )

    def select_trace(self, model, globals, proc_name, steps, violation, using, *args, **kwargs):
        raise NotImplementedError(
            f"The function select_trace is not yet implemented for class {self.__class__.__name__}"
        )

    def verify_call(self, name, inputs, *args, **kwargs):
        raise NotImplementedError(
            f"The function verify_call is not yet implemented for class {self.__class__.__name__}"
        )

    def command(self, command, *args, **kwargs):
        match command:
            case SetLogic(logic):
                return self.set_logic(logic, *args, **kwargs)

            case GetAssertions():
                return self.get_assertions(*args, **kwargs)

            case GetWitness():
                return self.get_witness(*args, **kwargs)

            case GetInfo(keyword):
                return self.get_info(keyword, *args, **kwargs)

            case SetInfo(keyword, argument):
                return self.set_info(keyword, argument, *args, **kwargs)

            case GetOption(keyword):
                return self.get_option(keyword, *args, **kwargs)

            case SetOption(keyword, argument):
                return self.set_option(keyword, argument, *args, **kwargs)

            case Assert(formula):
                return self.asserts(formula, *args, **kwargs)

            case DeclareSort(Sort(name, params)):
                return self.declare_sort(name, params, *args, **kwargs)

            case DefineSort(Sort(name, params), body):
                return self.define_sort(name, params, body, *args, **kwargs)

            case DeclareDatatypes(sorts, datatypes):
                return self.declare_datatypes(sorts, datatypes, *args, **kwargs)

            case DeclareVar(Variable(name, _, type)):
                return self.declare_var(name, type, *args, **kwargs)

            case DeclareFun(Function(name, arguments, result)):
                return self.declare_fun(name, arguments, result, *args, **kwargs)

            case DefineFun(Function(name, arguments, result), body):
                return self.define_fun(name, arguments, result, body, *args, **kwargs)

            case DefineFunsRec(funs, bodies):
                return self.define_funs_rec(funs, bodies, *args, **kwargs)

            case DefineProc(Procedure(name, inputs, outputs, locals), body):
                return self.define_proc(name, inputs, outputs, locals, body, *args, **kwargs)

            case DefineProcsRec(procs, bodies):
                return self.define_procs_rec(procs, bodies, *args, **kwargs)

            case AnnotateTag(tag, attributes):
                if tag not in self.annotations:
                    self.annotations[tag] = []
                self.annotations[tag].extend(attributes)
                return self.annotate_tag(tag, attributes, *args, **kwargs)

            case SelectTrace(Trace(model, globals, proc_name, steps, violation, using)):
                return self.select_trace(model, globals, proc_name, steps, violation, using, *args, **kwargs)

            case VerifyCall(name, inputs):
                return self.verify_call(name, inputs, *args, **kwargs)

            case _:
                self.unknown("command", command)


class VisitorWithShortcuts(Visitor):
    def bool_type(self, *args, **kwargs):
        raise NotImplementedError(f"The function bool_type is not yet implemented for class {self.__class__.__name__}")

    def int_sort(self, *args, **kwargs):
        raise NotImplementedError(f"The function int_sort is not yet implemented for class {self.__class__.__name__}")

    def real_sort(self, *args, **kwargs):
        raise NotImplementedError(f"The function real_sort is not yet implemented for class {self.__class__.__name__}")

    def array_sort(self, index_sort, elem_sort, *args, **kwargs):
        raise NotImplementedError(f"The function array_sort is not yet implemented for class {self.__class__.__name__}")

    def unhandled_sort(self, name, arguments, *args, **kwargs):
        raise NotImplementedError(
            f"The function sort is not yet implemented for class {self.__class__.__name__} "
            f"for sort {name} with arguments {arguments}"
        )

    def sort(self, name, arguments, *args, **kwargs):
        if name == "Bool" and len(arguments) == 0:
            return self.bool_sort()
        elif name == "Int" and len(arguments) == 0:
            return self.int_sort()
        elif name == "Real" and len(arguments) == 0:
            return self.real_sort()
        elif name == "Array" and len(arguments) == 2:
            first_param = arguments[0]
            second_param = arguments[1]
            index_sort = self.sort(first_param.name, first_param.args, *args, **kwargs)
            elem_sort = self.sort(second_param.name, second_param.args, *args, **kwargs)
            return self.array_sort(index_sort, elem_sort, *args, **kwargs)

        return self.unhandled_sort(name, arguments, *args, **kwargs)

    def bv_literal(self, value, width, *args, **kwargs):
        raise NotImplementedError(f"The function bv_literal is not yet implemented for class {self.__class__.__name__}")

    def fp_literal(self, value, exponent, significand, *args, **kwargs):
        raise NotImplementedError(f"The function fp_literal is not yet implemented for class {self.__class__.__name__}")

    def bool_literal(self, value, *args, **kwargs):
        raise NotImplementedError(
            f"The function bool_literal is not yet implemented for class {self.__class__.__name__}"
        )

    def int_literal(self, value, *args, **kwargs):
        raise NotImplementedError(
            f"The function int_literal is not yet implemented for class {self.__class__.__name__}"
        )

    def real_literal(self, numerator, denominator, *args, **kwargs):
        raise NotImplementedError(
            f"The function real_literal is not yet implemented for class {self.__class__.__name__}"
        )

    def array_literal(self, value, index_sort, elem_sort, *args, **kwargs):
        raise NotImplementedError(
            f"The function array_literal is not yet implemented for class {self.__class__.__name__}"
        )

    def unhandled_literal(self, value, sort, *args, **kwargs):
        raise NotImplementedError(
            f"The function literal is not yet implemented for class {self.__class__.__name__} "
            f"for literal {value} of sort {sort}"
        )

    def literal(self, value, sort, *args, **kwargs):
        match sort:
            case BitVec(width):
                return self.bv_literal(value, width, *args, **kwargs)
            case FloatingPoint(exponent, significand):
                return self.fp_literal(value, exponent, significand, *args, **kwargs)
            case Sort(name, sort_args):
                if name == "Bool" and len(sort_args) == 0:
                    return self.bool_literal(value, *args, **kwargs)
                elif name == "Int" and len(sort_args) == 0:
                    return self.int_literal(value, *args, **kwargs)
                elif name == "Real" and len(sort_args) == 0:
                    assert isinstance(value, Fraction), "Real literal must be a tuple of (numerator, denominator)"
                    return self.real_literal(value.numerator, value.denominator, *args, **kwargs)
                elif name == "Array" and len(sort_args) == 2:
                    index_sort = self.sort(sort_args[0], *args, **kwargs)
                    elem_sort = self.sort(sort_args[1], *args, **kwargs)
                    return self.array_literal(value, index_sort, elem_sort, *args, **kwargs)

        return self.unhandled_literal(value, sort, *args, **kwargs)

    def and_func(self, function_args, *args, **kwargs):
        raise NotImplementedError(f"The function and_func is not yet implemented for class {self.__class__.__name__}")

    def or_func(self, function_args, *args, **kwargs):
        raise NotImplementedError(f"The function or_func is not yet implemented for class {self.__class__.__name__}")

    def not_func(self, function_arg, *args, **kwargs):
        raise NotImplementedError(f"The function not_func is not yet implemented for class {self.__class__.__name__}")

    def implication(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(
            f"The function implication is not yet implemented for class {self.__class__.__name__}"
        )

    def equality(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(f"The function equality is not yet implemented for class {self.__class__.__name__}")

    def add(self, function_args, *args, **kwargs):
        raise NotImplementedError(f"The function add is not yet implemented for class {self.__class__.__name__}")

    def minus(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(f"The function minus is not yet implemented for class {self.__class__.__name__}")

    def multiply(self, function_args, *args, **kwargs):
        raise NotImplementedError(f"The function multiply is not yet implemented for class {self.__class__.__name__}")

    def div(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(f"The function div is not yet implemented for class {self.__class__.__name__}")

    def less_than(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(f"The function less_than is not yet implemented for class {self.__class__.__name__}")

    def less_than_or_equals(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(
            f"The function less_than_or_equals is not yet implemented for class {self.__class__.__name__}"
        )

    def greater_than(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(
            f"The function greater_than is not yet implemented for class {self.__class__.__name__}"
        )

    def greater_than_or_equals(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(
            f"The function greater_than_or_equals is not yet implemented for class {self.__class__.__name__}"
        )

    def mod(self, arg1, arg2, *args, **kwargs):
        raise NotImplementedError(f"The function mod is not yet implemented for class {self.__class__.__name__}")

    def array_select(self, array_term, index_term, *args, **kwargs):
        raise NotImplementedError(
            f"The function array_select is not yet implemented for class {self.__class__.__name__}"
        )

    def array_store(self, array_term, index_term, value_term, *args, **kwargs):
        raise NotImplementedError(
            f"The function array_store is not yet implemented for class {self.__class__.__name__}"
        )

    def constant(self, name, *args, **kwargs):
        raise NotImplementedError(f"The function constant is not yet implemented for class {self.__class__.__name__}")

    def unhandled_application(self, function, arguments, *args, **kwargs):
        raise NotImplementedError(
            f"The function application is not yet implemented for class {self.__class__.__name__} "
            f"for function {function} with arguments {arguments}"
        )

    def floor(self, arg, *args, **kwargs):
        raise NotImplementedError(f"The function floor is not yet implemented for class {self.__class__.__name__}")

    def ceiling(self, arg, *args, **kwargs):
        raise NotImplementedError(f"The function ceiling is not yet implemented for class {self.__class__.__name__}")

    def to_real(self, arg, *args, **kwargs):
        raise NotImplementedError(f"The function to_real is not yet implemented for class {self.__class__.__name__}")

    def application(self, function, arguments, *args, **kwargs):
        processed_arguments = [self.term(arg, *args, **kwargs) for arg in arguments]

        match function:
            case "and":
                return self.and_func(processed_arguments, *args, **kwargs)
            case "or":
                return self.or_func(processed_arguments, *args, **kwargs)
            case "not" if len(arguments) == 1:
                return self.not_func(processed_arguments[0], *args, **kwargs)
            case "=>":
                result = processed_arguments[0]
                for i in range(1, len(processed_arguments)):
                    result = self.implication(result, processed_arguments[i], *args, **kwargs)
                return result
            case "=":
                if len(processed_arguments) == 1:
                    return processed_arguments[0]

                result = self.bool_literal(True, *args, **kwargs)
                for i in range(len(processed_arguments) - 1):
                    result = self.and_func(
                        [
                            result,
                            self.equality(
                                processed_arguments[i],
                                processed_arguments[i + 1],
                                *args,
                                **kwargs,
                            ),
                        ],
                        *args,
                        **kwargs,
                    )
                return result
            case "+":
                return self.add(processed_arguments, *args, **kwargs)
            case "-":
                if len(processed_arguments) == 1:
                    # Negation
                    return self.minus(
                        self.int_literal(0, *args, **kwargs),
                        processed_arguments[0],
                        *args,
                        **kwargs,
                    )

                result = processed_arguments[0]
                for i in range(1, len(processed_arguments)):
                    result = self.minus(result, processed_arguments[i], *args, **kwargs)
                return result
            case "*":
                return self.multiply(processed_arguments, *args, **kwargs)
            case "div":
                result = processed_arguments[0]
                for i in range(1, len(processed_arguments)):
                    result = self.div(result, processed_arguments[i], *args, **kwargs)
                return result

            case "mod":
                assert len(processed_arguments) == 2
                return self.mod(processed_arguments[0], processed_arguments[1], *args, **kwargs)

            # Boolean functions
            case "<" if len(arguments) == 2:
                return self.less_than(processed_arguments[0], processed_arguments[1], *args, **kwargs)
            case "<=" if len(arguments) == 2:
                return self.less_than_or_equals(processed_arguments[0], processed_arguments[1], *args, **kwargs)
            case ">" if len(arguments) == 2:
                return self.greater_than(processed_arguments[0], processed_arguments[1], *args, **kwargs)
            case ">=" if len(arguments) == 2:
                return self.greater_than_or_equals(processed_arguments[0], processed_arguments[1], *args, **kwargs)

            # Array functions
            case "select" if len(arguments) == 2:
                array_term = processed_arguments[0]
                index_term = processed_arguments[1]
                return self.array_select(array_term, index_term, *args, **kwargs)
            case "store" if len(arguments) == 3:
                array_term = processed_arguments[0]
                index_term = processed_arguments[1]
                value_term = processed_arguments[2]
                return self.array_store(array_term, index_term, value_term, *args, **kwargs)

            # MathSAT specific functions
            case "floor" if len(arguments) == 1:
                return self.floor(processed_arguments[0], *args, **kwargs)
            case "ceiling" if len(arguments) == 1:
                return self.ceiling(processed_arguments[0], *args, **kwargs)

            # Real functions
            case "to_real" if len(arguments) == 1:
                return self.to_real(processed_arguments[0], *args, **kwargs)

            case const if len(arguments) == 0:
                return self.constant(const, *args, **kwargs)

        return self.unhandled_application(function, arguments, *args, **kwargs)
