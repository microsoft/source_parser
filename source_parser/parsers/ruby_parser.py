# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=duplicate-code
from textwrap import dedent

from source_parser.parsers.language_parser import (
    LanguageParser,
    children_of_type,
    traverse_type,
)
from source_parser.utils import static_hash


class RubyParser(LanguageParser):
    """
    Parser for python source code structural feature extraction
    into the source_parser schema.
    """

    _method_types = ("method", "singleton_method")
    _class_types = ("class",)
    _import_types = ("call",)
    _docstring_types = ("comment",)
    _namespace_types = ("module",)
    _include_patterns = "*?.rb"  # this parser reads .rb files!

    def __init__(self, file_contents=None, parser=None, remove_comments=True):
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
            parsing. Default is True as docstrings are separate from comments
        """
        super().__init__(file_contents, parser, remove_comments)

    def update(self, file_contents):
        """Update the file being parsed"""
        self.file_bytes = file_contents.encode("utf-8")
        self.tree = self.parser.parse(self.file_bytes)
        # key is tuple(start_byte, end_byte)
        self._node2namespace = {}
        self._traverse_namespace(self.tree.root_node)

    @classmethod
    def get_lang(cls):
        return "ruby"

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

    def _traverse_namespace(self, node, prefix=""):
        """
        Record the namespace information for classes or functions which are defined in specific namespace
        Also record its parent node
        """
        for child in node.children:
            namespace_name = ""
            if child.type in self.namespace_types:
                name_node = child.child_by_field_name("name")
                namespace_name = self.span_select(name_node, indent=False) + "." if name_node else ""
                sub_modules = [
                    sub_child
                    for sub_child in child.children
                    if sub_child.type == "module" and len(sub_child.children) > 0
                ]
                for sub_module_node in sub_modules:
                    sub_module_name_node = sub_module_node.child_by_field_name("name")
                    sub_module_namespace_name = self.span_select(
                        sub_module_name_node, indent=False
                    ) + "." if sub_module_name_node else ""
                    self._traverse_namespace(
                        sub_module_node, prefix + namespace_name + sub_module_namespace_name
                    )
                sub_nodes = [
                    sub_child
                    for sub_child in child.children
                    if sub_child.type in ("class", "method")
                ]

                if len(sub_nodes) > 0:
                    self._traverse_namespace(
                        child, prefix + namespace_name
                    )
            if child.type in self.class_types:
                self._node2namespace[(child.start_byte, child.end_byte)] = prefix
                # add nested classes namespace
                classes = [
                    child for child in child.children if child.type == "class"
                ]
                for cls_node in classes:
                    self._node2namespace[(cls_node.start_byte, cls_node.end_byte)] = prefix
            if child.type in self.method_types:
                self._node2namespace[(child.start_byte, child.end_byte)] = prefix + namespace_name

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

    @staticmethod
    def _check_node_def(defn):
        def check_node_def(node):
            if node.type == defn:
                return node
            return None

        return check_node_def

    @property
    def class_nodes(self):
        """
        List of top-level child nodes corresponding to classes and class node defined in namespaces.
        Expect that `self.parse_class_node` will be run on these.
        """
        class_nodes = children_of_type(self.tree.root_node, self.class_types)
        for node in self.namespace_nodes:
            class_nodes.extend(children_of_type(node, self.class_types))
            for child in node.children:
                class_nodes.extend(children_of_type(child, self.class_types))

        # class node in condition node
        for node in self.tree.root_node.children:
            class_nodes.extend(children_of_type(node, self.class_types))
            for child in node.children:
                class_nodes.extend(children_of_type(child, self.class_types))

        class_nodes = [cls_node for cls_node in class_nodes if len(cls_node.children) > 0]
        return class_nodes

    @property
    def method_nodes(self):
        """
        List of top-level child nodes corresponding to methods and method node defined in namespaces.
        In Ruby, methods should be declared in module and class, so in most cases it is expected no method return from this.
        Expect that `self.parse_method_node` will be run on these.
        """
        method_nodes = children_of_type(self.tree.root_node, self.method_types)
        for node in self.namespace_nodes:
            method_nodes.extend(children_of_type(node, self.method_types))
        method_nodes = [mtd_node for mtd_node in method_nodes if len(mtd_node.children) > 0]
        return method_nodes

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

        return self._clean_docstring_comments(file_docstring)

    @staticmethod
    def _clean_docstring_comments(comment):
        comment = comment.strip().strip(""" "' """)
        comment = "\n".join(map(lambda s: s.lstrip("#"), comment.splitlines()))
        return dedent(comment)

    @property
    def file_context(self):
        """List of global import and assignment statements"""
        contexts = []
        file_context_nodes = children_of_type(self.tree.root_node, self._import_types)
        for node in file_context_nodes:
            content = self.span_select(node).strip()
            if (
                content.startswith("require ")
                or content.startswith("require_")
                or content.startswith("include ")
            ):
                contexts.append(content)

        return contexts

    def _parse_method_node(self, method_node):
        """See LanguageParser.parse_method_node for documentation"""

        results = {
            "default_arguments": {},
            "original_string": self.span_select(method_node),
            "byte_span": (method_node.start_byte, method_node.end_byte),
            "start_point": (self.starting_point + method_node.start_point[0], method_node.start_point[1]),
            "end_point": (self.starting_point + method_node.end_point[0], method_node.end_point[1]),
            "attributes": {
                "namespace_prefix": "",
                "parameters": [],
            }
        }

        # In Ruby, method should be defined in class, so it is expected not in self._node2namespace
        if (method_node.start_byte, method_node.end_byte) in self._node2namespace:
            results["attributes"]["namespace_prefix"] = self._node2namespace[(method_node.start_byte, method_node.end_byte)]

        signature = []
        # extract signature features and default arguments
        for def_child in method_node.children:

            if def_child.type == "identifier":
                results["name"] = self.span_select(def_child, indent=False).strip()

            # store default arguments
            if def_child.type == "method_parameters":
                param_nodes = children_of_type(def_child, "identifier")
                for arg_child in def_child.children:
                    if "optional_parameter" in arg_child.type:
                        default_idx = list(
                            map(lambda n: n.type, arg_child.children)
                        ).index("=")
                        arg = self.span_select(
                            *arg_child.children[:default_idx], indent=False
                        )
                        results["default_arguments"][arg] = self.span_select(
                            *arg_child.children[default_idx + 1:], indent=False
                        )
                        param_nodes.append(arg_child)

                results["attributes"]["parameters"] = self.select(param_nodes, indent=False) if len(param_nodes) > 0 else []

        start_index = 0
        param_index = 1
        for i, child in enumerate(method_node.children):
            if child.type == "method_parameters":
                param_index = i
                break
        sig = self.span_select(*method_node.children[start_index:param_index + 1])
        while sig.strip() == "def self":
            param_index += 2
            sig = self.span_select(*method_node.children[start_index:param_index + 1])
        signature.append(sig)

        results["signature"] = "\n".join(signature)

        body_node = method_node
        # get nested classes and methods
        classes = (
            [
                self._parse_class_node(c)
                for c in children_of_type(body_node, self.class_types)
            ]
            if body_node
            else []
        )
        results["classes"] = classes

        methods = (
            [
                self._parse_method_node(c)
                for c in children_of_type(body_node, self.method_types)
            ]
            if body_node
            else []
        )
        results["methods"] = methods

        return results

    def _parse_class_node(self, class_node):
        results = {
            "class_docstring": "",
            "definition": "",
            "methods": [],
            "byte_span": (class_node.start_byte, class_node.end_byte),
            "start_point": (self.starting_point + class_node.start_point[0], class_node.start_point[1]),
            "end_point": (self.starting_point + class_node.end_point[0], class_node.end_point[1]),
            "attributes": {
                "namespace_prefix": "",
                "contexts": [],
                "attribute_expressions": [],
            }
        }
        results["original_string"] = self.span_select(class_node)

        # This class is not nested in class or method, but defined in namespace, its parent should have been recorded
        if (class_node.start_byte, class_node.end_byte) in self._node2namespace:
            results["attributes"]["namespace_prefix"] = self._node2namespace[(class_node.start_byte, class_node.end_byte)]

        name_node = class_node.child_by_field_name("name")
        results["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )

        # bases
        bases_node = class_node.child_by_field_name("superclass")
        results["attributes"]["bases"] = [
            self.span_select(base_node, indent=False) for base_node in bases_node.children if base_node.type not in ["<"]
        ] if bases_node else []

        definition = []
        start_index = 0
        param_index = 1
        for i, child in enumerate(class_node.children):
            if child.type == "superclass":
                param_index = i
                break
        sig = self.span_select(*class_node.children[start_index:param_index + 1])
        definition.append(sig)

        results["definition"] = "\n".join(definition)

        body_node = class_node
        # In Ruby, include is the most common way of importing external code into a class
        contexts = []
        attribute_expressions = []
        file_context_nodes = children_of_type(class_node, ("call", ))
        for node in file_context_nodes:
            content = self.span_select(node)
            if content.strip().startswith("include "):
                for child in node.children:
                    if child.type == "argument_list":
                        contexts.append(self.span_select(child).replace("::", ".").strip())
            else:
                attribute_expressions.append(content)

        attribute_expressions_nodes = children_of_type(class_node, ("assignment", ))
        for node in attribute_expressions_nodes:
            attribute_expressions.append(self.span_select(node))

        results["attributes"]["contexts"] = contexts
        results["attributes"]["attribute_expressions"] = attribute_expressions

        # get nested classes and methods
        classes = (
            [
                self._parse_class_node(c)
                for c in children_of_type(body_node, self.class_types) if len(c.children) > 0
            ]
            if body_node
            else []
        )
        results["classes"] = classes

        methods = (
            [
                self._parse_method_node(c)
                for c in children_of_type(body_node, self.method_types) if len(c.children) > 0
            ]
            if body_node
            else []
        )
        results["methods"] = methods
        return results

    @property
    def schema(self):
        """
        Override schema to consider open classes cases.
        """
        classes = []
        class_names = []
        spans = []
        in_class_methods = []
        for c in self.class_nodes:
            class_result = self.parse_class_node(c)
            full_class_name = f"{class_result['attributes']['namespace_prefix']}{class_result['name']}"
            if full_class_name not in class_names:
                class_names.append(full_class_name)
                classes.append(class_result)
                spans.append((c.start_byte, c.end_byte))
            elif (c.start_byte, c.end_byte) not in spans:
                idx = class_names.index(full_class_name)
                classes[idx]["methods"].extend(class_result["methods"])
                spans.append((c.start_byte, c.end_byte))
            in_class_methods.extend([method["byte_span"] for method in class_result["methods"]])

        return {
            "file_hash": static_hash(self.file_bytes),
            "file_docstring": self.file_docstring,
            "contexts": self.file_context,
            "methods": [self.parse_method_node(c) for c in self.method_nodes if (c.start_byte, c.end_byte) not in in_class_methods],
            "classes": classes,
        }
