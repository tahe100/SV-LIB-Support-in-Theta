# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from abc import ABC
from dataclasses import dataclass


class Type(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")


class Term(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")

    def free_vars(self) -> set["Variable"]:
        raise NotImplementedError("Abstract base class")


class Statement(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")


class Command(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Annotated(Statement):
    inner: Term | Statement
    attributes: tuple[str | tuple[str, object], ...]
    scope: object
    resolve: object  # callable to resolve terms in this scope

    def __str__(self):
        return f"(! {str(self.inner)} {' '.join(str(attr) for attr in self.attributes)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Param(Type):
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class BitVec(Type):
    bits: int

    def __str__(self):
        return f"(BitVec {self.bits})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class FloatingPoint(Type):
    exponent: int
    significand: int

    def __str__(self):
        return f"(FloatingPoint {self.exponent} {self.significand})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Boolean(Type):
    pass

    def __str__(self):
        return "Bool"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Sort(Type):
    name: str
    args: tuple[Type, ...]

    def __str__(self):
        if self.args:
            args_str = " ".join(str(arg) for arg in self.args)
            return f"({self.name} {args_str})"
        else:
            return self.name

    @staticmethod
    def numeral_sort():
        """Part of the bitvector theory, cf. https://smt-lib.org/theories-Ints.shtml"""
        return Sort("numeral", tuple())


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Literal(Term):
    value: any
    sort: Type

    def free_vars(self) -> set["Variable"]:
        return set()

    def __str__(self):
        if isinstance(self.value, bool):
            return "true" if self.value else "false"

        return f"{self.value}"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Variable(Term):
    name: str
    procedure: str | None
    sort: Type

    def free_vars(self) -> set["Variable"]:
        return {self}

    def __str__(self):
        return f"{self.name}"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class At(Term):
    term: Term
    label: str

    def free_vars(self) -> set["Variable"]:
        return self.term.free_vars()

    def __str__(self):
        return f"(at {str(self.term)} {self.label})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Final(Term):
    term: Term

    def free_vars(self) -> set["Variable"]:
        return self.term.free_vars()

    def __str__(self):
        return f"(final {str(self.term)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Application(Term):
    fun: str
    args: tuple[Term, ...]

    def free_vars(self) -> set["Variable"]:
        free_vars = set()
        for arg in self.args:
            free_vars.update(arg.free_vars())
        return free_vars

    def __str__(self):
        args_str = " ".join(str(arg) for arg in self.args)
        return f"({self.fun} {args_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Binder(Term):
    quantifier: str
    bound: list[Variable]
    body: Term

    def free_vars(self) -> set["Variable"]:
        body_free_vars = self.body.free_vars()
        bound_vars = set(self.bound)
        return body_free_vars - bound_vars

    def __str__(self):
        bound_str = " ".join(f"({var.name} {str(var.sort)})" for var in self.bound)
        return f"({self.quantifier} ({bound_str}) {str(self.body)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Return(Statement):
    pass

    def __str__(self):
        return "(return)"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Break(Statement):
    pass

    def __str__(self):
        return "(break)"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Continue(Statement):
    pass

    def __str__(self):
        return "(continue)"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Assume(Statement):
    formula: Term

    def __str__(self):
        return f"(assume {str(self.formula)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Assign(Statement):
    pairs: tuple[tuple[Variable, Term], ...]

    def __str__(self):
        pairs_str = " ".join(f"({str(var)} {str(term)})" for var, term in self.pairs)
        return f"(assign {pairs_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Havoc(Statement):
    vars: tuple[Variable, ...]

    def __str__(self):
        vars_str = " ".join(str(var) for var in self.vars)
        return f"(havoc {vars_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Label(Statement):
    name: str

    def __str__(self):
        return f"(label {self.name})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Goto(Statement):
    name: str

    def __str__(self):
        return f"(goto {self.name})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Call(Statement):
    name: str
    inputs: tuple[Term, ...]
    outputs: tuple[Variable, ...]

    def __str__(self):
        inputs_str = " ".join(str(inp) for inp in self.inputs)
        outputs_str = " ".join(str(out) for out in self.outputs)
        return f"(call {self.name} ({inputs_str}) ({outputs_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class If(Statement):
    condition: Term
    iftrue: Statement
    iffalse: Statement

    def __str__(self):
        if isinstance(self.iffalse, Sequence) and len(self.iffalse.statements) == 0:
            return f"(if {str(self.condition)} {str(self.iftrue)})"
        else:
            return f"(if {str(self.condition)} {str(self.iftrue)} {str(self.iffalse)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class While(Statement):
    condition: Term
    body: Statement

    def __str__(self):
        return f"(while {str(self.condition)} {str(self.body)})"


def Skip():
    return Sequence(())


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Sequence(Statement):
    statements: tuple[Statement, ...]

    def __str__(self):
        statements_str = " ".join(str(stmt) for stmt in self.statements)
        return f"(sequence {statements_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Choice(Statement):
    statements: tuple[Statement, ...]

    def __str__(self):
        statements_str = " ".join(str(stmt) for stmt in self.statements)
        return f"(choice {statements_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Function:
    name: str
    arguments: tuple[Variable, ...]
    result: Type

    def __str__(self):
        args_str = " ".join(f"({arg.name} {str(arg.sort)})" for arg in self.arguments)
        return f"({self.name} ({args_str}) {str(self.result)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Procedure:
    name: str
    inputs: tuple[Variable, ...]
    outputs: tuple[Variable, ...]
    locals: tuple[Variable, ...]

    def __str__(self):
        inputs_str = " ".join(f"({inp.name} {str(inp.sort)})" for inp in self.inputs)
        outputs_str = " ".join(f"({out.name} {str(out.sort)})" for out in self.outputs)
        locals_str = " ".join(f"({loc.name} {str(loc.sort)})" for loc in self.locals)
        return f"({self.name} ({inputs_str}) ({outputs_str}) ({locals_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Constructor:
    fun: Function
    selectors: tuple[Function, ...]

    def __str__(self):
        selectors_str = " ".join(str(sel) for sel in self.selectors)
        return f"({str(self.fun)} ({selectors_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Datatype:
    constructors: tuple[Constructor, ...]

    def __str__(self):
        constructors_str = " ".join(str(cons) for cons in self.constructors)
        return f"({constructors_str})"


class Step(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class HavocStep(Step):
    update: tuple[object, ...]

    def __str__(self):
        update_str = " ".join(str(u) for u in self.update)
        return f"(havoc {update_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class InitProcVars(Step):
    proc_name: str
    update: tuple[object, ...]

    def __str__(self):
        update_str = " ".join(str(u) for u in self.update)
        return f"(init-proc-vars {self.proc_name} {update_str})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class ChoiceStep(Step):
    index: int

    def __str__(self):
        return f"(choice {self.index})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Leap(Step):
    tag: str
    update: tuple[object, ...]

    def __str__(self):
        update_str = " ".join(str(u) for u in self.update)
        return f"(leap {self.tag} {update_str})"


class Violation(ABC):  # noqa: B024
    def __init__(self):
        raise NotImplementedError("Abstract base class")


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Incorrect(Violation):
    tag: str
    attributes: tuple[object, ...]

    def __str__(self):
        return f"(incorrect-annotation {self.tag} {self.attributes})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Invalid(Violation):
    step: Step

    def __str__(self):
        return f"(invalid-step {self.step})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class SetLogic(Command):
    logic: str

    def __str__(self):
        return f"(set-logic {self.logic})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class GetAssertions(Command):
    pass

    def __str__(self):
        return "(get-assertions)"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class GetInfo(Command):
    keyword: str

    def __str__(self):
        return f"(get-info {self.keyword})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class SetInfo(Command):
    keyword: str
    argument: object

    def __str__(self):
        return f"(set-info {self.keyword} {self.argument})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class GetOption(Command):
    keyword: str

    def __str__(self):
        return f"(get-option {self.keyword})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class SetOption(Command):
    keyword: str
    argument: object

    def __str__(self):
        return f"(set-option {self.keyword} {self.argument})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Assert(Command):
    constraint: Term

    def __str__(self):
        return f"(assert {str(self.constraint)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DeclareSort(Command):
    sort: Sort

    def __str__(self):
        return f"(declare-sort {self.sort.name} {len(self.sort.args)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DefineSort(Command):
    sort: Sort
    body: Type

    def __str__(self):
        return f"(define-sort {self.sort.name} {self.sort.args} {str(self.body)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DeclareDatatypes(Command):
    sorts: tuple[Sort, ...]
    datatypes: tuple[Datatype, ...]

    def __str__(self):
        sorts_str = " ".join(str(s) for s in self.sorts)
        datatypes_str = " ".join(str(d) for d in self.datatypes)
        return f"(declare-datatypes ({sorts_str}) ({datatypes_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DeclareVar(Command):
    var: Variable

    def __str__(self):
        return f"(declare-var {self.var.name} {str(self.var.sort)})"


class DeclareConst(Command):
    var: Variable

    def __str__(self):
        return f"(declare-const {self.var.name} {str(self.var.sort)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DeclareFun(Command):
    fun: Function

    def __str__(self):
        args_str = " ".join(str(arg.sort) for arg in self.fun.arguments)
        return f"(declare-fun {self.fun.name} ({args_str}) {str(self.fun.result)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DefineFun(Command):
    fun: Function
    body: Term

    def __str__(self):
        args_str = " ".join(f"({arg.name} {str(arg.sort)})" for arg in self.fun.arguments)
        return f"(define-fun {self.fun.name} ({args_str}) {str(self.fun.result)} {str(self.body)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DefineFunsRec(Command):
    funs: tuple[Function, ...]
    bodies: tuple[Term, ...]

    def __str__(self):
        funs_str = " ".join(str(fun) for fun in self.funs)
        bodies_str = " ".join(str(body) for body in self.bodies)
        return f"(define-funs-rec ({funs_str}) ({bodies_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DefineProc(Command):
    proc: Procedure
    body: Statement

    def __str__(self):
        inputs_str = " ".join(f"({inp.name} {str(inp.sort)})" for inp in self.proc.inputs)
        outputs_str = " ".join(f"({out.name} {str(out.sort)})" for out in self.proc.outputs)
        locals_str = " ".join(f"({loc.name} {str(loc.sort)})" for loc in self.proc.locals)
        return f"(define-proc {self.proc.name} ({inputs_str}) ({outputs_str}) ({locals_str}) {str(self.body)})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class DefineProcsRec(Command):
    procs: tuple[Procedure, ...]
    bodies: tuple[Statement, ...]

    def __str__(self):
        procs_str = " ".join(str(proc) for proc in self.procs)
        bodies_str = " ".join(str(body) for body in self.bodies)
        return f"(define-procs-rec ({procs_str}) ({bodies_str}))"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class AnnotateTag(Command):
    tag: str
    attributes: tuple[object, ...]

    def __str__(self):
        return f"(annotate-tag {self.tag} {self.attributes})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class Trace:
    model: tuple[DefineFun, ...]
    globals: tuple[tuple[Variable, Term], ...]
    proc_name: str
    steps: tuple[Step, ...]
    violation: Violation
    using: tuple[object, ...]

    def __str__(self):
        model_str = " ".join(str(fun) for fun in self.model)
        globals_str = " ".join(f"({var.name} {str(term)})" for var, term in self.globals)
        steps_str = " ".join(str(step) for step in self.steps)
        using_str = " ".join(str(u) for u in self.using)
        return (
            f"(trace "
            f"(model {model_str}) "
            f"(globals {globals_str}) "
            f"(proc-name {self.proc_name}) "
            f"(steps {steps_str}) "
            f"(violation {str(self.violation)}) "
            f"(using {using_str})"
            f")"
        )


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class SelectTrace(Command):
    trace: Trace

    def __str__(self):
        return f"(select-trace {self.trace})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class VerifyCall(Command):
    name: str
    inputs: tuple[Term, ...]

    def __str__(self):
        return f"(verify-call {self.name} {self.inputs})"


@dataclass(frozen=True, eq=True, repr=True, unsafe_hash=True, slots=True)
class GetWitness(Command):
    pass

    def __str__(self):
        return "(get-witness)"
