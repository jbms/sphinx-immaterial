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
import distutils.command.build
import os
import pathlib
import subprocess
import tempfile

import setuptools.command.build_py
import setuptools.command.develop
import setuptools.command.install
import setuptools.command.sdist

with open("requirements.txt", encoding="utf-8") as reqs:
    REQUIREMENTS = [reqs.readlines()]

root_dir = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.join(root_dir, "sphinx_immaterial")

optional_requirements = pathlib.Path("requirements")


def read_optional_reqs(name: str):
    reqs = optional_requirements / name
    return reqs.read_text(encoding="utf-8").splitlines()


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


class BuildCommand(distutils.command.build.build):
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


class DevelopCommand(setuptools.command.develop.develop):
    def run(self):
        self.run_command("static_bundles")
        super().run()


class StaticBundlesCommand(setuptools.command.build_py.build_py):
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
    name="sphinx_immaterial",
    description="Adaptation of mkdocs-material theme for the Sphinx documentation system",
    long_description=pathlib.Path("README.rst").read_text(encoding="utf-8"),
    long_description_content_type="text/x-rst",
    author="Jeremy Maitin-Shepard",
    author_email="jeremy@jeremyms.com",
    url="https://github.com/jbms/sphinx-immaterial",
    packages=setuptools.find_packages(
        where=".", include=["sphinx_immaterial", "sphinx_immaterial.*"]
    ),
    package_dir={"sphinx_immaterial": "sphinx_immaterial"},
    package_data={
        "sphinx_immaterial": [
            ".icons/*/**",
            ".icons/*/*/**",
            "partials/*.html",
            "partials/*/*.html",
            "partials/*/*/*.html",
            "partials/*/*/*/*.html",
            "bundles/*/**",
            "LICENSE",
            "*.html",
            "custom_admonitions.css",
            "theme.conf",
        ],
        "sphinx_immaterial.apidoc.cpp.cppreference_data": ["*.xml"],
    },
    python_requires=">=3.9",
    install_requires=REQUIREMENTS,
    use_scm_version={
        # It would be nice to include the commit hash in the version, but that
        # can't be done in a PEP 440-compatible way.
        "version_scheme": "no-guess-dev",
        # Test PyPI does not support local versions.
        "local_scheme": "no-local-version",
        "fallback_version": "0.0.0",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Framework :: Sphinx :: Extension",
        "Framework :: Sphinx :: Theme",
        "Topic :: Documentation :: Sphinx",
    ],
    entry_points={
        "sphinx.html_themes": [
            "sphinx_immaterial = sphinx_immaterial",
        ]
    },
    setup_requires=[
        "setuptools_scm>=6.3.2",
    ],
    extras_require={
        k: read_optional_reqs(f"{k}.txt")
        for k in [
            "json",
            "jsonschema_validation",
            "clang-format",
            "keys",
            "cpp",
            "black",
        ]
    },
    cmdclass=dict(
        sdist=SdistCommand,
        build=BuildCommand,
        install=InstallCommand,
        static_bundles=StaticBundlesCommand,
        develop=DevelopCommand,
    ),
)
