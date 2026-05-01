# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from .llvm_opcode import LlvmOpCode
from .llvm_to_svlib_visitor import LlvmToSvLibVisitor
from .translator import LlvmToSvLibTranslator

visit_module = LlvmToSvLibVisitor.visit_module
translate = LlvmToSvLibTranslator.translate

__all__ = ["LlvmOpCode", "visit_module", "translate"]
