#!/usr/bin/env python3

# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import sys
from pathlib import Path

from pysvlib.translators.btor2.cli import Btor2ToSvLibCLI

sys.path.append(str(Path(__file__).absolute().parent.parent))

from pysvlib import __version__
from pysvlib.svlib.backend.chc.cli import ChcCli
from pysvlib.svlib.backend.validator.cli import ValidatorCLI
from pysvlib.svlib.static_analysis.formatter.cli import FormatterCli
from pysvlib.svlib.static_analysis.linter.cli import LinterCLI
from pysvlib.translators.llvm_to_svlib.cli import LlvmToSvLibCLI
from pysvlib.utils.cli import PySvLibCLI
from pysvlib.utils.logging import get_logger, setup_logging


def parse_args(argv: list[str], cli_classes: list[PySvLibCLI]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pysvlib", description="Command Line Tool for working with SV-LIB files")

    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging, which crashes on errors instead of reporting them",
    )

    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for cli_class in cli_classes:
        cli_class.add_subparser(subparsers)

    return parser.parse_args(argv)


def pysvlib(argv: list[str]) -> int:
    # TODO: we could also dynamically determine the subclasses
    cli_classes: list[PySvLibCLI] = [
        ChcCli(),
        ValidatorCLI(),
        FormatterCli(),
        LinterCLI(),
        LlvmToSvLibCLI(),
        Btor2ToSvLibCLI(),
    ]

    args = parse_args(argv, cli_classes)
    # do not make assumptions about arguments here,
    # as some tools could not have e.g. debug defined in their parser

    # Setup logging
    setup_logging(logging.getLevelName(args.log_level))

    get_logger().debug(
        "Starting PySvLib",
    )

    if args.profile:
        import cProfile

        pr = cProfile.Profile()
        pr.enable()

    for cli_class in cli_classes:
        if cli_class.command_name() == args.command:
            cli_class.run(args)

    if args.profile:
        pr.disable()
        pr.print_stats(sort="cumtime")

    return 0


def pysvlib_main() -> int:
    # In order to be able to test the command line tool, we separate the main function here.
    return pysvlib(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(pysvlib_main())
