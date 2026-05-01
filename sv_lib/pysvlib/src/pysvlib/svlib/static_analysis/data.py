# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from enum import Enum


class StaticAnalysisError(ABC):
    """Base class for errors found by a static analysis."""

    @abstractmethod
    def report(self) -> str:
        """Return a human-readable error message."""
        raise NotImplementedError("Subclasses should implement this method to return a human-readable error message")


class StaticAnalysisResult(Enum):
    """Enum for the result of a static analysis."""

    Done = "done"
