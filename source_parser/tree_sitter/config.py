# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Load bundled grammar capsules using the Tree-sitter 0.26 API.

Grammar snapshots are compiled when building the package, not at import time.
The manifest is shared with the package build so installed wheels expose the
same languages without depending on a source checkout or a writable cache.
"""

from enum import Enum
from functools import lru_cache
from importlib import import_module
from importlib.resources import files
import json
from typing import Union

from tree_sitter import Language


LANGS = list(json.loads(files(__package__).joinpath("grammars.json").read_text(encoding="utf-8")))
LanguageId = Enum("LanguageId", {language.upper(): language for language in LANGS})


@lru_cache(maxsize=None)
def _get_language(language: LanguageId) -> Language:
    binding = import_module(f"{__package__}._bindings.{language.value}")
    return Language(binding.language())


def get_language(language: Union[LanguageId, str]) -> Language:
    """Return a bundled language by its LanguageId or lowercase language name."""
    return _get_language(LanguageId(language))
