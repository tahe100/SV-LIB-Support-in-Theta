# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional

from pysvlib.sexpr import Keyword, Symbol, inline_let, print_sexprs
from pysvlib.svlib.backend.chc.data import HornClause, ProcedureContext
from pysvlib.svlib.backend.data import BackendResult
from pysvlib.svlib.printer import format_list
from pysvlib.svlib.solver import Solver
from pysvlib.svlib.syntax import (
    Application,
    Assert,
    Binder,
    Command,
    DeclareFun,
    Function,
    SetLogic,
    Sort,
    Statement,
    Term,
    Variable,
    While,
)
from pysvlib.svlib.visitor import Visitor


def build_chc(horn: "HornTranslator", commands: list[Command]) -> list[Command]:
    for cmd in commands:
        horn.command(cmd)

    for proc in horn.procedure_context:
        horn.translate_procedure(proc)

    cmds = horn.procedures_to_chc()
    return cmds


def verify_chc(commands: list[Command], solver: Optional[Solver]) -> tuple[BackendResult, str, list[Command] | None]:
    horn = HornTranslator()
    cmds = build_chc(horn, commands)
    script = format_list(cmds)

    check = [(Symbol("check-sat"),)]
    script.extend(check)

    if solver:
        answer = solver.run_solver(script, get_model=True)
        answer = [inline_let(command, dict()) for command in answer]

        match answer:
            case [Symbol("sat"), [*model]] | [Symbol("sat"), *model]:
                witness = translate_correctness_witness(horn, model)
                return BackendResult.Correct, "", witness

            case [Symbol("unsat"), *_]:
                return BackendResult.Incorrect, "", None

            case [[Symbol("error"), *message]]:
                return BackendResult.Error, f"solver backend returned error: {message}"

            case _:
                raise NotImplementedError(f"Unexpected solver answer format: {answer}")
    else:
        text = print_sexprs(script)
        print(text)
        return BackendResult.Unknown, "no solver specified", None


def translate_correctness_witness(horn: "HornTranslator", model: list[Command]) -> list[Command]:
    # We express the invariants using the functions defined.
    # The variables in scope are hopefully stored in the correct order.

    witness = list(model)
    for proc, ctx in horn.procedure_context.items():
        tag = proc  # UH OH bad assumption

        pre_pred = f"{proc}_pre"
        pre_vars = tuple(Symbol(var.name) for var in horn.get_pre_cond_scope(ctx))
        pre_cmd = (
            Symbol("annotate-tag"),
            Symbol(tag),
            Keyword("requires"),
            (Symbol(pre_pred), *pre_vars),
        )
        witness.append(pre_cmd)

        post_pred = f"{proc}_post"
        post_vars = tuple(Symbol(var.name) for var in horn.get_post_cond_scope(ctx))
        post_cmd = (
            Symbol("annotate-tag"),
            Symbol(tag),
            Keyword("ensures"),
            (Symbol(post_pred), *post_vars),
        )
        witness.append(post_cmd)

    for pred, scope in horn.loop_heads.items():
        tag = horn.attributes_with_pp[pred]
        variables = tuple(Symbol(var.name) for var in scope)
        cmd = (
            Symbol("annotate-tag"),
            Symbol(tag),
            Keyword("invariant"),
            (Symbol(pred), *variables),
        )
        witness.append(cmd)

    return witness


# =====================================================================
#   Helpers
# =====================================================================
def mk_pred_call(name: str, args: List[Term]):
    if len(args) < 1:
        args = ()  # avoids packing a single argument in parentheses
    return Application(name, args)


def declare_predicate(name: str, args: List[Variable]):
    return DeclareFun(Function(name, [v for v in args], Sort("Bool", [])))


def make_forall(bound: List[Variable], body: Application):
    return Assert(Binder("forall", bound, body))


# =====================================================================
#   Horn Translator
# =====================================================================
class HornTranslator(Visitor):
    def __init__(self):
        super().__init__()
        self.procedure_context: Dict[str, ProcedureContext] = {}
        self.attributes_with_pp: Dict[str, str] = {}  # used to extract model answer from solver
        self.global_vars: Dict[str, Variable] = {}  # we need global vars in calls
        self.procs_to_verify: List[str] = []

        self.loop_entry: List[str] = []
        self.loop_exit: List[str] = []

        self.loop_heads = {}

    # =====================================================================
    #   CTX Helpers
    # =====================================================================
    def new_program_point(self, ctx: ProcedureContext, point_type: str | None):
        if point_type is None:
            point_type = ""
        idx = ctx.pp_counter
        ctx.pp_counter += 1
        p = f"{ctx.name}{point_type}_p{idx}"
        if p not in ctx.points:
            ctx.points.append(p)
        return p

    def append_clause(
        self,
        ctx,
        p_from,
        p_to,
        cond,
        new_args=None,
        fresh=None,
        from_kind=None,
        call_pre_args=None,
    ):
        clause = HornClause(
            p_from,
            p_to,
            cond,
            new_args,
            from_kind=from_kind,
            call_pre_args=call_pre_args,
        )
        ctx.clauses.append(clause)
        if fresh:
            ctx.fresh_vars_for_clause[(p_from, p_to)] = fresh

    def append_check_true(self, ctx, p_from, cond):
        clause = HornClause(p_from, None, cond)
        ctx.clauses.append(clause)

    def fresh_var(self, var_name, sort):
        return Variable(f"{var_name}'", "", sort)  # add ' at the end

    def get_global_scope(self, ctx):
        return list(ctx.vars.values())

    def get_pre_cond_scope(self, callee_ctx):
        return list((self.global_vars | callee_ctx.inputs).values())

    def get_post_cond_scope(self, callee_ctx):
        return list((self.global_vars | callee_ctx.inputs | callee_ctx.outputs).values())

    # =====================================================================
    #   Visitor: command
    # =====================================================================

    def define_proc(self, name, inputs, outputs, locals, body, *args, **kwargs):
        # only temp save, we need to see all tags. Translation happens in translate_procedure
        proc = ProcedureContext(name=name, pp_counter=0, body=body)
        # vars, inputs and outputs as dict for ProcedureContext
        for v in body.scope.values():
            proc.vars[v.name] = Variable(v.name, v.procedure, v.sort)
        for v in inputs:
            proc.inputs[v.name] = Variable(v.name, v.procedure, v.sort)
        for v in outputs:
            proc.outputs[v.name] = Variable(v.name, v.procedure, v.sort)
        self.procedure_context[name] = proc
        return

    def set_logic(self, cmd):
        return

    def set_info(self, keyword, argument):
        return

    def set_option(self, keyword, argument):
        return

    def verify_call(self, name, inputs):
        self.procs_to_verify.append(name)  # we need to see all procedures before translating
        return self

    def get_witness(self, *args, **kwargs):
        return

    def declare_var(self, name, type, *args, **kwargs):
        self.global_vars[name] = Variable(name, None, type)
        return

    # =====================================================================
    #   Visitor: statement
    # =====================================================================

    def sequence(self, statements: List[Statement], ctx: ProcedureContext, p_from: str):
        p = p_from
        for s in statements:
            if p is None:
                return None
            p = self.statement(s, ctx, p)
        return p

    def annotated_statement(self, inner, tags, attributes, attributes_, scope, resolve, ctx, p_from):
        # add check-true at the program point after the inner statement
        for term in self.resolve_attributes_as_terms("check-true", attributes + attributes_, scope, resolve):
            # check-true clauses attach to p_from
            self.append_check_true(ctx, p_from, term)

        match inner, tags:
            case While(_condition, _body), [tag, *_]:
                self.attributes_with_pp[p_from] = tag
            case While(_condition, _body), _:
                raise ValueError(f"no tag for annotated statement with attributes {attributes + attributes_}")

        p_to = self.statement(inner, ctx, p_from)

        return p_to

    def annotate_tag(self, tag, attributes, *args, **kwargs):
        return

    def assume(self, formula, ctx, p_from):
        p_to = self.new_program_point(ctx, "_assume")
        self.append_clause(ctx, p_from, p_to, formula)
        return p_to

    def assign(self, pairs, ctx, p_from):
        p_to = self.new_program_point(ctx, "_assign")
        updates = dict(ctx.vars)
        for lhs, rhs in pairs:
            updates[lhs.name] = rhs
        self.append_clause(ctx, p_from, p_to, Application("true", ()), new_args=updates.values())
        return p_to

    def havoc(self, vars, ctx, p_from):
        p_to = self.new_program_point(ctx, "_havoc")
        updates = dict(ctx.vars)
        fresh = []
        for v in vars:
            fv = self.fresh_var(v.name, v.sort)
            updates[v.name] = fv
            fresh.append(fv)
        cond = Application("true", ())
        self.append_clause(ctx, p_from, p_to, cond, new_args=updates.values(), fresh=fresh)
        return p_to

    def call(self, name, inputs, outputs, ctx, p_from):
        callee = name
        if callee not in self.procedure_context:
            raise ValueError(f"Procedure {callee} not defined before call")

        pre = f"{callee}_pre"
        post = f"{callee}_post"

        # Program point after call
        p_after = self.new_program_point(ctx, "_after_call")

        self.append_clause(
            ctx,
            p_from,
            pre,
            Application("true", ()),
            new_args=list(self.global_vars.values()) + list(inputs),
        )

        # Fresh outputs
        fresh_returns = []
        for lhs in outputs:
            fr = self.fresh_var(lhs.name, lhs.sort)
            fresh_returns.append(fr)

        # Fresh globals
        fresh_globals = []
        for g in self.global_vars.values():
            fg = self.fresh_var(g.name, g.sort)
            fresh_globals.append(fg)

        # Condition: callee_post(globals', outputs', inputs)
        cond = Application(post, fresh_globals + fresh_returns + list(inputs))

        # Update caller state
        updates = dict(ctx.vars)
        for lhs, fr in zip(outputs, fresh_returns, strict=True):
            updates[lhs.name] = fr

        # Globals get updated too
        for g, fg in zip(self.global_vars.values(), fresh_globals, strict=True):
            updates[g.name] = fg

        new_args = [updates.get(v.name, v) for v in ctx.vars.values()]

        self.append_clause(
            ctx,
            pre,
            p_after,
            cond,
            new_args=new_args,
            fresh=fresh_returns + fresh_globals,
            from_kind="pre",
            call_pre_args=list(self.global_vars.values()) + list(inputs),
        )

        return p_after

    def ifs(self, condition, if_true, if_false, ctx, p_from):
        p_then = self.new_program_point(ctx, "_if_then")
        p_else = self.new_program_point(ctx, "_if_else")
        p_join = self.new_program_point(ctx, "_if_join")

        self.append_clause(ctx, p_from, p_then, condition)
        self.append_clause(ctx, p_from, p_else, Application("not", [condition]))

        end_then = self.statement(if_true, ctx, p_then)
        end_else = self.statement(if_false, ctx, p_else)

        if end_then is not None:
            self.append_clause(ctx, end_then, p_join, Application("true", ()))
        if end_else is not None:
            self.append_clause(ctx, end_else, p_join, Application("true", ()))

        return p_join

    def whiles(self, condition, body, ctx, p_from):
        self.loop_heads[p_from] = self.get_global_scope(ctx)  # remember this to generate invarians later

        p_body = self.new_program_point(ctx, "_while_body")
        p_join = self.new_program_point(ctx, "_while_join")

        self.loop_entry.append(p_from)  # required for continue statement
        self.loop_exit.append(p_join)  # required for break statement

        self.append_clause(ctx, p_from, p_body, condition)
        self.append_clause(ctx, p_from, p_join, Application("not", [condition]))

        p_end = self.statement(body, ctx, p_body)

        if p_end is not None:
            self.append_clause(ctx, p_end, p_from, Application("true", ()))

        self.loop_entry.pop()  # clear for next while statement
        self.loop_exit.pop()

        return p_join

    def returns(self, ctx, p_from):
        clause = HornClause(
            p_from=p_from,
            p_to=f"{ctx.name}_post",
            condition=Application("true", ()),
            new_args=self.get_post_cond_scope(ctx),
            is_return=True,
        )
        ctx.clauses.append(clause)
        return None  # returning none to avoid linking the return to loop- / if-join

    def breaks(self, ctx, p):
        if not self.loop_exit:
            raise ValueError("Break is outside a loop")

        p_join = self.loop_exit[-1]  # last entry is most recent

        self.append_clause(ctx, p, p_join, Application("true", ()))

        return None

    def continues(self, ctx, p):
        if not self.loop_entry:
            raise ValueError("Continue is outside a loop")

        p_join = self.loop_entry[-1]  # last entry is most recent

        self.append_clause(ctx, p, p_join, Application("true", ()))

        return p

    # =====================================================================
    #   Procedure Translation
    # =====================================================================

    def translate_procedure(self, name):
        ctx = self.procedure_context[name]
        ctx.entry = self.new_program_point(ctx, None)
        ctx.exit = self.statement(ctx.body, ctx, ctx.entry)
        self.procedure_context[ctx.name] = ctx
        return

    # =====================================================================
    #   CHC generation
    # =====================================================================

    def procedures_to_chc(self):
        cmds = [SetLogic("HORN")]

        for name, ctx in self.procedure_context.items():
            pre_binder = self.get_pre_cond_scope(ctx)
            full_binder = self.get_global_scope(ctx)
            post_binder = self.get_post_cond_scope(ctx)

            # predicate declarations
            cmds.append(declare_predicate(f"{name}_pre", pre_binder))
            for p in ctx.points:
                cmds.append(declare_predicate(p, full_binder))
            cmds.append(declare_predicate(f"{name}_post", post_binder))

            # pre assert - only for verify-call procedures
            if name in self.procs_to_verify:
                if len(pre_binder) < 1:
                    cmds.append(Assert(Application(f"{name}_pre", ())))
                else:
                    pre_app = mk_pred_call(f"{name}_pre", pre_binder)
                    cmds.append(make_forall(pre_binder, pre_app))

            # entry
            entry_body = Application(
                "=>",
                [
                    mk_pred_call(f"{name}_pre", pre_binder),
                    mk_pred_call(ctx.entry, full_binder),
                ],
            )
            cmds.append(make_forall(full_binder, entry_body))

            # transitions
            for c in ctx.clauses:
                # check-true clauses have no target clause
                if c.p_to is None:
                    from_app = mk_pred_call(c.p_from, full_binder)
                    body = Application("=>", [from_app, c.condition])
                    cmds.append(make_forall(full_binder, body))
                    continue

                if c.from_kind == "pre":
                    from_app = mk_pred_call(c.p_from, c.call_pre_args)
                else:
                    from_app = mk_pred_call(c.p_from, full_binder)

                if c.is_return:  # link return to the post condition point
                    to_app = mk_pred_call(c.p_to, c.new_args)
                    body = Application("=>", [from_app, to_app])
                    cmds.append(make_forall(full_binder, body))
                    continue

                args_to = c.new_args if c.new_args is not None else full_binder
                to_app = mk_pred_call(c.p_to, args_to)

                and_app = Application("and", [from_app, c.condition])
                body = Application("=>", [and_app, to_app])

                quant = full_binder + ctx.fresh_vars_for_clause.get((c.p_from, c.p_to), [])
                cmds.append(make_forall(quant, body))

            # post condition
            if ctx.exit is not None:
                exit_app = mk_pred_call(ctx.exit, full_binder)
                post_app = mk_pred_call(f"{name}_post", post_binder)
                cmds.append(make_forall(full_binder, Application("=>", [exit_app, post_app])))

        return cmds
