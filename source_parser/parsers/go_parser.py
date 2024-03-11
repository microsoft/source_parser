# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
java_parser.py

This is the class which uses tree_sitter to parse Go files
into structural components defined by the source_parser schema,
the code is incomplete and is included as a placeholder.
"""

from typing import List, Dict, Any

from source_parser.parsers.language_parser import (
    LanguageParser,
)


def match_from_span(node, blob: str) -> str:
    start = node.startIndex
    end = node.endIndex
    return blob[start:end]


class GoParser(LanguageParser):

    FILTER_PATHS = ("test", "vendor")

    @staticmethod
    def get_definition(tree, blob: str) -> List[Dict[str, Any]]:
        definitions = []
        comment_buffer = []
        for child in tree.root_node.children:
            if child.type == "comment":
                comment_buffer.append(child)
            elif child.type in ("method_declaration", "function_declaration"):
                docstring = "\n".join(
                    [match_from_span(comment, blob) for comment in comment_buffer]
                )

                metadata = GoParser.get_function_metadata(child, blob)
                definitions.append(
                    {
                        "type": child.type,
                        "identifier": metadata["identifier"],
                        "parameters": metadata["parameters"],
                        "function": match_from_span(child, blob),
                        "docstring": docstring,
                        "start_point": child.start_point,
                        "end_point": child.end_point,
                    }
                )
                comment_buffer = []
            else:
                comment_buffer = []
        return definitions

    @staticmethod
    def get_function_metadata(function_node, blob: str) -> Dict[str, str]:
        metadata = {
            "identifier": "",
            "parameters": "",
        }
        if function_node.type == "function_declaration":
            metadata["identifier"] = match_from_span(function_node.children[1], blob)
            metadata["parameters"] = match_from_span(function_node.children[2], blob)
        elif function_node.type == "method_declaration":
            metadata["identifier"] = match_from_span(function_node.children[2], blob)
            metadata["parameters"] = " ".join(
                [
                    match_from_span(function_node.children[1], blob),
                    match_from_span(function_node.children[3], blob),
                ]
            )
        return metadata
