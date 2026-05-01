# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class AntlrBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        # Currently unnecessary, but will be required to build
        # ANTLR parsers from grammar files in the future.
        return super().initialize(version, build_data)
