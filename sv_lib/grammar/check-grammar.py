#!/usr/bin/env python3

# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener


# -----------------------------------------------------------------------------
# Custom error listener
# -----------------------------------------------------------------------------
class ParseErrorListener(ErrorListener):
    def __init__(self) -> None:
        super().__init__()
        self.errors: List[str] = []

    def syntaxError(
        self, recognizer, offendingSymbol, line: int, column: int, msg: str, e
    ) -> None:
        self.errors.append(f"line {line}:{column} {msg}")


# -----------------------------------------------------------------------------
# Build the argument parser
# -----------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate SV-LIB files using ANTLR grammar."
    )
    parser.add_argument("directory", help="Directory containing SV-LIB files")
    parser.add_argument(
        "--grammar", default="SvLib.g4", help="ANTLR grammar file (default: SvLib.g4)"
    )
    parser.add_argument(
        "--antlr", default="antlr4", help="ANTLR command (default: antlr4)"
    )
    parser.add_argument(
        "--force-regen",
        action="store_true",
        help="Force regeneration of ANTLR parser, ignoring timestamps",
    )
    return parser


# -----------------------------------------------------------------------------
# Determine whether regeneration is required
# -----------------------------------------------------------------------------
def grammar_needs_regeneration(grammar_file: Path) -> bool:
    generated_files: List[str] = ["SvLibLexer.py", "SvLibParser.py"]

    # Only one level of imports is handled here, should be fine for now
    all_grammars = [grammar_file]
    for line in grammar_file.read_text().splitlines():
        line = line.strip()
        if line.startswith("import "):
            imported_file = line.strip().split()[1].split(";")[0]
            all_grammars.append(grammar_file.parent / (imported_file + ".g4"))

    # Check if all grammars exist
    for file in all_grammars:
        if not os.path.exists(file):
            print(f"ERROR: Imported grammar file '{file}' not found.")
            sys.exit(1)

    grammar_mtime: float = max(os.path.getmtime(file) for file in all_grammars)

    for file in generated_files:
        if not os.path.exists(file):
            return True
        if os.path.getmtime(file) < grammar_mtime:
            return True

    return False


# -----------------------------------------------------------------------------
# Generate ANTLR parser
# -----------------------------------------------------------------------------
def generate_parser(grammar_file: Path, antlr_cmd: str, force_regen: bool) -> None:
    if not os.path.exists(grammar_file):
        print(f"ERROR: Grammar file '{grammar_file}' not found.")
        sys.exit(1)

    must_regen: bool = force_regen or grammar_needs_regeneration(grammar_file)

    if must_regen:
        if force_regen:
            print("Forcing regeneration (--force-regen).")
        else:
            print("Grammar newer than generated parser → regenerating…")

        antlr_command = [antlr_cmd, "-Dlanguage=Python3", str(grammar_file)]
        try:
            subprocess.check_call(antlr_command)
        except FileNotFoundError:
            print(f"ERROR: ANTLR command '{antlr_cmd}' not found.")
            sys.exit(1)
        except subprocess.CalledProcessError:
            print("ERROR: ANTLR parser generation failed.")
            sys.exit(1)
    else:
        print("ANTLR parser is up-to-date.\n")

    # Validate imports after regeneration
    try:
        import SvLibLexer  # noqa: F401
        import SvLibParser  # noqa: F401
    except ImportError:
        print("ERROR: Failed to import generated parser files.")
        sys.exit(1)


# -----------------------------------------------------------------------------
# Parse a single file using entry rule "script"
# -----------------------------------------------------------------------------
def parse_file(path: str) -> List[str]:
    from SvLibLexer import SvLibLexer
    from SvLibParser import SvLibParser

    lexer = SvLibLexer(FileStream(path, encoding="utf-8"))
    tokens = CommonTokenStream(lexer)
    parser = SvLibParser(tokens)

    listener = ParseErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    if path.endswith("witness.svlib"):
        parser.witnessFile()
    else:
        parser.script()
    return listener.errors


# -----------------------------------------------------------------------------
# Check all files in directory
# -----------------------------------------------------------------------------
def check_files(directory: str) -> bool:
    print(f"Checking files in: {directory}\n")
    failed: bool = False

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".svlib"):
                path: str = os.path.join(root, filename)
                errors: List[str] = parse_file(path)

                if errors:
                    failed = True
                    print(f"❌ {path}")
                    for err in errors:
                        print(f"   {err}")
                else:
                    print(f"✔ {path}")

    print()
    return failed


# -----------------------------------------------------------------------------
# Main dispatcher
# -----------------------------------------------------------------------------
def main() -> None:
    args = build_arg_parser().parse_args()

    # Call functions with only the data they need
    generate_parser(
        grammar_file=Path(args.grammar).absolute(),
        antlr_cmd=args.antlr,
        force_regen=args.force_regen,
    )

    had_errors: bool = check_files(directory=args.directory)

    if had_errors:
        print("❌ Some files did not parse correctly.")
        sys.exit(1)

    print("✔ All files parsed successfully.")
    sys.exit(0)


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
