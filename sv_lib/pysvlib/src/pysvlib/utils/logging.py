# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import logging


def setup_logging(log_level: int = logging.INFO):
    """
    Sets up the logging.
    :param log_level: Set the lowest log level to be displayed.
    """
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")


def get_logger() -> logging.Logger:
    """
    Returns the logger for PySvLib.

    :return: Logger instance.
    """
    return logging.getLogger("pysvlib")
