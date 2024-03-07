# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""
from io import open
from os import path
import re
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

VERSIONFILE = path.join(HERE, "source_parser", "_version.py")
with open(VERSIONFILE, "rt", encoding="utf-8") as f:
    version = f.read()
    V_MATCH = re.match(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version
    )
if V_MATCH:
    VERSTR = V_MATCH.group(1)
else:
    raise RuntimeError(f"Unable to find version string in {VERSIONFILE}")


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
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="tree_sitter universal-ast codesearchnet method-docstring",  # Optional
    packages=find_packages(exclude=["contrib", "test"]),  # Required
    python_requires=">=3.6, <4",
    include_package_data=True,

    install_requires=[
        "autopep8>=1.4.4",
        "lz4>=3.1.0",
        "networkx>=2.5.1",
        "datasketch>=1.5.3"
    ],
)
