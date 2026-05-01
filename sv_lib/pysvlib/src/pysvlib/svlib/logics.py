# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0


class SmtLibLogics:
    def __init__(self, logic: str):
        self._core_functions = {"true", "false", "not", "=>", "and", "or", "xor", "ite", "=", "distinct", "_"}

        self._int_functions = {"+", "-", "*", "div", "mod", "<", "<=", ">", ">="}
        self._int_sorts = {"Int"}
        self._int_logics = {
            "LIA",
            "NIA",
            "QF_LIA",
            "QF_NIA",
            "AUFLIA",
            "AUFNIRA",
            "UFNIA",
            "QF_ALIA",
            "ALL",
        }

        self._real_functions = {"+", "-", "*", "/", "<", "<=", ">", ">="}
        self._real_sorts = {"Real"}
        self._real_logics = {
            "LRA",
            "QF_LRA",
            "QF_NRA",
            "AUFLIRA",
            "AUFNIRA",
            "UFLRA",
            "ALL",
        }

        self._array_functions = {"select", "store"}
        self._array_logics = {
            "QF_AX",
            "QF_ABV",
            "QF_AUFBV",
            "QF_ALIA",
            "AUFLIA",
            "AUFLIRA",
            "AUFNIRA",
            "ALL",
        }

        self._bv_functions = {
            "bvadd",
            "bvsub",
            "bvmul",
            "bvurem",
            "bvudiv",
            "bvand",
            "bvor",
            "bvxor",
            "bvnot",
            "bvneg",
            "bvshl",
            "bvlshr",
            "bvashr",
            "concat",
            "extract",
            "bvult",
            "bvule",
            "bvugt",
            "bvuge",
            "bvslt",
            "bvsle",
            "bvsgt",
            "bvsge",
        }
        self._bv_logics = {"QF_BV", "QF_ABV", "QF_UFBV", "QF_AUFBV", "ALL"}

        self._core_sorts = {"Bool", "String"}

        self._available_functions = self._core_functions
        self._available_sorts = self._core_sorts

        if logic in self._int_logics:
            self._available_functions |= self._int_functions
            self._available_sorts |= self._int_sorts
        if logic in self._real_logics:
            self._available_functions |= self._real_functions
            self._available_sorts |= self._real_sorts
        if logic in self._array_logics:
            self._available_functions |= self._array_functions
        if logic in self._bv_logics:
            self._available_functions |= self._bv_functions

    @property
    def available_functions(self):
        return self._available_functions.copy()

    @property
    def available_sorts(self):
        return self._available_sorts.copy()

    def logic_exists(self, logic: str) -> bool:
        return logic in self._bv_logics.union(self._real_logics).union(self._array_logics).union(self._int_logics)
