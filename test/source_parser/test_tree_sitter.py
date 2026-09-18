# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import Counter

import pytest
from tree_sitter import LANGUAGE_VERSION, MIN_COMPATIBLE_LANGUAGE_VERSION, Parser

from source_parser.helpers import schematize_method
from source_parser.tree_sitter import LiteralCount, file_tokenizer, normalize
from source_parser.tree_sitter.config import LanguageId, _get_language, get_language


GRAMMAR_EXAMPLES = {
    "bash": "echo hello",
    "c": "int main(void) { return 0; }",
    "cpp": "class Example {};",
    "csharp": "class Example {}",
    "css": "p { color: red; }",
    "go": "package main\nfunc main() {}",
    "html": "<p>hello</p>",
    "java": "class Example {}",
    "javascript": "const value = 1;",
    "json": '{"value": 1}',
    "lua": "local value",
    "php": "<?php $value = 1;",
    "python": "value = 1",
    "regex": "ab+",
    "ruby": "value = 1",
    "rust": "fn main() {}",
    "typescript": "const value: number = 1;",
}


@pytest.mark.parametrize("language_id", list(LanguageId))
def test_bundled_grammar(language_id):
    language = get_language(language_id)
    assert get_language(language_id.value) is language
    assert MIN_COMPATIBLE_LANGUAGE_VERSION <= language.abi_version <= LANGUAGE_VERSION

    tree = Parser(language).parse(GRAMMAR_EXAMPLES[language_id.value].encode("utf-8"))

    assert not tree.root_node.has_error


def test_languages_do_not_require_a_home_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _get_language.cache_clear()
    for language_id in LanguageId:
        get_language(language_id)
    assert not list(tmp_path.iterdir())


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        get_language("not-a-language")


@pytest.mark.parametrize(
    "language,source",
    [
        (LanguageId.PYTHON, "value = 1\nmessage = 'hello'\nvalue += 2\n"),
        (LanguageId.JAVASCRIPT, "let value = 1;\nconst message = 'hello';\nvalue += 2;\n"),
    ],
)
def test_tokenization_and_normalization(language, source):
    tokens = file_tokenizer(source, language)
    assert "value" in tokens
    assert "1" in tokens
    assert "2" in tokens

    normalized = normalize(source, language)
    assert "<NUM_LIT>" in normalized
    assert "<STR_LIT>" in normalized
    assert "hello" not in normalized


def test_literal_counters_keep_their_own_language():
    python_counter = LiteralCount(LanguageId.PYTHON)
    javascript_counter = LiteralCount(LanguageId.JAVASCRIPT)
    source = "value = 1\nmessage = 'hello'\nvalue += 2\n"
    expected = {
        "num": Counter({"1": 1, "2": 1}),
        "str": Counter({"hello": 1}),
        "char": Counter(),
        "regex": Counter(),
    }

    assert python_counter.count_lits(source) == expected
    assert javascript_counter.count_lits("let value = 3;\nvalue += 3;\n")["num"] == Counter({"3": 2})
    assert python_counter.count_lits(source) == expected


def test_python_helpers_use_bundled_grammar():
    method = schematize_method("def example(value):\n    return value + 1\n")

    assert method["name"] == "example"
    assert method["syntax_pass"]
