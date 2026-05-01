# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import traceback
from abc import ABC, abstractmethod
from pathlib import Path

from pysvlib.translators.data import TranslationResult
from pysvlib.translators.translation_exception import TranslationException
from pysvlib.utils.cli import PySvLibCLI
from pysvlib.utils.logging import get_logger


class TranslatorCLI(PySvLibCLI, ABC):
    """
    Abstract base class for translation specific CLI implementations.
    Should not be used directly, but only through one of its subclasses.
    Since they provide more features depending on the use-case.
    """

    NO_OVERWRITE_COMMAND: str = "--no-overwrite"

    @abstractmethod
    def command_help(self) -> str:
        raise NotImplementedError("Subclasses should implement this method to return the help message for the command")

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Return the file extension that is translated to.
        Example: '.svlib' (including '.') when translating from LLVM to SV-LIB.
        """
        raise NotImplementedError(
            "Subclasses should implement this method to return the file extension that is translated to."
        )

    @abstractmethod
    def add_translation_arguments(self, parser: argparse.ArgumentParser) -> None:
        raise NotImplementedError(
            "Subclasses should implement this method to add their specific translation arguments to the parser"
        )

    @abstractmethod
    def run_translation_saving_output(
        self, input_paths: list[Path], output_dir: Path, no_overwrite: bool, args: argparse.Namespace
    ) -> None:
        raise NotImplementedError("Subclasses should implement this method to run the translation")

    def add_subparser(self, current_parser: argparse._SubParsersAction) -> None:
        subparser = current_parser.add_parser(
            self.command_name(),
            help=self.command_help(),
        )
        # Add the common CLI for translation tasks, which means arbitrary
        # many files. Subclasses can then add additional arguments as needed.
        subparser.add_argument(
            "paths",
            nargs="+",
            type=lambda x: None if x is None else Path(x),
            help="Files or directories containing the programs to translate",
        )
        subparser.add_argument(
            "--output-dir",
            required=False,
            default=Path("output"),
            type=Path,
            help="Directory to store translation results.",
        )
        subparser.add_argument(
            TranslatorCLI.NO_OVERWRITE_COMMAND,
            action="store_true",
            help="Do not overwrite existing files when exporting translation results.",
        )

        self.add_translation_arguments(subparser)

    def run(self, args: argparse.Namespace) -> None:
        input_paths: list[Path] = args.paths

        output_dir: Path = args.output_dir
        no_overwrite: bool = args.no_overwrite

        # then perform more expensive translation
        get_logger().debug(f"Translating {input_paths}...")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            self.run_translation_saving_output(input_paths, output_dir, no_overwrite, args)
            get_logger().info(TranslationResult.Success.value)

        except Exception as exception:
            # when in --debug mode, actually raise the exception instead of logging
            debug: bool = args.debug
            if debug:
                raise exception

            get_logger().debug(traceback.format_exc())
            if isinstance(exception, TranslationException):
                # use .__class__.__name__ to see exactly which subclass is raised
                get_logger().error(
                    f"[{exception.__class__.__name__}] Translation failed for '{input_paths}': {exception}"
                )
            else:
                get_logger().critical(
                    f"Unexpected failure during translation of {input_paths}.\n{type(exception).__name__}\n{exception}"
                )
            get_logger().info(TranslationResult.Failure.value)

        return None


class ProjectTranslatorCLI(TranslatorCLI, ABC):
    """
    Abstract base class for implementing translators which take whole projects as inputs,
    for example LLVM, Python, Java, ...
    """

    @abstractmethod
    def run_translation(self, input_paths: list[Path], args: argparse.Namespace) -> str:
        raise NotImplementedError("Subclasses should implement this method to run the translation")

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Return the file extension that is translated to.
        Example: '.svlib' (including '.') when translating from LLVM to SV-LIB.
        """
        raise NotImplementedError(
            "Subclasses should implement this method to return the file extension that is translated to."
        )

    def run_translation_saving_output(
        self, input_paths: list[Path], output_dir: Path, no_overwrite: bool, args: argparse.Namespace
    ) -> None:
        output_path: Path = self.build_output_path(output_dir, self.get_file_extension())

        # first check if the path exists, and if overwrites are allowed
        if no_overwrite and os.path.exists(output_path):
            get_logger().warning(
                f"The file {str(output_path)} already exists, but {TranslatorCLI.NO_OVERWRITE_COMMAND} is specified."
            )
            get_logger().warning(f"Skipping translation for {str(input_paths)}.")
            return

        translated_program = self.run_translation(input_paths, args)
        self.export_translation(output_path, translated_program)
        get_logger().info(f"Translated {input_paths} to {str(output_path)}")

    @staticmethod
    def build_output_path(output_dir: Path, file_extension: str) -> Path:
        output_filename = f"translated-program{file_extension}"
        return output_dir / output_filename

    @staticmethod
    def export_translation(output_path: Path, translated_program: str):
        if os.path.exists(output_path):
            get_logger().warning(f"The file {str(output_path)} already exists and will be overwritten.")

        output_path.write_text(translated_program, encoding="utf-8")


class AllFilesStandaloneCLI(TranslatorCLI, ABC):
    """
    Abstract base class for translators which only take single files as input and not whole projects,
    so we do the translation for each file passed as input in the directory.

    This is usefull for translating for example BTor2 or MoXI.
    """

    @abstractmethod
    def run_translation(self, input_paths: Path, args: argparse.Namespace) -> str:
        raise NotImplementedError("Subclasses should implement this method to run the translation")

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Return the file extension that is translated to.
        Example: '.svlib' (including '.') when translating from BTor2 to SV-LIB.
        """
        raise NotImplementedError(
            "Subclasses should implement this method to return the file extension that is translated to."
        )

    @abstractmethod
    def valid_input_file_extensions(self) -> list[str]:
        """
        Return a list of file extensions that are valid for this translator.

        :return: A list of valid file extensions (including the dot, e.g., '.btor2').
        """
        raise NotImplementedError(
            "Subclasses should implement this method to return the file extension that is translated to."
        )

    def run_translation_saving_output(
        self, input_paths: list[Path], output_dir: Path, no_overwrite: bool, args: argparse.Namespace
    ) -> None:
        amount_translated_files = 0
        for input_path in input_paths:
            for file_extension in self.valid_input_file_extensions():
                all_files = input_path.rglob("*" + file_extension) if input_path.is_dir() else [input_path]
                for input_file in all_files:
                    output_file = Path(output_dir) / (
                        input_file.relative_to(input_path) if input_path.is_dir() else input_file.name
                    )
                    output_file = output_file.with_suffix(self.get_file_extension())
                    if output_file.exists() and no_overwrite:
                        get_logger().warning(f"The file {str(output_file)} already exists and will not be overwritten.")
                        continue

                    output_file.absolute().parent.mkdir(parents=True, exist_ok=True)

                    translated_program = self.run_translation(input_file, args)
                    output_file.write_text(translated_program, encoding="utf-8")
                    get_logger().debug(f"Translated {input_file} to {str(output_file)}")
                    amount_translated_files += 1

        get_logger().info(f"Translated {amount_translated_files} files to {str(output_dir)}")
