<!--
This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
https://gitlab.com/sosy-lab/benchmarking/sv-lib

SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers

SPDX-License-Identifier: Apache-2.0
-->

# Developing

## Logging

In order to avoid polluting external loggers
with log messages from SvLibChecker, we use a dedicated logger for all log messages
from PySvLib, which is named `pysvlib`.
This allows users of PySvLib to configure the logging behavior for PySvLib separately
from other loggers, e.g., by setting the logging level or by adding handlers to the `pysvlib` logger.

Therefore, instead of calling `logging....` use `get_logger()....`
which will call the logging functions on the `pysvlib` logger.