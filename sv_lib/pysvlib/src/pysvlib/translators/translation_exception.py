# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC


class TranslationException(Exception, ABC):
    """
    Abstract base for an exception that is raised when the translation of a program fails.
    """

    def __init__(self, message):
        super().__init__(message)
