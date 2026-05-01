# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from hatchling.builders.plugin.interface import BuilderInterface


class BuildSvCompArchive(BuilderInterface):
    PLUGIN_NAME = "custom"

    def get_version_api(self):
        # API version used by Hatch
        return {"svcomp": self.build_svcomp_archive}

    def create_wheel_archive(self, output_path: Path):
        from hatchling.builders.wheel import WheelBuilder

        output_path.mkdir(parents=True, exist_ok=True)
        # Taken by executing `hatch build -t wheel`
        # using a custom hook to take a look at the build data
        wheel_builder = WheelBuilder(
            root=self.root,
            plugin_manager=self.plugin_manager,
            config=self.config,
            metadata=self.metadata,
            app=self.app,
        )
        wheel_built_data = {
            "infer_tag": False,
            "pure_python": True,
            "dependencies": [],
            "force_include_editable": {},
            "extra_metadata": {},
            "shared_data": {},
            "shared_scripts": {},
            "artifacts": [],
            "force_include": {},
            "sbom_files": [],
            "build_hooks": ("custom",),
        }
        wheel_builder.build_standard(str(output_path), **wheel_built_data)

    @staticmethod
    def copy_dir_contents(src: Path, dst: Path) -> None:
        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)

    def add_z3_binary_for_svcomp27(self, archive_path: Path):
        # First adjust the solver path to the Z3 binary in the SV-COMP archive
        wheel_file = next(archive_path.glob("*.whl"))
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["wheel", "unpack", str(wheel_file), "-d", tmpdir], check=True)
            unpacked_archive = next(Path(tmpdir).iterdir())

            # download Z3 binary
            pysvlib_archive_with_z3 = Path(tmpdir) / "pysvlib-z3"
            pysvlib_archive_with_z3_zip = pysvlib_archive_with_z3.with_suffix(".zip")
            urlretrieve(
                "https://zenodo.org/records/18366617/files/pysvlib-0.0.0+g03e294a-dev-py3-none-any.zip",
                filename=pysvlib_archive_with_z3_zip,
            )

            with zipfile.ZipFile(pysvlib_archive_with_z3_zip, "r") as zip_ref:
                zip_ref.extractall(pysvlib_archive_with_z3)

            # Copy all z3 files into the directory
            z3_files = list(pysvlib_archive_with_z3.rglob("z3*"))
            for z3_file in z3_files:
                new_file = wheel_file.parent / z3_file.name
                shutil.copy2(z3_file, new_file)
                st = os.stat(new_file)
                os.chmod(new_file, st.st_mode | stat.S_IEXEC)

            # Replace the call to Z3
            for file in unpacked_archive.rglob("*.py"):
                if "_cli" in file.name or "_test" in file.name:
                    continue

                with file.open("r") as f:
                    content = f.read()

                if '"z3"' in content:
                    content = "from pathlib import Path" + os.linesep + content
                    content = content.replace(
                        '["z3",',
                        # TODO: This is hard-coded
                        '[str(Path(__file__).parent.parent.parent.parent / "z3"), ',
                    )

                    with file.open("w") as f:
                        f.write(content)

            # Now repack the wheel with the new files
            os.remove(wheel_file)
            subprocess.run(
                ["wheel", "pack", str(unpacked_archive), "-d", str(wheel_file.parent)],
                check=True,
            )

        return

    def build_svcomp_archive(self, directory: str, **build_data: Any) -> str:
        archive_path = Path(directory) / "pysvlib-svcomp"
        archive_path.mkdir(parents=True, exist_ok=True)

        executables_path = archive_path / "pysvlib"

        # Build Wheel archive first
        self.create_wheel_archive(executables_path)

        # Now copy all required files into the archive
        svcomp_archive_path = Path(__file__).parent / "svcomp-archive-files"
        self.copy_dir_contents(svcomp_archive_path, archive_path)
        shutil.move(archive_path / "pysvlib_cli.py", executables_path / "pysvlib_cli.py")

        # TODO: Remove for SV-COMP 2027
        # Now copy Z3 into the archive to make it possible to run the tool
        # without installing it
        self.add_z3_binary_for_svcomp27(executables_path)

        # Now create the zip archive
        wheel_archive = next(executables_path.glob("*.whl"))
        version = wheel_archive.name.split("-")[1]
        archive_name = f"pysvlib-svcomp-{version}"
        final_archive = archive_path.parent / archive_name
        final_archive.mkdir(parents=True, exist_ok=True)
        shutil.move(archive_path, final_archive / archive_name)
        shutil.make_archive(final_archive, "zip", final_archive)
        shutil.rmtree(final_archive)

        return directory
