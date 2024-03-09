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
    exec(version, main_ns)
    VERSTR = main_ns['__version__']

setup(
    name="source_parser",  # Required

    version=VERSTR,  # Required

    description="Parsers and tools for extracting method/class-level features from source code",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/microsoft/source_parser",  # Optional
    author="Microsoft Corporation",  # Optional
    author_email="vsdatascience@microsoft.com",  # Optional
    classifiers=[  # Optional
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="tree_sitter universal-ast codesearchnet method-docstring",  # Optional
    packages=find_packages(exclude=["source_parser/tree_sitter/assets", "test"]),  # Required
    python_requires=">=3.8",
    include_package_data=True,
    install_requires=[
        "autopep8>=1.4.4",
        "lz4>=3.1.0",
        "networkx>=2.5.1",
        "datasketch>=1.5.3",
        "tree-sitter>=0.20.1",
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
