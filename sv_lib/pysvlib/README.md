<!--
This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
https://gitlab.com/sosy-lab/benchmarking/sv-lib

SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers

SPDX-License-Identifier: Apache-2.0
-->

# PySV-LIB

## Program Translations

### From LLVM to SV-LIB

The translation uses `llvmlite` (https://pypi.org/project/llvmlite/) to parse `.ll` files.
Currently only LLVM versions `20.x.x` are compatible.

### From Btor2 to SV-LIB

The translation uses an ANTLR4 grammar to parse `.btor2` files and translate them to SV-LIB.
ANTLR should be installed and runnable as `antlr4` (if the cli command is `antlr` on your system you can change the run
command in the file `antlr_utils.py`).

Example usage:

```bash
pysvlib btor2_to_svlib src/pysvlib/translators/btor2/test-examples-dir/large-test-examples/ --output-dir src/pysvlib/translators/btor2/translation-output/
```

## Developing

We use ANTLR for some transformations of languages to and from SV-LIB.
Therefore, for development you need to have ANTLR4 installed.
You can find instructions on how to install ANTLR4
on the [official ANTLR website](https://www.antlr.org/).

The easiest is to install it through your package manager,
e.g., on Ubuntu/Debian:

```bash
sudo apt-get install antlr4
```

The only important thing is that the command `antlr4` is available in your PATH
and can be called from a python subprocess using only `/bin/sh`.