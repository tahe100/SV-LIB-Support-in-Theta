# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
from pathlib import Path
from typing import List


def grammar_needs_regeneration(grammar_file: Path, expected_generated_files: List[Path]) -> bool:
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
            raise FileNotFoundError(f"Imported grammar file '{file}' not found.")

    grammar_mtime: float = max(os.path.getmtime(file) for file in all_grammars)

    for file in expected_generated_files:
        if not file.exists():
            return True
        if os.path.getmtime(file) < grammar_mtime:
            return True

    return False


def generate_parser_if_needed(
    grammar_file: Path,
    expected_generated_files: List[Path],
    antlr_cmd: str = "antlr4",
    output_dir: Path = Path("."),
    force_regen: bool = False,
) -> None:
    if not os.path.exists(grammar_file):
        raise FileNotFoundError(f"Grammar file '{grammar_file}' not found.") from None

    must_regen: bool = force_regen or grammar_needs_regeneration(grammar_file, expected_generated_files)

    if must_regen:
        try:
            subprocess.run(
                [
                    antlr_cmd,
                    "-Dlanguage=Python3",
                    "-visitor",
                    "-o",
                    str(output_dir),
                    str(grammar_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError("ANTLR parser generation failed.") from None

    # Validate expected files exist after regeneration
    for file in expected_generated_files:
        if not file.exists():
            raise FileNotFoundError(f"Expected ANTLR generated file '{file}' not found.")
