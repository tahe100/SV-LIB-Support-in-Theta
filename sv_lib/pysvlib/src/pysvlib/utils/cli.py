# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import argparse
from abc import ABC, abstractmethod


class PySvLibCLI(ABC):
    @abstractmethod
    def command_name(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the name of the command")

    @abstractmethod
    def add_subparser(self, current_parser: argparse._SubParsersAction) -> None:
        raise NotImplementedError("Subclasses should implement this method to add their subparser to the main parser")

    @abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        raise NotImplementedError(
            "Subclasses should implement this method to run their command with the given arguments"
        )
