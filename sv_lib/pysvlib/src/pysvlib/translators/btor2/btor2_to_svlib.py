# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from pysvlib.svlib.syntax import Command
from pysvlib.translators.antlr_utils import generate_parser_if_needed


def get_btor2_grammar_path() -> Path:
    return Path(__file__).absolute().parent / "Btor2.g4"


def btor2_antlr_generated_files_dir() -> Path:
    return Path(__file__).absolute().parent / "antlr"


def expected_btor2_generated_files() -> list[Path]:
    gen_dir = btor2_antlr_generated_files_dir()
    return [
        gen_dir / "Btor2Lexer.py",
        gen_dir / "Btor2Parser.py",
        gen_dir / "Btor2Visitor.py",
    ]


def btor2_to_svlib(btor2_task: str) -> tuple[Command]:
    generate_parser_if_needed(
        get_btor2_grammar_path(),
        expected_btor2_generated_files(),
        output_dir=btor2_antlr_generated_files_dir(),
    )

    from pysvlib.translators.btor2.btor2_to_command_visitor import Btor2ToCommandsVisitor

    ctx = _parse_and_return_file_ctx(btor2_task)
    btor2_to_command_visitor = Btor2ToCommandsVisitor()
    commands = btor2_to_command_visitor.visitBtor2_file(ctx)

    return commands


def _parse_and_return_file_ctx(btor2_task: str):
    generate_parser_if_needed(
        get_btor2_grammar_path(),
        expected_btor2_generated_files(),
        output_dir=btor2_antlr_generated_files_dir(),
    )

    from antlr4 import CommonTokenStream
    from antlr4.InputStream import InputStream

    from pysvlib.translators.btor2.antlr.Btor2Lexer import Btor2Lexer
    from pysvlib.translators.btor2.antlr.Btor2Parser import Btor2Parser

    input_stream = InputStream(btor2_task)
    lexer = Btor2Lexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = Btor2Parser(token_stream)
    tree = parser.btor2_file()

    if parser.getNumberOfSyntaxErrors() > 0:
        raise SyntaxError("BTOR2 input contains syntax errors")

    return tree
