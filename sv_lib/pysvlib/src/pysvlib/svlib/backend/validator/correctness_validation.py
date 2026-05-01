# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from pysvlib.sexpr import print_sexprs
from pysvlib.sexpr.syntax import Symbol
from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.printer import format_list
from pysvlib.svlib.syntax import (
    Annotated,
    Application,
    Assert,
    Assign,
    Assume,
    Binder,
    Break,
    Call,
    Choice,
    Continue,
    DeclareDatatypes,
    DeclareFun,
    DeclareSort,
    DeclareVar,
    DefineFun,
    DefineSort,
    Function,
    GetAssertions,
    GetInfo,
    GetOption,
    Havoc,
    If,
    Literal,
    Return,
    Sequence,
    SetInfo,
    SetLogic,
    SetOption,
    Sort,
    Variable,
    While,
)
from pysvlib.svlib.visitor import Visitor


def validate_correctness(commands, solver=None) -> tuple[BackendResult, str]:
    validator = Validator()

    for command in commands:
        validator.command(command)

    script = validator.smtlib()

    if not solver:
        print(script)
        return BackendResult.Unknown, "no solver provided"

    result = solver.run_solver(script)
    match result:
        case Symbol("unsat"), *_:
            return BackendResult.Correct, ""

        case Symbol("sat"), *_:
            return BackendResult.Incorrect, ""

        case _ if solver:
            result_ = print_sexprs(result)
            raise ValueError(f"unexpected solver response: {result_}")


class Validator(Visitor):
    def __init__(self):
        super().__init__()

        self.var_index = 0

        self.globals = {}
        self.procedures = {}

        self.prelude = []
        self.axioms = []
        self.checks = []

    def _fresh_var(self, name, sort):
        self.var_index = self.var_index + 1
        return Variable(f"{name}#{str(self.var_index)}", None, sort)

    def _fresh_vars(self, names, sorts):
        vars_ = [self._fresh_var(name, sort) for name, sort in zip(names, sorts, strict=True)]
        update_ = {name: (var_.sort, var_) for name, var_ in zip(names, vars_, strict=True)}
        return vars_, update_

    def _modified(self, statement):
        match statement:
            case Annotated(inner, _, _, _):
                return self._modified(inner)

            case Break() | Return() | Continue():
                return set()

            case Assume(_phi):
                return set()

            case Havoc(vars):
                return {var.name for var in vars}

            case Assign(pairs):
                return {var.name for var, _ in pairs}

            case Call(_name, _inputs, outputs):
                # TODO: don't overapproximate this much here
                return self.globals.keys() | {var.name for var in outputs}

            case If(_condition, if_true, if_false):
                return self._modified(if_true) | self._modified(if_false)

            case While(_condition, body):
                return self._modified(body)

            case Choice(statements) | Sequence(statements):
                return {var for statement in statements for var in self._modified(statement)}

            case _:
                raise ValueError(f"cannot compute modified variables of statement {statement}")

    def resolve_property(self, keyword, attributes, scope, resolve, approx):
        formulas = self.resolve_attributes_as_terms(keyword, attributes, scope, resolve)
        # Note: do not evaluate here! Invariants need to be put into different states!
        return approx.conj(*formulas)

    def literal(self, value, sort, state):
        return Literal(value, sort)

    def variable(self, name, proc_name: str, sort, state):
        sort, value = state[name]
        return value

    def binder(self, quantifier, bound, body, state):
        raise NotImplementedError("avoid capture")

    def application(self, function, arguments, state):
        arguments_ = [self.term(argument, state) for argument in arguments]
        return Application(function, arguments_)

    def returns(self, approx, state, post, ret, brk, cont):
        return ret(state)

    def breaks(self, approx, state, post, ret, brk, cont):
        return brk(state)

    def continues(self, approx, state, post, ret, brk, cont):
        return cont(state)

    def annotated_statement(
        self,
        inner,
        tags,
        attributes,
        attributes_,
        scope,
        resolve,
        approx,
        state,
        post,
        ret,
        brk,
        cont,
    ):
        check = self.resolve_property("check-true", attributes + attributes_, scope, resolve, approx)
        check_ = self.term(check, state)

        match inner:
            case While(condition, body):
                invariant = self.resolve_property("invariant", attributes + attributes_, scope, resolve, approx)
                decreases = self.resolve_attributes_as_terms("decreases", attributes + attributes_, scope, resolve)

                # Note: we pass invariant and decreases unevaluated here!
                post_ = self.whiles(
                    condition,
                    body,
                    approx,
                    state,
                    post,
                    ret,
                    brk,
                    cont,
                    invariant,
                    decreases,
                )
                return approx.conj(check_, post_)

            case _:
                post_ = self.statement(inner, approx, state, post, ret, brk, cont)
                return approx.conj(check_, post_)

    def assume(self, formula, approx, state, post, ret, brk, cont):
        formula_ = self.term(formula, state)
        return approx.assume(formula_, post(state))

    def assign(self, pairs, approx, state, post, ret, brk, cont):
        update_ = {var.name: (var.sort, self.term(rhs, state)) for var, rhs in pairs}
        return post(state | update_)

    def havoc(self, vars, approx, state, post, ret, brk, cont):
        names = [var.name for var in vars]
        sorts = [var.sort for var in vars]
        bound_, update_ = self._fresh_vars(names, sorts)
        return approx.bind(bound_, post(state | update_))

    def ifs(self, condition, if_true, if_false, approx, state, post, ret, brk, cont):
        condition_ = self.term(condition, state)
        if_true_ = self.statement(if_true, approx, state, post, ret, brk, cont)
        if_false_ = self.statement(if_false, approx, state, post, ret, brk, cont)
        return approx.ite(condition_, if_true_, if_false_)

    def choice(self, statements, approx, state, post, ret, brk, cont):
        results_ = [self.statement(statement, approx, state, post, ret, brk, cont) for statement in statements]
        return approx.choice(results_)

    def sequence(self, statements, approx, state, post, ret, brk, cont):
        match statements:
            case []:
                return post(state)

            case first, *rest:

                def post_(state_):
                    return self.sequence(rest, approx, state_, post, ret, brk, cont)

                return self.statement(first, approx, state, post_, ret, brk, cont)

    def call(self, name, arguments, results, approx, state, post, ret, brk, cont):
        inputs, outputs, locals, body = self.procedures[name]

        def cont(update_):
            return post(state | update_)

        return self._verification_conditions_proc_call(
            name, inputs, outputs, locals, body, arguments, results, approx, cont
        )

    def whiles(self, condition, body, approx, state, post, ret, brk, cont, invariant, decreases):
        names = self._modified(body)
        entries = [state[name] for name in names]
        sorts = [sort for sort, _ in entries]

        bound_, update_ = self._fresh_vars(names, sorts)
        state_ = state | update_

        inv_now_ = self.term(invariant, state)
        inv_before_ = self.term(invariant, state_)

        match decreases:
            case []:
                decreases = None
            case [term]:
                decreases = term
            case _:
                raise NotImplementedError(f"multiple decreases clauses currently unsupported: {decreases}")

        if decreases:
            dec_before_ = self.term(decreases, state_)

        def loop(state__):
            inv_after_ = self.term(invariant, state__)

            if decreases:
                dec_after_ = self.term(decreases, state__)
                cond_after_ = self.term(condition, state__)

                zero = Literal(0, Sort("int", []))
                lower_ = Application("<=", [zero, dec_after_])
                upper_ = Application("<", [dec_after_, dec_before_])
                in_bounds_ = approx.assume(cond_after_, approx.conj(lower_, upper_))

                return approx.conj(inv_after_, in_bounds_)
            else:
                return inv_after_

        prog_ = If(condition, body, Break())
        phi_ = self.statement(prog_, approx, state_, loop, ret, post, loop)

        init_ = inv_now_
        loop_ = approx.bind(bound_, approx.assume(inv_before_, phi_))

        return approx.conj(init_, loop_)

    def set_logic(self, logic):
        logic = logic.replace("QF_", "")  # TODO: not always right
        self.prelude.append(SetLogic(logic))

    def get_assertions(self):
        self.prelude.append(GetAssertions())

    def get_witness(self):
        pass

    def get_option(self, keyword, argument):
        self.prelude.append(GetOption(keyword))

    def set_option(self, keyword, argument):
        match keyword, argument:
            case "produce-witnesses", _:
                self.prelude.append(SetOption("produce-models", argument))
                self.prelude.append(SetOption("produce-proofs", argument))

            case _:
                self.prelude.append(SetOption(keyword, argument))

    def get_info(self, keyword, argument):
        self.prelude.append(GetInfo(keyword))

    def set_info(self, keyword, argument):
        self.prelude.append(SetInfo(keyword, argument))

    def asserts(self, formula):
        # Note: don't add axioms sequentially, but bunch them up wrt. the individual verify-calls
        # self.prelude.append(Assert(formula))
        self.axioms.append(formula)

    def declare_sort(self, name, params):
        self.prelude.append(DeclareSort(Sort(name, params)))

    def define_sort(self, name, params, body):
        self.prelude.append(DefineSort(Sort(name, params), body))

    def declare_datatypes(self, sorts, datatypes):
        self.prelude.append(self, DeclareDatatypes(sorts, datatypes))

    def declare_fun(self, name, arguments, result):
        self.prelude.append(DeclareFun(Function(name, arguments, result)))

    def define_fun(self, name, arguments, result, body):
        self.prelude.append(DefineFun(Function(name, arguments, result), body))

    def declare_var(self, name, sort):
        var = Variable(name, None, sort)
        self.globals[name] = var
        self.prelude.append(DeclareVar(var))

    def define_proc(self, name, inputs, outputs, locals, body):
        self.procedures[name] = (inputs, outputs, locals, body)
        # Note: do not verify now, because some annotations may still come later
        # self.verify_proc(name)

    def define_procs_rec(self, procs, bodies):
        # TODO: use this information to compute sets of modified variables etc
        for proc, body in zip(procs, bodies, strict=True):
            self.define_proc(proc.name, proc.inputs, proc.outputs, proc.locals, body)

    def annotate_tag(self, tag, attributes):
        pass

    def select_trace(self, *args, **kwargs):
        raise NotImplementedError("select-trace commands are not supported for validating correctness witnesses")

    def _verification_conditions_proc_def(self, name, approx):
        inputs, outputs, locals, body = self.procedures[name]
        globals = [var for name, var in self.globals.items()]

        state = {}
        state |= {var.name: (var.sort, var) for var in globals}
        state |= {var.name: (var.sort, var) for var in inputs}
        state |= {var.name: (var.sort, var) for var in outputs}
        state |= {var.name: (var.sort, var) for var in locals}

        match body:
            case Annotated(inner, attributes, scope, resolve):
                tags, attributes_ = self.expand_tags(attributes)

                require = self.resolve_property("requires", attributes + attributes_, scope, resolve, approx)
                ensure = self.resolve_property("ensures", attributes + attributes_, scope, resolve, approx)

                def error(state_):
                    raise ValueError("non-local exit into nothing")

                def post(state_):
                    return self.term(ensure, state_)

                require_ = self.term(require, state)

                bound_ = globals + inputs + outputs + locals
                phi_ = self.statement(inner, approx, state, post, post, error, error)
                psi_ = approx.bind(bound_, approx.assume(require_, phi_))

                return psi_

            case _:
                # Note: don't check now! Procedures without contracts must be inlined always.
                return approx.true()

    def _verification_conditions_proc_call(self, name, inputs, outputs, locals, body, arguments, results, approx, cont):
        globals = [var for name, var in self.globals.items()]

        state = {}
        state |= {var.name: (var.sort, var) for var in globals}
        state |= {var.name: (var.sort, argument) for var, argument in zip(inputs, arguments, strict=True)}

        match body:
            case Annotated(_inner, attributes, scope, resolve):
                tags, attributes_ = self.expand_tags(attributes)
                require = self.resolve_property("requires", attributes + attributes_, scope, resolve, approx)
                require_ = self.term(require, state)

                return require_

            case _:
                state |= {var.name: (var.sort, var) for var in outputs}
                state |= {var.name: (var.sort, var) for var in locals}

                def error(state_):
                    raise ValueError("non-local exit into nothing")

                def post(state_):
                    globals_ = {var.name: state_[var.name] for var in globals}
                    results_ = {var.name: state_[var.name] for var in outputs}
                    return post(globals_ | results_)

                bound_ = globals + inputs + outputs + locals
                phi_ = self.statement(body, approx, state, post, post, error, error)
                psi_ = approx.bind(bound_, phi_)

                return psi_

    def verify_call(self, name, arguments):
        approx = All()

        conds = []

        for that in self.procedures:
            there = self._verification_conditions_proc_def(that, approx)
            conds.append(there)

        inputs, outputs, locals, body = self.procedures[name]

        def cont(update_):
            return approx.true()

        here = self._verification_conditions_proc_call(
            name, inputs, outputs, locals, body, arguments, outputs, approx, cont
        )
        conds.append(here)

        check = (self.axioms, conds)

        self.checks.append(check)

    def smtlib(self):
        approx = All()

        goals = []

        for axioms, conds in self.checks:
            axiom = approx.conj(*axioms)
            cond = approx.conj(*conds)
            goal = approx.assume(axiom, cond)
            goals.append(goal)

        assert_ = Assert(approx.neg(approx.conj(*goals)))

        script = format_list(self.prelude + [assert_])
        check_sat = (Symbol("check-sat"),)

        # cannot represent the check-sat with SV-LIB commands
        return [*script, check_sat]


class Approx:
    def _flatten_conj(self, arg):
        match arg:
            case Application("and", args):
                return self._flatten_conj_list(args)
            case Literal(True, Sort("Bool", ())):
                return []
            case _:
                return [arg]

    def _flatten_conj_list(self, args):
        return [res for arg in args for res in self._flatten_conj(arg)]

    def true(self):
        return Literal(True, Sort("Bool", ()))

    def neg(self, phi):
        return Application("not", [phi])

    def conj(self, *phis):
        phis_ = self._flatten_conj_list(phis)

        match phis_:
            case []:
                return self.true()
            case [phi_]:
                return phi_
            case _:
                return Application("and", phis_)

    def ite(self, condition, if_true, if_false):
        return Application("ite", [condition, if_true, if_false])


class All(Approx):
    def choice(self, paths):
        return Application("and", paths)

    def bind(self, bound, body):
        match bound, body:
            case [[], _]:
                return body
            case _, Literal(True, Sort("Bool", ())):
                return body
            case _:
                return Binder("forall", bound, body)

    def assume(self, pre, post):
        match pre, post:
            case Literal(True, Sort("Bool", ())), _:
                return post
            case _:
                return Application("=>", [pre, post])


class Ex(Approx):
    def choice(self, paths):
        return Application("or", paths)

    def bind(self, bound, body):
        match bound, body:
            case [[], _]:
                return body
            case _, Literal(True, Sort("Bool", ())):
                return body
            case _:
                return Binder("exists", bound, body)

    def assume(self, pre, post):
        match pre, post:
            case Literal(True, Sort("Bool", ())), _:
                return post
            case _:
                return self.conj("and", pre, post)
