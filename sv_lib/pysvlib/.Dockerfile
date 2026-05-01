# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

FROM python:3.12-slim

# Install build dependencies
# Required packages:
# - gcc, z3, cvc5: for running the validator tests
# - git: for determining the current commit hash during build
# - ANTLR: for building parsers from grammar files to
#      do transformation from- and to- SV-LIB programs
# - unzip: for unpacking the SV-COMP archive for testing purposes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc z3 cvc5 git antlr4 unzip \
    && rm -rf /var/lib/apt/lists/*

# Install hatch
RUN python -m pip install hatch

# Create the working directory
RUN mkdir /app
WORKDIR /app

# Copy all files to the working directory
# in order to install the dependencies
COPY . .

# Install the dependecies of the pip package using hatch
# Since they do not change often, this speeds up rebuilds
#
# Current this is a workaround for hatch not supporting
# installing dependencies without also installing the package itself.
# See: https://github.com/pypa/hatch/issues/963
RUN hatch dep show requirements | xargs pip install

# Delete all source files to ensure that nothign
# is left after installing the dependencies
RUN rm -rf ./*

# Workaround for https://github.com/antlr/antlr4-tools/issues/22
RUN sed -i 's@https://central.sonatype.com/solrsearch/select?q=a:antlr4-master+g:org.antlr@https://search.maven.org/solrsearch/select?q=a:antlr4-master+g:org.antlr@g' /usr/local/lib/python3.12/site-packages/antlr4_tool_runner.py
