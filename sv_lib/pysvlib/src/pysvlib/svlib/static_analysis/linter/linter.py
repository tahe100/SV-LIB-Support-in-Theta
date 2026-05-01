# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from typing import Optional

from pysvlib.sexpr import Symbol
from pysvlib.svlib.logics import SmtLibLogics
from pysvlib.svlib.static_analysis.linter.error import (
    DuplicateDeclaredSortError,
    DuplicateFunNameError,
    DuplicateVariableError,
    FunctionArityMismatchError,
    InvalidArgumentTypeError,
    InvalidFunNameError,
    InvalidProcNameError,
    InvalidSortError,
    InvalidSortNameError,
    InvalidTypeError,
    InvalidVariableNameError,
    LinterError,
    LinterException,
    LogicNotFoundError,
    SortArityMismatchError,
    SortIsNoneError,
    UndefinedFunctionError,
    UndefinedVariableError,
)
from pysvlib.svlib.syntax import BitVec, FloatingPoint, Param, Sort, Term, Type, Variable
from pysvlib.svlib.visitor import Visitor


class Linter(Visitor):
    def __init__(self):
        super().__init__()

        # self.global_variables[name] = sort
        self.global_variables: dict[str, Type] = {}

        # self.scope[var.name] = var
        self.scope: dict[str, Variable] = {}

        # declared_sorts[name] = arity
        self.declared_sorts: dict[str, int] = {}
        # declared_funs[name] = (arguments, result)
        self.declared_funs: dict[str, tuple[tuple[Variable, ...], Type]] = {}

        # builtin functions and logics
        # Set a default value so linting can continue even if select_logic never occurs
        self.smt_lib_logics = SmtLibLogics("LIA")
        # Collected errors during linting
        self.errors: list[LinterError] = []

    def lint(self, ast_without_linting):
        self._lint_without_errors(ast_without_linting)
        self._check_errors()

    def _lint_without_errors(self, ast_without_linting):
        for command in ast_without_linting:
            self.command(command)

        return self.errors

    def _check_errors(self):
        # Check if any errors were collected during linting and raise a summary exception.
        if self.errors:
            raise LinterException(self.errors)

    def declare_var(self, name: str, sort: Optional[int] = None, *args, **kwargs):
        # Variable Checks
        if name in self.global_variables:
            self.errors.append(DuplicateVariableError(name))
        if not self.__validate_name(name):
            self.errors.append(InvalidVariableNameError(name))
            return

        # Sort Checks:
        if sort is None:
            self.errors.append(SortIsNoneError(name))
            return
        if not isinstance(sort, (Param, BitVec, FloatingPoint, Sort)):
            self.errors.append(InvalidSortError(sort))
            return

        # validate type
        self.type(sort)

        # Add variable name to dict
        self.global_variables[name] = sort

    def declare_sort(self, name, arguments, *args, **kwargs):
        if not self.__validate_str(name):
            self.errors.append(InvalidSortNameError(name))
            return

        if not isinstance(arguments, tuple):
            self.errors.append(InvalidArgumentTypeError(name, "tuple", type(arguments).__name__))
            return

        if name in self.declared_sorts:
            self.errors.append(DuplicateDeclaredSortError(name))
            return

        self.declared_sorts[name] = len(arguments)

    def define_sort(self, name, params, body, *args, **kwargs):
        if not self.__validate_str(name):
            self.errors.append(InvalidSortNameError(name))
            return

        if name in self.declared_sorts:
            self.errors.append(DuplicateDeclaredSortError(name))
            return

        if not isinstance(body, (Param, BitVec, FloatingPoint, Sort)):
            self.errors.append(InvalidSortError(body))
            return

        self.sort(name, params)
        self.declared_sorts[name] = len(params)

    def declare_datatypes(self, sorts, datatypes, *args, **kwargs):
        pass

    def declare_fun(self, name, arguments, result, *args, **kwargs):
        if isinstance(name, Symbol):
            name = name.name

        if not self.__validate_str(name):
            self.errors.append(InvalidFunNameError(name))
            return

        if name in self.declared_funs:
            self.errors.append(DuplicateFunNameError(name))

        if not isinstance(arguments, tuple):
            self.errors.append(InvalidArgumentTypeError(name, "tuple", type(arguments).__name__))
            return

        # All elements of the arguments tuple have to be unique Variables
        self.__validate_params(arguments)

        # result has to be a type
        if not isinstance(result, Type):
            self.errors.append(InvalidTypeError(type(result).__name__, "function result"))
            return
        self.type(result)

        self.declared_funs[name] = (arguments, result)

    def define_fun(self, name, arguments, result, body, *args, **kwargs):
        if isinstance(name, Symbol):
            name = name.name
        elif not isinstance(name, str):
            self.errors.append(InvalidTypeError(type(name).__name__, "function name"))

        if not self.__validate_str(name):
            self.errors.append(InvalidFunNameError(name))

        if name in self.declared_funs:
            self.errors.append(DuplicateFunNameError(name))

        # All elements of the arguments lists have to be unique variables with valid types
        variables = self.__validate_params(arguments)

        # result has to be a type
        if not isinstance(result, Type):
            self.errors.append(InvalidTypeError(type(result).__name__, "function result"))
            return
        self.type(result)

        # body has to be a valid term and cannot reference outside scope variables
        self.scope = variables
        self.term(body)
        self.scope = {}

        self.declared_funs[name] = (arguments, result)

    def define_funs_rec(self, funs, bodies, *args, **kwargs):
        pass

    def define_proc(
        self,
        name,
        inputs: tuple[Variable],
        outputs: tuple[Variable],
        proc_locals: tuple[Variable],
        body,
        *args,
        **kwargs,
    ):
        if not self.__validate_name(name):
            self.errors.append(InvalidProcNameError(name))
            return

        # validate outputs and locals and add to scope
        params = proc_locals + outputs + inputs
        self.__validate_params(params)

        # set scope after validating locals and outputs
        self.scope = {var.name: var for var in (*proc_locals, *outputs, *inputs)}
        self.statement(body)
        self.scope = {}

    def define_procs_rec(self, procs, bodies, *args, **kwargs):
        pass

    def param(self, name, *args, **kwargs):
        pass

    def bitvec(self, bits, *args, **kwargs):
        pass

    def floating_point(self, exponent, significand, *args, **kwargs):
        pass

    def sort(self, name, arguments, *args, **kwargs):
        if not self.__validate_str(name):
            self.errors.append(InvalidSortNameError(name))

        if arguments is None:
            arguments = []

        # Check if its a builtin sort and if arity is 0 (primitive types)
        if name in self.smt_lib_logics.available_sorts:
            if len(arguments) > 0:
                self.errors.append(SortArityMismatchError(name, 0, len(arguments)))
                return
            return

        if name == "Array":
            if len(arguments) != 2:
                self.errors.append(SortArityMismatchError(name, 2, len(arguments)))
                return
            # Use Recursion to check all sorts and nested sorts in the array
            for arg in arguments:
                self.type(arg)
            # return if no error was thrown above
            return

        # check if its a declared sort and verify length of args and arity
        declared_sort = self.declared_sorts.get(name)
        if declared_sort is not None and declared_sort != len(arguments):
            self.errors.append(SortArityMismatchError(name, declared_sort, len(arguments)))
            return
        elif declared_sort is not None:
            return

        # Should be evaluated before this -> must be invalid
        self.errors.append(InvalidSortError(name))

    def literal(self, value, sort, *args, **kwargs):
        # sort has to be a valid type
        self.type(sort)
        # TODO: verify value is actually of defined type

    def variable(self, name, _proc_name, sort, *args, **kwargs):
        if not self.__validate_name(name):
            self.errors.append(InvalidVariableNameError(name))
            return

        if name not in self.global_variables and name not in self.scope:
            self.errors.append(UndefinedVariableError(name))

        # sort has to be a valid type
        self.type(sort)

    def application(self, function, arguments, *args, **kwargs):
        if not self.__validate_str(function):
            self.errors.append(InvalidFunNameError(function))
            return

        declared_fun = self.declared_funs.get(function)
        is_declared_var = function in self.global_variables
        builtin_funs = self.smt_lib_logics.available_functions
        is_builtin = function in builtin_funs

        scope_variable_exists = not self.is_scope_empty() and function in self.scope

        if (declared_fun is None and not is_declared_var) and not is_builtin and not scope_variable_exists:
            # This is fine since only copy of the set is returned
            available_funs = self.smt_lib_logics.available_functions.union(self.declared_funs.keys())
            self.errors.append(UndefinedFunctionError(function, available_funs))
            return

        # Just validate inner terms for builtins
        # TODO: we should not branch here and validate the arity of builtin functions too -> has to be added to parser
        if is_builtin:
            for term in arguments:
                if not isinstance(term, Term):
                    self.errors.append(InvalidTypeError(type(term).__name__, "application argument"))
                self.term(term)
            return

        # All arguments have to be valid terms
        if declared_fun is not None:
            fun_args, fun_result = declared_fun
            if len(arguments) != len(fun_args):
                self.errors.append(FunctionArityMismatchError(function, len(fun_args), len(arguments)))
            for term in arguments:
                if not isinstance(term, Term):
                    self.errors.append(InvalidTypeError(type(term).__name__, "application argument"))
                self.term(term, args)

    def binder(self, quantifier, bound, body, *args, **kwargs):
        pass

    def at(self, term, label, *args, **kwargs):
        pass

    def final(self, term, *args, **kwargs):
        pass

    def annotated_statement(self, inner, tags, attributes, attributes_, scope, resolve, *args, **kwargs):
        pass

    def returns(self, *args, **kwargs):
        pass

    def breaks(self, *args, **kwargs):
        pass

    def continues(self, *args, **kwargs):
        pass

    def assign(self, pairs, *args, **kwargs):
        pass

    def havoc(self, vars, *args, **kwargs):
        pass

    def label(self, label, *args, **kwargs):
        pass

    def goto(self, label, *args, **kwargs):
        pass

    def call(self, name, inputs, outputs, *args, **kwargs):
        pass

    def ifs(self, condition, iftrue, iffalse, *args, **kwargs):
        pass

    def whiles(self, condition, body, *args, **kwargs):
        pass

    def sequence(self, statements, *args, **kwargs):
        pass

    def choice(self, statements, *args, **kwargs):
        pass

    def set_logic(self, logic, *args, **kwargs):
        if not self.smt_lib_logics.logic_exists(logic):
            self.errors.append(LogicNotFoundError(logic))
            return

        # Set available builtin functions list based on set logic
        self.smt_lib_logics = SmtLibLogics(logic.upper())

    def get_assertions(self, *args, **kwargs):
        pass

    def get_witness(self, *args, **kwargs):
        pass

    def get_info(self, keyword, *args, **kwargs):
        pass

    def set_info(self, keyword, argument, *args, **kwargs):
        pass

    def get_option(self, keyword, *args, **kwargs):
        pass

    def set_option(self, keyword, argument, *args, **kwargs):
        pass

    def asserts(self, formula, *args, **kwargs):
        pass

    def annotate_tag(self, tag, attributes, *args, **kwargs):
        pass

    def select_trace(self, model, globals, proc_name, steps, violation, using, *args, **kwargs):
        pass

    def verify_call(self, name, inputs, *args, **kwargs):
        pass

    """Helper Functions"""

    def is_scope_empty(self):
        return len(self.scope) == 0

    def __validate_str(self, string: str):
        return isinstance(string, str) and string != "" and string is not None

    def __validate_name(self, name: str):
        return self.__validate_str(name) and not name.startswith("#")

    def __validate_params(self, vars: tuple[Variable, ...]) -> dict[str, Variable]:
        variables = {}
        for var in vars:
            if not (isinstance(var, Variable)):
                self.errors.append(
                    InvalidTypeError(
                        type(var).__name__,
                        f"function '{getattr(var, 'name', '?')}' input",
                    )
                )
                continue

            if not self.__validate_name(var.name):
                self.errors.append(InvalidVariableNameError(var.name))

            self.type(var.sort)

            if var.name in variables:
                self.errors.append(DuplicateVariableError(var.name))
                continue
            variables[var.name] = var

        return variables
