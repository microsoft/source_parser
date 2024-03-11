# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=duplicate-code
"""
cpp_parser.py

This is the class which uses tree_sitter to parse CPP files
into structural components defined by the source_parser schema

cpp_parser language-specific output schema for classes:
[{
    'name': 'class name',
    'original_string': 'verbatim entire string of class',
    'body': 'verbatim string for class body',
    'docstring': 'comment preceeding class',
    'syntax_pass': True/False,
    'classes': [...] # nested classes,
    'methods': [...] # nested methods,
    'attributes': {
                'namespace_prefix': 'namespace of method, in form of namespace1::namespace2::',
                'annotations': ['list of public/private],
                'fields': [{
                            'original_string': 'verbatim entire string of statement',
                            'docstring': 'comment preceeding field',
                            'annotations': ['list of public/private/static/..],
                            'type': 'int e.g.',
                            'syntax_pass': True/False,
                            }, ...]
                },
}, ...]

cpp_parser language-specific output schema for methods:
[{
    'name': 'method name',
    'original_string': 'verbatim string of entire method',
    'signature': 'verbatim string of method signature',
    'body': 'method body, verbatim string',
    'docstring': 'comment preceeding method',
    'syntax_pass': True/False,
    'classes': [...] # nested classes,
    'methods': [...] # nested methods,
    'attributes': {
                'namespace_prefix': 'namespace of method, in form of namespace1::namespace2::',
                'annotations': ['list of public/private/static/virtual/const],
                'return_type': 'return type',
                },
}, ...]
"""

from typing import List

from source_parser.parsers.language_parser import (
    LanguageParser,
    has_correct_syntax,
    traverse_type,
    children_of_type,
    previous_sibling,
)
from source_parser.parsers.commentutils import strip_c_style_comment_delimiters


class CppParser(LanguageParser):
    """
    Parser for Cpp source code structural feature extraction
    into the source_parser schema.
    """
    _method_types = ("function_definition",)
    _class_types = ("class_specifier",)
    _import_types = (
        "preproc_include",
        "preproc_def",
        "preproc_call",
    )
    _docstring_types = ("comment",)
    _namespace_types = ("namespace_definition",)
    _include_patterns = "*?.cpp"

    def update(self, file_contents):
        """Update the file being parsed"""
        self.file_bytes = file_contents.encode("utf-8")
        self.tree = self.parser.parse(self.file_bytes)

        # key is tuple(start_byte, end_byte)
        self._node2namespace = {}
        self._node2parent = {}
        self._traverse_namespace(self.tree.root_node)

    @classmethod
    def get_lang(cls):
        return "cpp"

    @property
    def method_types(self):
        """Return method node types"""
        return self._method_types

    @property
    def class_types(self):
        """Return class node types string"""
        return self._class_types

    @property
    def namespace_types(self):
        """Return namespace node types string"""
        return self._namespace_types

    @property
    def import_types(self):
        """Return class node types string"""
        return self._import_types

    @property
    def include_patterns(self):
        return self._include_patterns

    def _get_docstring_before(self, node, parent_node=None):
        """
        Returns docstring node directly before 'node'.

        If the previous sibling is not a docstring, returns None.
        """

        if parent_node is None:
            parent_node = self.tree.root_node

        prev_sib = previous_sibling(node, parent_node)
        if prev_sib is None:
            return None
        if prev_sib.type in self._docstring_types:
            return prev_sib
        return None

    @property
    def file_docstring(self):
        """The first single or multi-line comment in the file"""

        file_docstring = ""
        if not self.tree.root_node.children:
            return file_docstring
        for child in self.tree.root_node.children:
            if child.type != "comment":
                break
            file_docstring += self.span_select(child) + "\n"

        return strip_c_style_comment_delimiters(file_docstring).strip()

    @property
    def file_context(self) -> List[str]:
        """List of global import and define"""

        file_context_nodes = children_of_type(self.tree.root_node, self._import_types)
        return [self.span_select(node).strip() for node in file_context_nodes]

    def _traverse_namespace(self, node, prefix=""):
        """
        record the namespace information for classes or functions which are defined in specific namespace
        Also record its parent node
        """
        for child in node.children:
            if child.type in self.namespace_types:
                name_node = child.child_by_field_name("name")
                namespace_name = self.span_select(name_node, indent=False) if name_node else "(unique)"
                for grandchild in child.children:
                    if grandchild.type == "declaration_list":
                        self._traverse_namespace(grandchild, prefix + namespace_name + "::")
                        break
            if child.type == "class_specifier":
                self._node2namespace[(child.start_byte, child.end_byte)] = prefix
                # It may take too much memory to save node
                self._node2parent[(child.start_byte, child.end_byte)] = node
            if child.type == "function_definition":
                self._node2namespace[(child.start_byte, child.end_byte)] = prefix
                self._node2parent[(child.start_byte, child.end_byte)] = node

    @property
    def namespace_nodes(self):
        """
        List of all nodes corresponding to namespace definition.
        """
        namespace_nodes = []
        try:
            traverse_type(self.tree.root_node, namespace_nodes, self.namespace_types)
        # sometimes when the code is not syntax correct
        # it might cause tree-sitter recursion depth exceed error (e.g. in a very long list)
        except RecursionError:
            pass
        return namespace_nodes

    @property
    def class_nodes(self):
        """
        List of top-level child nodes corresponding to classes and class node defined in namespaces.
        Expect that `self.parse_class_node` will be run on these.
        """
        class_nodes = children_of_type(self.tree.root_node, self.class_types)
        for node in self.namespace_nodes:
            for child in node.children:
                if child.type == "declaration_list":
                    class_nodes.extend(children_of_type(child, self.class_types))
                    break
        return class_nodes

    @property
    def method_nodes(self):
        """
        List of top-level child nodes corresponding to methods and method node defined in namespaces.
        Expect that `self.parse_method_node` will be run on these.
        """
        method_nodes = children_of_type(self.tree.root_node, self.method_types)
        for node in self.namespace_nodes:
            for child in node.children:
                if child.type == "declaration_list":
                    method_nodes.extend(children_of_type(child, self.method_types))
                    break
        return method_nodes

    def _get_signature(self, method_node):
        """
        return all child nodes corresponding to a method signature
        """
        nodes = []
        for child in method_node.children:
            if child.type == "compound_statement":
                return self.span_select(*nodes, indent=False) if len(nodes) > 0 else ""
            nodes.append(child)
        return self.span_select(*nodes, indent=False) if len(nodes) > 0 else ""

    def _parse_method_node(self, method_node, parent_node=None):
        result = {
            "original_string": self.span_select(method_node, indent=False),
            "byte_span": (method_node.start_byte, method_node.end_byte),
            "start_point": (self.starting_point + method_node.start_point[0], method_node.start_point[1]),
            "end_point": (self.starting_point + method_node.end_point[0], method_node.end_point[1]),
            "signature": self._get_signature(method_node),
            "attributes": {
                "namespace_prefix": "",
                "annotations": []
            }
        }

        # This method is not nested in class or method, but defined in namespace, its parent should have been recorded
        if (method_node.start_byte, method_node.end_byte) in self._node2namespace:
            parent_node = self._node2parent[(method_node.start_byte, method_node.end_byte)]
            result["attributes"]["namespace_prefix"] = self._node2namespace[(method_node.start_byte, method_node.end_byte)]

        comment_node = self._get_docstring_before(method_node, parent_node)
        result["docstring"] = (
            strip_c_style_comment_delimiters(
                self.span_select(comment_node, indent=False)
            ).strip()
            if comment_node
            else ""
        )

        body_node = method_node.child_by_field_name("body")
        result["body"] = (
            self.span_select(body_node, indent=False) if body_node else ""
        )

        name_node = method_node.child_by_field_name("declarator").child_by_field_name("declarator")
        result["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )

        type_node = method_node.child_by_field_name("type")
        result["attributes"]["return_type"] = (
            self.span_select(type_node, indent=False) if type_node else ""
        )

        # get public or private annotation if it's nested in a class, default is private
        if parent_node and parent_node.type == "field_declaration_list":
            access = "private"
            for child in parent_node.children:
                if child == method_node:
                    result["attributes"]["annotations"].append(access)
                    break
                if child.type == "access_specifier":
                    access = self.span_select(child.children[0], indent=False)

        # get annotations other than public/private
        for child in method_node.children:
            if child.type == "function_declarator":
                # const annotation
                if len(child.children) > 0 and child.children[-1].type == "type_qualifier":
                    result["attributes"]["annotations"].append(self.span_select(child.children[-1], indent=False))
                break
            # static/virtual/explicit annotation
            if child.type in ["storage_class_specifier", "virtual_function_specifier", "explicit_function_specifier"]:
                result["attributes"]["annotations"].append(self.span_select(child, indent=False))

        # sometimes when the code is not syntax correct
        # it might cause tree-sitter recursion depth exceed error (e.g. test/assets/cpp_examples/LongList.cpp)
        try:
            result["syntax_pass"] = has_correct_syntax(method_node)
        except RecursionError:
            result["syntax_pass"] = False

        # get nested classes and methods
        classes = (
            [
                self._parse_class_node(c, body_node)
                for c in children_of_type(body_node, self.class_types)
            ]
            if body_node
            else []
        )
        result["classes"] = classes

        methods = (
            [
                self._parse_method_node(c, body_node)
                for c in children_of_type(body_node, self.method_types)
            ]
            if body_node
            else []
        )
        result["methods"] = methods

        return result

    def _parse_class_node(self, class_node, parent_node=None):
        result = {
            "original_string": self.span_select(class_node, indent=False),
            "byte_span": (class_node.start_byte, class_node.end_byte),
            "start_point": (self.starting_point + class_node.start_point[0], class_node.start_point[1]),
            "end_point": (self.starting_point + class_node.end_point[0], class_node.end_point[1]),
            "attributes": {
                "namespace_prefix": "",
                "annotations": [],
                "fields": []
            }
        }

        # This class is not nested in class or method, but defined in namespace, its parent should have been recorded
        if (class_node.start_byte, class_node.end_byte) in self._node2namespace:
            parent_node = self._node2parent[(class_node.start_byte, class_node.end_byte)]
            result["attributes"]["namespace_prefix"] = self._node2namespace[(class_node.start_byte, class_node.end_byte)]

        comment_node = self._get_docstring_before(class_node, parent_node)
        result["docstring"] = (
            strip_c_style_comment_delimiters(
                self.span_select(comment_node, indent=False)
            ).strip()
            if comment_node
            else ""
        )

        name_node = class_node.child_by_field_name("name")
        result["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )

        body_node = class_node.child_by_field_name("body")
        result["body"] = (
            self.span_select(body_node, indent=False) if body_node else ""
        )

        # get public or private annotation if it's nested in a class, default is private
        if parent_node and parent_node.type == "field_declaration_list":
            access = "private"
            for child in parent_node.children:
                if child == class_node:
                    result["attributes"]["annotations"].append(access)
                    break
                if child.type == "access_specifier":
                    access = self.span_select(child.children[0], indent=False)

        fields = []
        access = "private"
        if body_node and len(body_node.children) > 0:
            for field in body_node.children:
                if field.type == "access_specifier":
                    access = self.span_select(field.children[0], indent=False)
                if field.type != "field_declaration":
                    continue
                field_dict = {
                    "original_string": self.span_select(field, indent=False),
                    "annotations": [access],
                }

                comment_node = self._get_docstring_before(field, body_node)
                field_dict["docstring"] = (
                    strip_c_style_comment_delimiters(
                        self.span_select(comment_node, indent=False)
                    ).strip()
                    if comment_node
                    else ""
                )

                type_node = field.child_by_field_name("type")
                field_dict["type"] = (
                    self.span_select(type_node, indent=False) if type_node else ""
                )

                if field.children[0].type == "storage_class_specifier":
                    field_dict["annotations"].append(self.span_select(field.children[0], indent=False))

                try:
                    field_dict["syntax_pass"] = has_correct_syntax(field)
                except RecursionError:
                    field_dict["syntax_pass"] = False

                fields.append(field_dict)
        result["attributes"]["fields"] = fields

        # sometimes when the code is not syntax correct
        # it might cause tree-sitter recursion depth exceed error (e.g. test/assets/cpp_examples/LongList.cpp)
        try:
            result["syntax_pass"] = has_correct_syntax(class_node)
        except RecursionError:
            result["syntax_pass"] = False

        # get nested classes and methods
        classes = (
            [
                self._parse_class_node(c, body_node)
                for c in children_of_type(body_node, self.class_types)
            ]
            if body_node
            else []
        )
        result["classes"] = classes

        methods = (
            [
                self._parse_method_node(c, body_node)
                for c in children_of_type(body_node, self.method_types)
            ]
            if body_node
            else []
        )
        result["methods"] = methods

        return result
