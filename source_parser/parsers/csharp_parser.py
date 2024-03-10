# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=duplicate-code
"""
csharp_parser.py

This is the class which uses tree_sitter to parse C# files
into structural components defined by the source_parser schema

We combine classes, structs and interfaces together as 'classes' and annotate their types by 'module_type'
csharp_parser language-specific output schema for classes/structs/interfaces:
[{
    'module_type': 'class/struct/interface',
    'name': 'class name',
    'original_string': 'verbatim entire string of class',
    'body': 'verbatim string for class body',
    'docstring': 'comment preceeding class',
    'syntax_pass': True/False,
    'classes': [...], # nested classes
    'methods': [{
                'body': 'method body, verbatim string',
                'docstring': 'comment preceeding method',
                'name': 'method name',
                'original_string': 'verbatim string of entire method',
                'signature': 'verbatim string of method signature',
                'syntax_pass': True/False,
                'classes': [...] # nested classes,
                'methods': [...] # nested methods,
                'attributes': {
                               'namespace_prefix': 'namespace of method, in form of namespace1.namespace2.',
                               'modifiers': ['list of public/private/abstract/virtual...'],
                               'attributes': [list of attributes used for class, even custom attributes],
                               'parameters': ['list of parameters'],
                               'return_type': 'return type',
                            },
              ... ],

    'attributes': {
                'namespace_prefix': 'namespace of method, in form of namespace1.namespace2.',
                'bases': ['list of base class/struct/interface'],
                'modifiers': ['list of public/private/abstract/virtual...'],
                'attributes': [list of attributes used for class, even custom attributes],

                'fields': [{
                            'original_string': 'verbatim entire string of statement',
                            'docstring': 'comment preceeding field',
                            'modifiers': ['list of public/private/abstract/virtual...'],
                            'type': 'int e.g.',
                            'name': 'name of field',
                            'syntax_pass': True/False,
                            }, ...]
                'properties': [{
                                'original_string': 'verbatim entire string of statement',
                                'docstring': 'comment preceeding field',
                                'modifiers': ['list of public/private/abstract/virtual...'],
                                'type': 'int e.g.',
                                'name': 'name of property',
                                'accessors': 'like a body',
                                'syntax_pass': True/False,
                                }, ...]
                },
}, ... ]
"""

from typing import List

from source_parser.parsers.language_parser import (
    LanguageParser,
    has_correct_syntax,
    traverse_type,
    children_of_type,
)
from source_parser.parsers.commentutils import strip_c_style_comment_delimiters


class CSharpParser(LanguageParser):
    """
    Parser for C# source code structural feature extraction
    into the source_parser schema.
    """
    _method_types = (
        "constructor_declaration",
        "method_declaration",
    )
    _class_types = (
        "class_declaration",
        "struct_declaration",
        "interface_declaration",
    )
    _import_types = (
        "using_directive",
    )
    _docstring_types = ("comment",)
    _namespace_types = ("namespace_declaration",)
    _include_patterns = "*?.cs"

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
        return "csharp"

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
        Returns a list of docstring nodes directly before 'node'.
        If the previous sibling is not a docstring, returns None.

        Note that in C#, docstring may be in form of
        /// comment line 1
        /// comment line 2
        ...
        It will be parsed as several nodes, so return a list.
        """

        if parent_node is None:
            parent_node = self.tree.root_node

        node_index = -1
        for i, child in enumerate(parent_node.children):
            if child == node:
                node_index = i
                break
        if node_index < 0:
            return None

        stop_index = -1
        for sib_index in range(node_index - 1, -1, -1):
            if parent_node.children[sib_index].type not in self._docstring_types:
                stop_index = sib_index
                break

        if node_index == 0 or stop_index == node_index - 1:
            return None
        return parent_node.children[stop_index + 1:node_index]

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
        Record the namespace information for classes or functions which are defined in specific namespace
        Also record its parent node
        """
        for child in node.children:
            if child.type in self.namespace_types:
                name_node = child.child_by_field_name("name")
                namespace_name = self.span_select(name_node, indent=False) if name_node else "(unique)"
                for grandchild in child.children:
                    if grandchild.type == "declaration_list":
                        self._traverse_namespace(grandchild, prefix + namespace_name + ".")
                        break
            if child.type in self.class_types:
                self._node2namespace[(child.start_byte, child.end_byte)] = prefix
                # It may take too much memory to save node
                self._node2parent[(child.start_byte, child.end_byte)] = node
            if child.type in self.method_types:
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
        In C#, methods should be declared in class, struct or interface, so in most cases it is expected no method return from this.
        Expect that `self.parse_method_node` will be run on these.
        """
        method_nodes = children_of_type(self.tree.root_node, self.method_types)
        for node in self.namespace_nodes:
            for child in node.children:
                if child.type == "declaration_list":
                    method_nodes.extend(children_of_type(child, self.method_types))
                    break
        return method_nodes

    def _get_field_info(self, field_node):
        """
        get field type and name
        """
        field_info = {
            "type": "",
            "name": "",
        }
        for child in field_node.children:
            if child.type == "variable_declaration":
                type_node = child.child_by_field_name("type")
                field_info["type"] = self.span_select(type_node, indent=False) if type_node else ""
                for grand_child in child.children:
                    if grand_child.type == "variable_declarator":
                        field_info["name"] = self.span_select(grand_child, indent=False)
                break
        return field_info

    def _parse_method_node(self, method_node, parent_node=None):
        result = {
            "original_string": self.span_select(method_node),
            "byte_span": (method_node.start_byte, method_node.end_byte),
            "start_point": (self.starting_point + method_node.start_point[0], method_node.start_point[1]),
            "end_point": (self.starting_point + method_node.end_point[0], method_node.end_point[1]),
            "attributes": {
                "namespace_prefix": "",
                "attributes": [],
                "parameters": [],
            }
        }

        # In C#, method should be defined in class, so it is expected not in self._node2namespace
        if (method_node.start_byte, method_node.end_byte) in self._node2namespace:
            parent_node = self._node2parent[(method_node.start_byte, method_node.end_byte)]
            result["attributes"]["namespace_prefix"] = self._node2namespace[(method_node.start_byte, method_node.end_byte)]

        comment_nodes = self._get_docstring_before(method_node, parent_node)
        result["docstring"] = (
            strip_c_style_comment_delimiters(
                self.span_select(*comment_nodes)
            ).strip()
            if comment_nodes
            else ""
        )

        type_node = method_node.child_by_field_name("type")
        result["attributes"]["return_type"] = (
            self.span_select(type_node, indent=False) if type_node else ""
        )

        name_node = method_node.child_by_field_name("name")
        result["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )

        for child in method_node.children:
            if child.type == "parameter_list":
                param_nodes = children_of_type(child, "parameter")
                result["attributes"]["parameters"] = self.select(param_nodes, indent=False) if len(param_nodes) > 0 else []
                break

        body_node = method_node.child_by_field_name("body")
        result["body"] = (
            self.span_select(body_node) if body_node else ""
        )

        modifiers_node_list = children_of_type(method_node, "modifier")
        result["attributes"]["modifiers"] = self.select(modifiers_node_list, indent=False) if len(modifiers_node_list) > 0 else []

        # attributes is always the first child
        if method_node.children[0].type == "attribute_list":
            attribute_node_list = children_of_type(method_node.children[0], "attribute")
            result["attributes"]["attributes"] = self.select(attribute_node_list, indent=False) if len(attribute_node_list) > 0 else []

        # signature from after attribute list to parameter_list
        start_index = 0
        if method_node.children[0].type == "attribute_list":
            start_index = 1
        for i, child in enumerate(method_node.children):
            if child.type == "parameter_list":
                param_index = i
                break
        result["signature"] = self.span_select(*method_node.children[start_index:param_index + 1])

        # sometimes when the code is not syntax correct
        # it might cause tree-sitter recursion depth exceed error
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
            "module_type": class_node.type.split("_")[0],
            "original_string": self.span_select(class_node),
            "byte_span": (class_node.start_byte, class_node.end_byte),
            "start_point": (self.starting_point + class_node.start_point[0], class_node.start_point[1]),
            "end_point": (self.starting_point + class_node.end_point[0], class_node.end_point[1]),
            "attributes": {
                "namespace_prefix": "",
                "attributes": [],
                "fields": [],
                "properties": [],
            }
        }

        defn_index = list(map(lambda n: n.type, class_node.children)).index("identifier") + 1
        result["definition"] = self.span_select(*class_node.children[:defn_index])

        # This class is not nested in class or method, but defined in namespace, its parent should have been recorded
        if (class_node.start_byte, class_node.end_byte) in self._node2namespace:
            parent_node = self._node2parent[(class_node.start_byte, class_node.end_byte)]
            result["attributes"]["namespace_prefix"] = self._node2namespace[(class_node.start_byte, class_node.end_byte)]

        comment_nodes = self._get_docstring_before(class_node, parent_node)
        result["class_docstring"] = (
            strip_c_style_comment_delimiters(
                self.span_select(*comment_nodes)
            ).strip()
            if comment_nodes
            else ""
        )

        name_node = class_node.child_by_field_name("name")
        result["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )

        body_node = class_node.child_by_field_name("body")
        result["body"] = (
            self.span_select(body_node) if body_node else ""
        )

        modifiers_node_list = children_of_type(class_node, "modifier")
        result["attributes"]["modifiers"] = self.select(modifiers_node_list, indent=False) if len(modifiers_node_list) > 0 else []

        # attributes is always the first child
        if class_node.children[0].type == "attribute_list":
            attribute_node_list = children_of_type(class_node.children[0], "attribute")
            result["attributes"]["attributes"] = self.select(attribute_node_list, indent=False) if len(attribute_node_list) > 0 else []

        # bases
        bases_node = class_node.child_by_field_name("bases")
        result["attributes"]["bases"] = [
            self.span_select(base_node, indent=False) for base_node in bases_node.children if base_node.type not in [":", ","]
        ] if bases_node else []

        # fields
        fields = []
        field_nodes = children_of_type(body_node, "field_declaration") if body_node else []
        for node in field_nodes:
            field_dict = {
                "original_string": self.span_select(node, indent=False),
            }
            comment_nodes = self._get_docstring_before(node, body_node)
            field_dict["docstring"] = (
                strip_c_style_comment_delimiters(
                    self.span_select(*comment_nodes, indent=False)
                ).strip()
                if comment_nodes
                else ""
            )

            field_info = self._get_field_info(node)
            field_dict.update(field_info)

            modifier_nodes = children_of_type(node, "modifier")
            field_dict["modifiers"] = self.select(modifier_nodes, indent=False) if len(modifier_nodes) > 0 else []

            try:
                field_dict["syntax_pass"] = has_correct_syntax(node)
            except RecursionError:
                field_dict["syntax_pass"] = False

            fields.append(field_dict)

        result["attributes"]["fields"] = fields

        # properties
        properties = []
        property_nodes = children_of_type(body_node, "property_declaration") if body_node else []
        for node in property_nodes:
            property_dict = {
                "original_string": self.span_select(node, indent=False),
            }
            comment_nodes = self._get_docstring_before(node, body_node)
            property_dict["docstring"] = (
                strip_c_style_comment_delimiters(
                    self.span_select(*comment_nodes, indent=False)
                ).strip()
                if comment_nodes
                else ""
            )

            type_node = node.child_by_field_name("type")
            property_dict["type"] = (
                self.span_select(type_node, indent=False) if type_node else ""
            )

            name_node = node.child_by_field_name("name")
            property_dict["name"] = (
                self.span_select(name_node, indent=False) if name_node else ""
            )

            accessors_node = node.child_by_field_name("accessors")
            property_dict["accessors"] = (
                self.span_select(accessors_node, indent=False) if accessors_node else ""
            )

            modifier_nodes = children_of_type(node, "modifier")
            property_dict["modifiers"] = self.select(modifier_nodes, indent=False) if len(modifier_nodes) > 0 else []

            try:
                property_dict["syntax_pass"] = has_correct_syntax(node)
            except RecursionError:
                property_dict["syntax_pass"] = False

            properties.append(property_dict)

        result["attributes"]["properties"] = properties

        # sometimes when the code is not syntax correct
        # it might cause tree-sitter recursion depth exceed error
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
