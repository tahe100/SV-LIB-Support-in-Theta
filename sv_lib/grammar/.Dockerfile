# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/* \

# Create the working directory
RUN mkdir /app
WORKDIR /app

# Copy all files to the working directory
# in order to install the dependencies
COPY . .

# Install all the dependencies for running the tests
# and building the grammar
RUN pip install -r requirements.txt

# Workaround for https://github.com/antlr/antlr4-tools/issues/22
RUN sed -i 's@https://central.sonatype.com/solrsearch/select?q=a:antlr4-master+g:org.antlr@https://search.maven.org/solrsearch/select?q=a:antlr4-master+g:org.antlr@g' /usr/local/lib/python3.12/site-packages/antlr4_tool_runner.py

# Delete all source files to ensure that nothign
# is left after installing the dependencies
RUN rm -rf ./*