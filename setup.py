# Copyright 2021 The Sphinx-Immaterial Authors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import setuptools

import atexit
import os
import subprocess
import tempfile

import setuptools.command.build_py
import setuptools.command.develop
import setuptools.command.install
import setuptools.command.sdist
from sphinx_immaterial.google_fonts import install_google_fonts

from importlib.resources import files
from sphinx_immaterial import resources

from sphinx_immaterial import DEFAULT_THEME_OPTIONS

root_dir = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.join(root_dir, "sphinx_immaterial")


def _setup_temp_egg_info(cmd):
    """Use a temporary directory for the `neuroglancer.egg-info` directory.

    When building an sdist (source distribution) or installing, locate the
    `sphinx_immaterial.egg-info` directory inside a temporary directory so that
    it doesn't litter the source directory and doesn't pick up a stale
    SOURCES.txt from a previous build.
    """
    egg_info_cmd = cmd.distribution.get_command_obj("egg_info")
    if egg_info_cmd.egg_base is None:
        tempdir = tempfile.TemporaryDirectory(dir=os.curdir)
        egg_info_cmd.egg_base = tempdir.name
        atexit.register(tempdir.cleanup)


class SdistCommand(setuptools.command.sdist.sdist):
    def run(self):
        _setup_temp_egg_info(self)
        self.run_command("static_bundles")
        super().run()

    def make_release_tree(self, base_dir, files):
        # Exclude .egg-info from source distribution.  These aren't actually
        # needed, and due to the use of the temporary directory in `run`, the
        # path isn't correct if it gets included.
        files = [x for x in files if ".egg-info" not in x]
        super().make_release_tree(base_dir, files)


class InstallCommand(setuptools.command.install.install):
    def run(self):
        _setup_temp_egg_info(self)
        self.run_command("static_bundles")
        super().run()


class BuildCommand(setuptools.command.build.build):
    def finalize_options(self):
        if self.build_base == "build":
            # Use temporary directory instead, to avoid littering the source directory
            # with a `build` sub-directory.
            tempdir = tempfile.TemporaryDirectory()
            self.build_base = tempdir.name
            atexit.register(tempdir.cleanup)
        super().finalize_options()

    def run(self):
        _setup_temp_egg_info(self)
        self.run_command("static_bundles")
        super().run()


class BuildPyCommand(setuptools.command.build_py.build_py):
    def run(self):
        self.run_command("static_bundles")
        super().run()


class DevelopCommand(setuptools.command.develop.develop):
    def run(self):
        self.run_command("static_bundles")
        super().run()


class StaticBundlesCommand(
    setuptools.command.build.build, setuptools.command.build.SubCommand
):
    editable_mode: bool = False

    user_options = setuptools.command.build_py.build_py.user_options + [
        (
            "bundle-type=",
            None,
            'The bundle type. "min" (default) creates minified bundles,'
            ' "dev" creates non-minified files.',
        ),
        (
            "skip-npm-reinstall",
            None,
            "Skip running `npm install` if the `node_modules` directory already exists.",
        ),
        (
            "skip-rebuild",
            None,
            "Skip rebuilding if the `sphinx_immaterial/bundles` directory already exists.",
        ),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.bundle_type = "min"
        self.skip_npm_reinstall = None
        self.skip_rebuild = None

    def finalize_options(self):
        super().finalize_options()
        if self.bundle_type not in ["min", "dev"]:
            raise RuntimeError('bundle-type has to be one of "min" or "dev"')

        if self.skip_npm_reinstall is None:
            self.skip_npm_reinstall = False

        if self.skip_rebuild is None:
            self.skip_rebuild = False

    def run(self):
        if self.skip_rebuild:
            output_dir = os.path.join(package_root, "bundles")
            if os.path.exists(output_dir):
                print(
                    "Skipping rebuild of package since %s already exists"
                    % (output_dir,)
                )
                return

        target = {"min": "build", "dev": "build:dev"}

        try:
            install_google_fonts(
                files(resources),
                files(resources),
                DEFAULT_THEME_OPTIONS["font"].values(),
            )
            tgt = target[self.bundle_type]
            node_modules_path = os.path.join(root_dir, "node_modules")
            if self.skip_npm_reinstall and os.path.exists(node_modules_path):
                print(
                    "Skipping `npm install` since %s already exists"
                    % (node_modules_path,)
                )
            else:
                subprocess.call("npm i", shell=True, cwd=root_dir)
            res = subprocess.call(f"npm run {tgt}", shell=True, cwd=root_dir)
        except:  # noqa: E722
            raise RuntimeError("Could not run 'npm run %s'." % tgt)

        if res:
            raise RuntimeError("failed to build sphinx-immaterial package.")


setuptools.setup(
    cmdclass=dict(
        sdist=SdistCommand,
        build=BuildCommand,
        build_py=BuildPyCommand,
        install=InstallCommand,
        static_bundles=StaticBundlesCommand,
        develop=DevelopCommand,
    ),
)
