# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
language_parser.py

This module contains helper functions and the LanguageParser base class
which should be the basis of all language parsers. To use, you must implement
all the methods decorated with @abstractmethod. Follow the
`source_parsers.parsers.python_parser` for an example.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Union

from tree_sitter import Parser
from source_parser.tree_sitter.config import get_language, LanguageId

from source_parser.utils import strip_comments, static_hash


def traverse(node, results: List) -> None:
    """
    Recurse tree starting with node, collecting all nodes in results list
    """
    if node.type == "string":
        results.append(node)
        return
    for child in node.children:
        traverse(child, results)
    if not node.children:
        results.append(node)


def nodes_are_equal(n_1, n_2):
    """Tests not equivalence"""
    return (
        n_1.type == n_2.type
        and n_1.start_point == n_2.start_point
        and n_1.end_point == n_2.end_point
    )


def previous_sibling(node, parent_node):
    """
    Search for the previous sibling of the node.

    Returns the previous sibling node if it exists; otherwise, returns None.
    """
    if not parent_node:
        return None

    previous_sibling_index = -1
    for i, child in enumerate(parent_node.children):
        if child == node:
            previous_sibling_index = i - 1
            break
    if previous_sibling_index >= 0:
        return parent_node.children[previous_sibling_index]
    return None


def node_parent(tree, node):
    """Returns parent of node"""
    to_visit = [tree.root_node]
    while len(to_visit) > 0:
        next_node = to_visit.pop()
        for child in next_node.children:
            if nodes_are_equal(child, node):
                return next_node
            to_visit.extend(next_node.children)
    raise ValueError("Could not find node in tree.")


def traverse_type(node, results: List, type_set: Tuple[str]) -> None:
    """Traverse tree starting with node, collecting types in `type_set` in `results` list"""
    if isinstance(type_set, str):
        type_set = (type_set,)
    if node.type in type_set:
        results.append(node)
    if not node.children:
        return
    for child in node.children:
        traverse_type(child, results, type_set)


def has_correct_syntax(node):
    """
    Detect if tree has correct syntax

    Parameters
    ----------
    node : Node
        tree_sitter Node object corresponding to code
        which is being tested for syntax correctness

    Returns
    -------
    correct : True/False
        whether the node contains correct syntax
    """
    if "ERROR" in node.sexp() or "MISSING" in node.sexp():
        return False
    return True


def children_of_type(node, types: Union[str, Tuple]):
    """
    Return children of node of type belonging to types

    Parameters
    ----------
    node : tree_sitter.Node
        node whose children are to be searched
    types : str/tuple
        single or tuple of node types to filter

    Return
    ------
    result : list[Node]
        list of nodes of type in types
    """
    if isinstance(types, str):
        return children_of_type(node, (types,))
    return [child for child in node.children if child.type in types]


def children_not_of_type(node, types: Union[str, Tuple]):
    """
    Return children of node not of type belonging to types

    Parameters
    ----------
    node : tree_sitter.Node
        node whose children are to be searched
    types : str/tuple
        single or tuple of node types to filter

    Return
    ------
    result : list[Node]
        list of nodes not of type in types
    """
    if isinstance(types, str):
        return children_not_of_type(node, (types,))
    return [child for child in node.children if child.type not in types]


class LanguageParser(ABC):
    """
    LanguageParser abstract class. All language parsers
    should implement these methods indicated by @abstractmethod.
    """

    @classmethod
    @abstractmethod
    def get_lang(cls) -> str:
        """Language label string, e.g. 'python'"""

    @property
    @abstractmethod
    def method_types(self) -> Tuple[str]:
        """Tuple of method node type strings"""

    @property
    @abstractmethod
    def class_types(self) -> Tuple[str]:
        """Tuple of class node type strings"""

    @property
    @abstractmethod
    def import_types(self) -> Tuple[str]:
        """Tuple of import node type strings"""

    @property
    @abstractmethod
    def include_patterns(self) -> Union[Tuple[str], str]:
        """Glob pattern(s) of files to be handled by this parser"""

    @property
    def exclude_patterns(self) -> Union[Tuple[str], str]:
        """Glob pattern(s) of files to be ignored by this parser"""
        return (".?*",)

    @property
    @abstractmethod
    def file_docstring(self) -> str:
        """The first single or multi-line comment in the file"""

    @property
    @abstractmethod
    def file_context(self) -> List[str]:
        """List of global import and assignment statements"""

    @abstractmethod
    def _parse_method_node(self, method_node) -> Dict[str, Union[str, List, Dict]]:
        """Implement this method following `parse_method_node`"""

    @abstractmethod
    def _parse_class_node(self, class_node) -> Dict[str, Union[str, List, Dict]]:
        """Implement this method following `parse_class_node`"""

    def parse_method_node(self, method_node) -> Dict[str, Union[str, List, Dict]]:
        """
        Parse a method node into the correct schema

        Parameters
        ----------
        method_node : TreeSitter.Node
            tree_sitter node corresponding to a method


        Returns
        -------
        results : dict[str] = str, list, or dict
            parsed representation of the method corresponding to the following
            schema. See individual language implementations of `_parse_method_node`
            for guidance on language-specific entries.

            results = {
                'original_string': 'verbatim code of whole method',
                'signature':
                    'string corresponding to definition, name, arguments of method',
                'name': 'name of method',
                'docstring': 'verbatim docstring corresponding to this method',
                'body': 'verbatim code body',
                'byte_span': (start_byte, end_byte),
                'start_point': (start_line_number, start_column),
                'end_point': (end_line_number, end_column),
                'original_string_normed':
                    'code of whole method with string-literal, numeral normalization',
                'signature_normed': 'string-literals/numerals normalized signature',
                'body_normed': 'body with string-literals/numerals normalized',
                'default_arguments': ['arg1': 'default value 1', ...],
                'syntax_pass': 'whether the method is syntactically correct',
                'attributes': [
                        'language_specific_keys': 'language_specific_values',
                    ],
            }
        """
        msg = f"method_node is type {method_node.type}, requires types {self.method_types}"
        assert method_node.type in self.method_types, msg
        return self._parse_method_node(method_node)

    def parse_class_node(self, class_node) -> Dict[str, Union[str, List, Dict]]:
        """
        Parse a class node into the correct schema

        Parameters
        ----------
        class_node : TreeSitter.Node
            tree_sitter node corresponding to a class

        Returns
        -------
        results : dict[str] = str, list, or dict
            parsed representation of the class corresponding to the following
            schema. See individual language implementations of `_parse_class_node`
            for guidance on language-specific entries.

            results = {
                'original_string': 'verbatim code of class',
                'name': 'class name',
                'definition': 'class definition statement',
                'class_docstring': 'docstring for to to-level class definition,
                'attributes': [  # list of class attributes
                        'attr1_statement', ...
                    ],
                'methods': [
                    # list of class methods of the same form as top-level methods',
                    ...
                    ]
                }
        """
        msg = f"class_node must be of types {self.class_types}"
        assert class_node.type in self.class_types, msg
        return self._parse_class_node(class_node)

    def __init__(self, file_contents=None, parser=None, remove_comments=False):
        """
        Initialize LanguageParser

        Parameters
        ----------
        file_contents : str
            string containing a source code file contents
        parser : tree_sitter.parser (optional)
            optional pre-initialized parser
        remove_comments: True/False
            whether to strip comments from the source file before structural
            parsing. Default is False as docstrings are considered comments
            in some languages
        """
        self.starting_point = 0
        if parser:
            self.parser = parser
        else:
            self.parser = Parser()
            self.parser.set_language(get_language(LanguageId(self.get_lang())))
        if file_contents:
            self.update(file_contents)
            if remove_comments:  # must have file_contents to strip
                self.update(strip_comments(self))

    def update(self, file_contents):
        """Update the file being parsed"""
        self.file_bytes = file_contents.encode("utf-8")
        while self.file_bytes[:1] == "\n".encode("utf-8"):
            self.starting_point += 1
            self.file_bytes = self.file_bytes[1:]
        self.tree = self.parser.parse(self.file_bytes)

    def preprocess_file(self, file_contents):
        """
        Run any pre-processing on file_contents

        NOTE: should raise TimeoutException if limiting
        time execution of preprocessing

        And if filtering content it should return an empty string
        to indicate the file failed a content test (e.g. detecting
        and filtering minified code).
        """
        return file_contents

    @property
    def method_nodes(self):
        """
        List of top-level child nodes corresponding to methods
        Expect that `self.parse_method_node` will be run on these.
        """
        return children_of_type(self.tree.root_node, self.method_types)

    @property
    def class_nodes(self):
        """
        List of top-level child nodes corresponding to classes.
        Expect that `self.parse_class_node` will be run on these.
        """
        return children_of_type(self.tree.root_node, self.class_types)

    @property
    def import_nodes(self):
        """List of top-level child nodes corresponding to import statements"""
        return children_of_type(self.tree.root_node, self.import_types)

    @property
    def file_imports(self):
        """List of top-level child import statements"""
        return [self.span_select(node) for node in self.import_nodes]

    def span_select(self, *nodes, indent=True):
        """
        Select the part of the file_content corresponding
        to the span of nodes. Warning: if you give this non-consecutive
        nodes, it will return the file contents spanning between the nodes

        Parameters
        ----------
        nodes : TreeSitter.Node
            arbitrary number of nodes to use to extract file_contents
        (optional)
        indent : True/False
            If true, adds spaces to indent beginning of node contents
            to match true file position. Useful for maintaining relative
            indentation in class methods, for example.

        Returns
        -------
        selection : str
            selection of self.file_contents spanning all the input nodes
        """
        if not nodes or not all(nodes):
            return ""

        start, end = nodes[0].start_byte, nodes[-1].end_byte
        select = self.file_bytes[start:end].decode("utf-8")
        if indent:
            return " " * nodes[0].start_point[1] + select
        return select

    def select(self, nodes, indent=True):
        """
        span_select a list of nodes, individually.

        Parameters
        ----------
        nodes : List[TreeSitter.Node]
            list of nodes to extract file_contents
        (optional)
        indent : True/False
            If true, adds spaces to indent beginning of node contents
            to match true file position. Useful for maintaining relative
            indentation in class methods, for example.

        Returns
        -------
        selection : List[str]
            list of selection of self.file_contents spanning each input node
        """
        return [self.span_select(n, indent=indent) for n in nodes]

    @property
    def schema(self):
        """
        The file-level components of the schema

        See the top-level README.md file for a detailed description
        of the schema contents
        """
        return {
            "file_hash": static_hash(self.file_bytes),
            "file_docstring": self.file_docstring,
            "contexts": self.file_context,
            "methods": [self.parse_method_node(c) for c in self.method_nodes],
            "classes": [self.parse_class_node(c) for c in self.class_nodes],
        }
