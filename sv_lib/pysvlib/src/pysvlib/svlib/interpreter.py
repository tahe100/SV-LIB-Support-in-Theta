# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import contextlib

from pysvlib.svlib import Variable
from pysvlib.svlib.syntax import ChoiceStep, HavocStep
from pysvlib.svlib.visitor import Visitor


class Interpreter(Visitor):
    def __init__(self):
        super().__init__()

        self.globals = []

        self.functions = {}
        self.procedures = {}
        self.traces = []

    def literal(self, value, sort, state):
        return value

    def variable(self, name, sort, state):
        sort, value = state[name]
        return value

    def binder(self, quantifier, bound, body, state):
        raise NotImplementedError("not executable")

    def application(self, function, arguments, state):
        arguments_ = [self.term(argument, state) for argument in arguments]

        match function, arguments_:
            case _ if function in self.functions:
                formals, result, body = self.functions[function.name]
                update_ = self._update(formals, arguments_)
                return self.term(body, state | update_)

            case _:
                raise NotImplementedError(f"unsupported function: {function}")

    def returns(self, state, input):
        raise Returned()

    def breaks(self, state, input):
        raise Breaked()

    def continues(self, state, input):
        raise Continued()

    def annotated_statement(self, inner, tags, attributes, attributes_, scope, resolve, state, input):
        self.statement(inner, state)

    def assume(self, formula, state, input):
        if not self.term(formula, state):
            raise AssumtionFiat(formula)

    def assign(self, pairs, state, input):
        for var, rhs in pairs:
            state[var.name] = (var.sort, self.term(rhs, state))

    def havoc(self, vars, state, input):
        updates = input.havoc(vars)

        for var, value in updates:
            state[var.name] = (var.sort, value)

    def choice(self, statements, state, input):
        index = input.choice(len(statements))

        self.statement(statements[index])

    def sequence(self, statements, state, input):
        for statement in statements:
            self.statement(statement, state, input)

    def call(self, name, arguments, receiver, state, input):
        inputs, outputs, locals, body = self.procedures[name]

        updates = input.init_proc_vars(name, outputs, locals)

        state_ = {}

        for name in self.globals:
            state_[name] = state[name]

        for var, val in updates:
            state_[var.name] = (var.sort, val)

        try:
            self.statement(body, state_, input)

        except Returned:
            with contextlib.suppress(Returned):
                pass

        for name in self.globals:
            state[name] = state_[name]

        for var, out in zip(receiver, outputs, strict=True):
            state[var.name] = state_[out.name]

    def ifs(self, condition, if_true, if_false, state, input):
        if self.term(condition, state):
            self.statement(if_true, state, input)
        else:
            self.statement(if_false, state, input)

    def whiles(self, condition, body, state, invariant):
        while self.term(condition, state):
            try:
                self.statement(body, state, invariant)

            except Breaked:
                break

            except Continued:
                continue

    def set_logic(self, logic):
        pass

    def get_assertions(self):
        pass

    def get_witness(self):
        pass

    def get_option(self, keyword, argument):
        pass

    def set_option(self, keyword, argument):
        pass

    def get_info(self, keyword, argument):
        pass

    def set_info(self, keyword, argument):
        pass

    def asserts(self, formula):
        pass

    def declare_sort(self, name, params):
        pass

    def define_sort(self, name, params, body):
        pass

    def declare_datatypes(self, sorts, datatypes):
        pass

    def declare_fun(self, name, arguments, result):
        pass

    def define_fun(self, name, arguments, result, body):
        self.functions[name] = (arguments, body)

    def declare_var(self, name, sort):
        self.globals.append(Variable(name, None, sort))

    def define_proc(self, name, inputs, outputs, locals, body):
        self.procedures[name] = (inputs, outputs, locals, body)

    def define_procs_rec(self, procs, bodies):
        for proc, body in zip(procs, bodies, strict=True):
            self.define_proc(proc.name, proc.inputs, proc.outputs, proc.locals, body)

    def annotate_tag(self, tag, attributes):
        pass

    def select_trace(self, *trace):
        self.traces.append(trace)

    def verify_call(self, name, arguments):
        for trace in self.traces:
            model, globals, proc_name, steps, violation, using = trace

            if name == proc_name:
                old_functions = self.functions
                self.functions = old_functions.copy()

                try:
                    for definition in model:
                        self.command(definition)

                    input = TraceInput(globals, steps, violation, using)
                    inputs, outputs, locals, body = self.procedures[name]

                    initial = input.init_global_vars(self.globals)
                    updates = input.init_proc_vars(name, outputs, locals)

                    state = {}

                    for var, val in initial:
                        state[var.name] = (var.sort, val)

                    for var, val in updates:
                        state[var.name] = (var.sort, val)

                    self.statement(body, state, input)

                except Exception as e:
                    self.functions = old_functions
                    raise e


class UserInput:
    def _read(self, what, variables):
        for var in variables:
            value = input(f"  {var.name} = ")
            if value:
                value = eval(value)
            yield var, value

    def init_global_vars(self, globals):
        return self._read("init global variables", globals)

    def init_proc_vars(self, name, outputs, locals):
        return self._read(f"init procedure variables: {name}", outputs + locals)

    def havoc(self, variables):
        return self._read("havoc", variables)

    def choice(self, arity):
        return int(input(f"choice of {arity}: "))


class RandomInput:
    def __init__(self, seed):
        self.seed = seed

    def init_global_vars(self, globals):
        pass

    def init_proc_vars(self, name, outputs, locals):
        pass

    def havoc(self, variables):
        pass

    def choice(self, arity):
        pass


class TraceInput:
    def __init__(self, globals, steps, violation, using):
        self.globals = globals
        self.steps = steps
        self.violation = violation
        self.using = using

        self.index = -1

    def _update(self, vars, assign):
        stuff = {var.name: value for var, value in assign}
        return [(var, stuff.get(var.name)) for var in vars]

    def _step(self):
        assert self.index >= 0 and self.index < len(self.steps)
        step = self.steps[self.index]
        self.index = self.index + 1
        return step

    def init_global_vars(self, globals):
        assert self.index < 0
        self.index = 0
        return self._update(globals, self.globals)

    def init_proc_vars(self, name, outputs, locals):
        match self.step():
            case step:
                raise ValueError(f"expected (init-proc-vars _), found {step}")

    def havoc(self, vars):
        match self.step():
            case HavocStep(assign):
                return self._update(vars, assign)

            case step:
                raise ValueError(f"expected (havoc _), found {step}")

    def choice(self, arity):
        match self.step():
            case ChoiceStep(index):
                return index

            case step:
                raise ValueError(f"expected (choice _), found {step}")


class Breaked(Exception):
    pass


class Continued(Exception):
    pass


class Returned(Exception):
    pass


class AssumtionFiat(Exception):
    def __init__(self, formula):
        self.formula = formula
