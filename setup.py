# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""
from io import open
from os import path
from setuptools import setup, find_packages

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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="tree_sitter universal-ast codesearchnet method-docstring",
    packages=find_packages(
        exclude=["source_parser/tree_sitter/assets", "test"]),
    python_requires=">=3.8",
    include_package_data=True,
    install_requires=[
        "autopep8>=1.4.4",
        "lz4>=3.1.0",
        "networkx>=2.5.1",
        "datasketch>=1.5.3",
        "tree-sitter>=0.20.1,<0.22",
        "ray>=1.0.0",
        "psutil>=5.6.3",
        "autopep8>=1.4.4",
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
