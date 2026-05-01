# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pysvlib.svlib.static_analysis.data import StaticAnalysisError


class LinterError(StaticAnalysisError):
    """Base class for all linter errors."""

    def __init__(self, message: str):
        self.message = message

    def report(self) -> str:
        # TODO: This should be improved
        return self.message

    def __str__(self) -> str:
        return self.message


class DuplicateVariableError(LinterError):
    """Raised when a variable is declared more than once."""

    def __init__(self, var_name):
        super().__init__(f"Duplicate variable declaration: {var_name}")
        self.var_name = var_name


class UnknownCommandError(LinterError):
    """Raised when an unknown AST command is encountered."""

    def __init__(self, command):
        super().__init__(f"Unknown command: {command}")
        self.command = command


class InvalidSortError(LinterError):
    """Raised when a variable has an invalid or unsupported sort/type."""

    def __init__(self, sort):
        super().__init__(f"Invalid sort: {sort}")
        self.sort = sort


class SortIsNoneError(LinterError):
    """Raised when a variable is declared without a sort in SV-LIB."""

    def __init__(self, var_name: str):
        super().__init__(f"Variable '{var_name}' declared without a sort")
        self.var_name = var_name


class InvalidVariableNameError(LinterError):
    """Raised when a variable name is not a valid string or is empty."""

    def __init__(self, name):
        super().__init__(f"Invalid variable name: {repr(name)}. Must be a non-empty string.")
        self.name = name


class InvalidSortNameError(LinterError):
    """Raised when a sort name is invalid (empty, None, or not a string)."""

    def __init__(self, name):
        super().__init__(f"Invalid sort name: {name}")
        self.name = name


class DuplicateDeclaredSortError(LinterError):
    """Raised when a sort with the same name has already been declared."""

    def __init__(self, sort):
        self.sort = sort
        name = getattr(sort, "name", repr(sort))
        super().__init__(f"Sort {name} has already been declared.")


class SortArityMismatchError(LinterError):
    """Raised when a sort is used with a different number of arguments than declared."""

    def __init__(self, name: str, expected: int, actual: int):
        self.name = name
        self.expected = expected
        self.actual = actual
        super().__init__(f"Sort '{name}' expected {expected} argument(s), got {actual}.")


class InvalidFunNameError(LinterError):
    """Raised when a function name is invalid (empty, None, or not a string)."""

    def __init__(self, name):
        super().__init__(f"Invalid function name: {name}")
        self.name = name


class InvalidProcNameError(LinterError):
    """Raised when a function name is invalid (empty, None, or not a string)."""

    def __init__(self, name):
        super().__init__(f"Invalid proc name: {name}")
        self.name = name


class DuplicateFunNameError(LinterError):
    """Raised when a function with the same name has already been declared."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Function '{name}' has already been declared.")


class DuplicateFunArgumentsNameError(LinterError):
    """Raised when a function has duplicate argument names."""

    def __init__(self, name, var_name):
        self.name = name
        super().__init__(f"Function '{name}' has duplicate argument names: {var_name}")


class UndefinedFunctionError(LinterError):
    """Raised when trying to apply/call a function that hasn't been declared or defined."""

    def __init__(self, function_name, available_functions):
        self.function_name = function_name
        super().__init__(
            f"Function '{function_name}' is not declared or defined. Available functions: {available_functions}"
        )


class FunctionArityMismatchError(LinterError):
    """Raised when function application has wrong number of arguments."""

    def __init__(self, function_name, expected, actual):
        self.function_name = function_name
        self.expected = expected
        self.actual = actual
        super().__init__(f"Function '{function_name}' expects {expected} arguments, got {actual}.")


class LogicNotFoundError(LinterError):
    """Raised when a logic is not found or unsupported in SV-LIB."""

    def __init__(self, logic_name: str):
        self.logic_name = logic_name
        super().__init__(f"Logic not found: {logic_name}")


class UndefinedVariableError(LinterError):
    """Raised when referencing a variable that has not been declared."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Variable '{name}' has not been declared.")


class InvalidLogicNameError(LinterError):
    """Raised when a logic name is invalid."""

    def __init__(self, name: str):
        super().__init__(f"Invalid logic name: {name}")
        self.name = name


class InvalidTypeError(LinterError):
    """Raised when an object has an invalid type."""

    def __init__(self, actual_type: str, context: str = ""):
        self.actual_type = actual_type
        self.context = context
        msg = f"Invalid type: {actual_type}"
        if context:
            msg += f" in {context}"
        super().__init__(msg)


class InvalidArgumentTypeError(LinterError):
    """Raised when a function argument has an invalid type."""

    def __init__(self, fun_name: str, expected: str, actual_type: str):
        self.fun_name = fun_name
        self.expected = expected
        self.actual_type = actual_type
        super().__init__(f"Function '{fun_name}' has invalid argument type: expected {expected}, got {actual_type}")


class ParserError(LinterError):
    """Raised when the parser crashes/fails completely."""

    def __init__(self, message="Parser Error"):
        super().__init__(message)


class LinterException(Exception):
    """Raised when linting finds one or more errors."""

    def __init__(self, errors):
        self.errors = errors
        if not isinstance(errors, list):
            super().__init__(errors)
            return

        super().__init__(
            f"Linting found {len(errors)} error(s):\n"
            + "\n".join(f"  {i + 1}. {error}" for i, error in enumerate(errors))
        )
