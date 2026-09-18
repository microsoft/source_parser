# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from source_parser.parsers.java_parser import JavaParser
from source_parser.parsers.language_parser import has_correct_syntax


def test_syntax_fail():
    # Code has a missing parenthesis
    # This code is syntactically incorrect, but tree-sitter marks the missing parenthesis as MISSING
    # Previous version of source-parser misses this error

    code = "class Dummy { public void test ( { } }"
    jp = JavaParser(code)
    class_dict_list = [
        jp._parse_class_node(class_node) for class_node in jp.class_nodes
    ]

    # print(class_dict_list)
    assert class_dict_list[0]['syntax_pass'] is False


def test_syntax_pass():

    code = "class Dummy { public void test ( ) { } }"
    jp = JavaParser(code)
    class_dict_list = [
        jp._parse_class_node(class_node) for class_node in jp.class_nodes
    ]

    # print(class_dict_list)
    assert class_dict_list[0]['syntax_pass'] is True


def test_missing_node_is_incorrect_syntax():
    parser = JavaParser("class Dummy { public void test ( { } }")
    nodes = [parser.tree.root_node]
    missing = []
    while nodes:
        node = nodes.pop()
        if node.is_missing:
            missing.append(node)
        nodes.extend(node.children)

    assert missing
    assert all(not has_correct_syntax(node) for node in missing)


if __name__ == "__main__":
    test_syntax_fail()
    test_syntax_pass()
