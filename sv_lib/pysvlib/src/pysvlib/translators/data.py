# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from enum import Enum


class TranslationResult(Enum):
    """Enum for the result of a translation."""

    Failure = "Translation Failure"
    Success = "Translation Success"
