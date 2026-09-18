# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""
from io import open
from copy import copy
import json
from os import path
from pathlib import Path
from shutil import copyfile
from setuptools import Extension, setup, find_packages
from setuptools.command.build_ext import build_ext

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

VERSIONFILE = path.join(HERE, "source_parser", "_version.py")
with open(VERSIONFILE, "rt", encoding="utf-8") as f:
    version = f.read()
    main_ns = {}
    # pylint: disable=exec-used
    exec(version, main_ns)
    # pylint: enable=exec-used
    VERSTR = main_ns['__version__']


def grammar_extensions():
    """Build each pinned grammar against its own generated parser headers."""
    grammar_dir = Path("source_parser") / "tree_sitter"
    with (grammar_dir / "grammars.json").open(encoding="utf-8") as manifest:
        grammars = json.load(manifest)

    extensions = []
    for language, symbol in grammars.items():
        source_dir = grammar_dir / "assets" / f"tree-sitter-{language}"
        if language == "typescript":
            source_dir /= "typescript"
        source_dir /= "src"
        parser_source = source_dir / "parser.c"
        if not parser_source.is_file():
            raise FileNotFoundError(
                f"Missing grammar source {parser_source}. "
                "Run 'git submodule update --init --recursive' before building."
            )
        sources = [grammar_dir / "binding.c", parser_source]
        sources.extend(sorted(source_dir.glob("scanner.*")))
        extensions.append(Extension(
            f"source_parser.tree_sitter._bindings.{language}",
            sources=[str(source) for source in sources],
            include_dirs=[str(source_dir)],
            define_macros=[
                ("Py_LIMITED_API", "0x030B0000"),
                ("LANGUAGE_MODULE", language),
                ("LANGUAGE_SYMBOL", symbol),
            ],
            py_limited_api=True,
        ))
    return extensions


class BuildGrammars(build_ext):
    """Keep macro-specific binding objects separate during parallel builds."""

    def build_extension(self, ext):
        ext = copy(ext)
        binding_source = Path(self.build_temp) / ext.name / "binding.c"
        binding_source.parent.mkdir(parents=True, exist_ok=True)
        copyfile(ext.sources[0], binding_source)
        ext.sources = [str(binding_source), *ext.sources[1:]]
        super().build_extension(ext)


setup(
    name="source_parser",

    version=VERSTR,

    description="Parsers and tools for extracting method/class-level features from source code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/microsoft/source_parser",
    author="Microsoft",
    author_email="vsdatascience@microsoft.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="tree_sitter universal-ast codesearchnet method-docstring",
    packages=find_packages(exclude=["test", "test.*"]),
    python_requires=">=3.11",
    include_package_data=False,
    package_data={
        "source_parser": ["languages.yml"],
        "source_parser.tree_sitter": ["grammars.json"],
    },
    license_files=["LICENSE", "source_parser/tree_sitter/assets/*/LICENSE*"],
    ext_modules=grammar_extensions(),
    cmdclass={"build_ext": BuildGrammars},
    options={"bdist_wheel": {"py_limited_api": "cp311"}},
    install_requires=[
        "autopep8>=1.4.4",
        "lz4>=3.1.0",
        "networkx>=2.5.1",
        "datasketch>=1.5.3,<2",
        "tree-sitter>=0.26,<0.27",
        "fissix>=24.4.24,<25",
        "ray>=1.0.0",
        "psutil>=5.6.3",
        "PyYAML>=6.0",
        "tqdm>=4.36.1",
        "columnize>=0.3.10"
    ],
    entry_points={
        'console_scripts': [
            'repo_parse = source_parser.cli.repo_parse:main',
            'repo_scrape = source_parser.cli.repo_scrape:main',
        ],
    },
)
