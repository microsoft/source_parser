# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
config.py

This module checks for tree-sitter grammar shared objects and
compiles them if they do not exist. The compiled shared objects
for each language are stored in `$HOME/.cache/source-parser/`

To add more language gramma support, simply add the git submodules
corresponding to the desired grammars. For example, to add `bash`
parsing support, invoke

`git submodule add https://github.com/tree-sitter/tree-sitter-bash.git
    assets/tree_sitter/tree-sitter-bash`


usage:

>>> from source_parser.tree_sitter.config import get_language, LanguageId
>>> print(f'Currently supported langs: {list(LanguageId)}')
>>> py_lang = get_language('python')
"""
# pylint: disable=logging-fstring-interpolation
import logging
import re
from enum import Enum
from pathlib import Path
from shutil import rmtree
from threading import Lock
from typing import Union
from tree_sitter import Language

DATADIR = Path(__file__).parent / "assets"
LANGS = ["-".join(repo.name.split("-")[2:]) for repo in DATADIR.iterdir()]
LANGDIR = Path.home() / ".cache" / "source_parser"
RE_TSLANG = re.compile(r"^extern const TSLanguage \*(\w+)\(void\).*")

# This can be used as `LanguageId.CPP`, `LanguageId.TYPESCRIPT`, etc.
# The keys and values can be retrieved as `LanguageId.C.name` and `Language.C.value`, respectively
# Keys are language names, capitalized, without punctuation
# Values are the same as LANGS
LanguageId = Enum(
    "LanguageId",
    {lang.replace("-", "").upper(): lang.replace("-", "") for lang in LANGS},
)
PARSER_RELATIVE_PATH = (
    {  # typescript has two grammars (one extra for tsx), so we select one
        lang: (
            "src/parser.c" if lang.value != "typescript" else "typescript/src/parser.c"
        )
        for lang in LanguageId
    }
)
PARSER_SYMBOL_NAMES = (
    {  # csharp reponame and parser.c symbol name differ from other language conventions
        lang: (
            f"tree_sitter_{lang.value}"
            if lang.value != "csharp"
            else "tree_sitter_c_sharp"
        )
        for lang in LanguageId
    }
)

LOGGER = logging.getLogger(__name__)

# Create a lock instance
build_library_lock = Lock()


def build_library(language: LanguageId, force_build=False):
    """
    Look for the tree sitter parser shared objects in `LANGDIR`, which
    should have a
        '$HOME/.cache/source-parser/tree-sitter-<lang>.so'
    for each grammar subdirectory in located in
        `../assets/tree-sitter/tree-sitter-<lang>`
    If `LANGDIR` does not exist, build it and save it in that location.

    Parameters
    ----------
    language : LanguageId
        Language ID for language
    force_build : True/False
        force the system to re-build even if the parsers exist
    """
    if not LANGDIR.parent.exists():
        LANGDIR.mkdir(parents=True)
        LOGGER.info(f"Created directory {LANGDIR} for parsers")

    reponame = f"tree-sitter-{language.value}"

    src_dir = (DATADIR / reponame / PARSER_RELATIVE_PATH[language]).parent.parent
    langlib = LANGDIR / f"{reponame}.so"

    if src_dir:
        if not langlib.exists() or force_build:
            with build_library_lock:
                LOGGER.info(f"Building language shared object {langlib}")
                Language.build_library(str(langlib), [src_dir])
                LOGGER.info(f"Saved language shared object {langlib}")
        else:
            LOGGER.info(f"Found language shared object {langlib}")

    else:
        LOGGER.warning(
            'Could not find "parser.c" within language ' f"parser in {langlib}"
        )


def get_language(language: Union[LanguageId, str], force_build=False) -> Language:
    """
    Get tree-sitter Language object for `language`

    Parameters
    ----------

    language : Union[LanguageId, str]
        unique language string or Language ID for language
    force_build : True/False
        force the system to re-build even if the parsers exist

    Returns
    -------
    tree_sitter_language : tree_sitter.Language
    """
    if isinstance(language, str):
        language = LanguageId(language)
    build_library(language, force_build=force_build)

    reponame = f"tree-sitter-{language.value}"
    langlib = LANGDIR / f"{reponame}.so"
    name = PARSER_SYMBOL_NAMES[language]
    try:
        return Language(str(langlib), "_".join(name.split("_")[2:]))
    except ValueError as v_err:
        LOGGER.warning(v_err)
        cache_dir = Path(langlib).parent
        LOGGER.warning(
            f"Deleting cache {cache_dir} and re-trying to build and load tree-sitter Language"
        )
        rmtree(cache_dir)
        build_library(language, force_build=True)
        return Language(str(langlib), name)
