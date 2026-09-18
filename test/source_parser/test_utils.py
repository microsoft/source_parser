# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tree_sitter import Parser

from source_parser.tree_sitter.config import get_language
from source_parser.utils import tokenize


@pytest.mark.parametrize("whitespace", [True, False])
@pytest.mark.parametrize(
    "source,expected_tokens,expected_types",
    [
        ("", [], []),
        (" \n\t", [], []),
        (
            "def f(x):\n    return x + 1\n",
            ["def ", "f", "(", "x", ")", ":\n    ", "return ", "x ", "+ ", "1\n"],
            ["def", "identifier", "(", "identifier", ")", ":", "return", "identifier", "+", "integer"],
        ),
        (
            "value = call(1, nested(2, 3), 4)\nnext_value = 5\n",
            ["value ", "= ", "call", "(", "1", ", ", "nested", "(", "2", ", ", "3", ")", ", ", "4", ")\n",
             "next_value ", "= ", "5\n"],
            ["identifier", "=", "identifier", "(", "integer", ",", "identifier", "(", "integer", ",", "integer",
             ")", ",", "integer", ")", "identifier", "=", "integer"],
        ),
        (
            "caf\u00e9 = 'snowman: \u2603\\n'\n# comment\n",
            ["caf\u00e9 ", "= ", "'snowman: \u2603\\n'\n", "# comment\n"],
            ["identifier", "=", "string", "comment"],
        ),
    ],
)
def test_tokenize(source, expected_tokens, expected_types, whitespace):
    parser = Parser(get_language("python"))
    file_bytes = source.encode("utf-8")
    root = parser.parse(file_bytes).root_node

    tokens, types = tokenize(file_bytes, root, whitespace=whitespace)

    if not whitespace:
        expected_tokens = [token.rstrip() for token in expected_tokens]
    assert tokens == expected_tokens
    assert types == expected_types


@pytest.mark.parametrize("whitespace", [True, False])
def test_tokenize_subtree_preserves_indentation(whitespace):
    parser = Parser(get_language("python"))
    file_bytes = b"def f():\n    return 'ok'\n"
    root = parser.parse(file_bytes).root_node
    body = root.children[0].child_by_field_name("body")

    tokens, types = tokenize(file_bytes, body, whitespace=whitespace)

    expected = ["    return ", "'ok'\n"] if whitespace else ["    return", "'ok'"]
    assert tokens == expected
    assert types == ["return", "string"]


def test_tokenize_does_not_modify_tree_children():
    parser = Parser(get_language("python"))
    file_bytes = b"first = 1\nsecond = 2\n"
    root = parser.parse(file_bytes).root_node
    children = list(root.children)

    first_result = tokenize(file_bytes, root)

    assert root.children == children
    assert tokenize(file_bytes, root) == first_result


def test_tokenize_wide_tree_preserves_source_order():
    parser = Parser(get_language("python"))
    source = "".join(f"value_{index} = {index}\n" for index in range(2000))
    file_bytes = source.encode("utf-8")
    root = parser.parse(file_bytes).root_node

    tokens, types = tokenize(file_bytes, root, whitespace=False)

    expected_tokens = [
        token
        for index in range(2000)
        for token in (f"value_{index}", "=", str(index))
    ]
    assert tokens == expected_tokens
    assert types == ["identifier", "=", "integer"] * 2000
