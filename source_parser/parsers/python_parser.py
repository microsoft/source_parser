# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=duplicate-code
"""
python_parser.py

This is the class which uses tree_sitter to parse python files
into structural components defined by the source_parser schema

#NOTE: Currently this parser ignores `if __name__ == "__main__":` blocks

"""

from collections import defaultdict
from textwrap import dedent

from source_parser.parsers.language_parser import (
    LanguageParser,
    has_correct_syntax,
)
from source_parser.langtools.python import check_python3_attempt_fix, fix_indentation


class PythonParser(LanguageParser):
    """
    Parser for python source code structural feature extraction
    into the source_parser schema.
    """

    _method_types = ("function_definition", "decorated_definition")
    _class_types = ("class_definition", "decorated_definition")
    _import_types = ("import_statement", "import_from_statement")
    _docstring_types = ("string", "comment")
    _include_patterns = "*?.py"  # this parser reads .py files!

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

    @classmethod
    def get_lang(cls):
        return "python"

    @property
    def method_types(self):
        """Return method node types"""
        return self._method_types

    @property
    def class_types(self):
        """Return class node types string"""
        return self._class_types

    @property
    def import_types(self):
        """Return class node types string"""
        return self._import_types

    @property
    def include_patterns(self):
        return self._include_patterns

    @staticmethod
    def _distinguish_decorated(defn):
        def distinguish_decorated(node):
            if node.type == defn:
                return node
            if node.type == "decorated_definition":
                if node.children[-1].type == defn:
                    return node
            return None

        return distinguish_decorated

    def _get_decorated_defn(self, nodes, defn_type):
        return list(filter(None, map(self._distinguish_decorated(defn_type), nodes),))

    @property
    def class_nodes(self):
        return self._get_decorated_defn(
            self.tree.root_node.children, "class_definition"
        )

    @property
    def method_nodes(self):
        return self._get_decorated_defn(
            self.tree.root_node.children, "function_definition"
        )

    @staticmethod
    def _clean_docstring_comments(comment):
        comment = comment.strip().strip(""" "' """)
        comment = "\n".join(map(lambda s: s.lstrip("#"), comment.splitlines()))
        return dedent(comment)

    def preprocess_file(self, file_contents):
        """
        Run any pre-processing on file_contents

        Raises
        ------
        source_parser.langtools.python.TimeoutException
        """
        return fix_indentation(check_python3_attempt_fix(file_contents))

    @property
    def file_docstring(self):
        """The first single or multi-line comment in the file"""
        file_docstring = ""
        if not self.tree.root_node.children:
            return file_docstring
        first = self.tree.root_node.children[0]
        if first.children and first.children[0].type == "string":
            file_docstring = self.span_select(first.children[0])
        elif first.type == "comment":
            file_docstring = self.span_select(first)
        return self._clean_docstring_comments(file_docstring)

    @property
    def file_context(self):
        """List of global import and assignment statements"""
        context = self.file_imports
        for child in self.tree.root_node.children:
            if (
                child.type == "expression_statement"
                and child.children[0].type == "assignment"
            ):
                context.append(self.span_select(child))
        return context

    def _parse_method_node(self, method_node):
        """See LanguageParser.parse_method_node for documentation"""

        results = {
            "attributes": defaultdict(list),
            "syntax_pass": has_correct_syntax(method_node),
            "default_arguments": {},
            "original_string": self.span_select(method_node),
            "byte_span": (method_node.start_byte, method_node.end_byte),
            "start_point": (self.starting_point + method_node.start_point[0], method_node.start_point[1]),
            "end_point": (self.starting_point + method_node.end_point[0], method_node.end_point[1]),
        }

        # handle decorators
        signature = []
        if method_node.type == "decorated_definition":
            for child in method_node.children:
                if child.type == "decorator":
                    decorator = self.span_select(child)
                    results["attributes"]["decorators"].append(decorator)
                    signature.append(decorator)
                elif child.type == "function_definition":
                    method_node = child

        # extract signature features and default arguments
        for def_child in method_node.children[:-1]:

            if def_child.type == "identifier":
                results["name"] = self.span_select(def_child, indent=False).strip()

            # store default arguments
            if def_child.type == "parameters":
                for arg_child in def_child.children:
                    if "default" in arg_child.type:
                        default_idx = list(
                            map(lambda n: n.type, arg_child.children)
                        ).index("=")
                        arg = self.span_select(
                            *arg_child.children[:default_idx], indent=False
                        )
                        results["default_arguments"][arg] = self.span_select(
                            *arg_child.children[default_idx + 1:], indent=False
                        )

        signature.append(self.span_select(*method_node.children[:-1]))
        results["signature"] = "\n".join(signature)

        results["body"] = ""
        results["docstring"] = ""
        body_node = method_node.children[-1]
        if body_node.children and body_node.children[0].children:
            if body_node.children[0].children[0].type in self._docstring_types:
                results["docstring"] = self._clean_docstring_comments(
                    self.span_select(body_node.children[0].children[0]),
                )
                results["body"] = self.span_select(*body_node.children[1:])
            else:
                results["body"] = self.span_select(body_node)

        return results

    def _parse_class_node(self, class_node):
        results = {
            "attributes": defaultdict(list),
            "class_docstring": "",
            "methods": [],
            "byte_span": (class_node.start_byte, class_node.end_byte),
            "start_point": (self.starting_point + class_node.start_point[0], class_node.start_point[1]),
            "end_point": (self.starting_point + class_node.end_point[0], class_node.end_point[1]),

        }
        results["original_string"] = self.span_select(class_node)

        definition = []
        if class_node.type == "decorated_definition":
            for child in class_node.children:
                if child.type == "decorator":
                    decorator = self.span_select(child).strip()
                    results["attributes"]["decorators"].append(decorator)
                    definition.append(decorator)
                elif child.type == "class_definition":
                    class_node = child

        defn_index = list(map(lambda n: n.type, class_node.children)).index(":") + 1
        definition.append(self.span_select(*class_node.children[:defn_index]))
        results["definition"] = "\n".join(definition)

        results["name"] = self.span_select(class_node.children[1], indent=False)

        is_class = self._distinguish_decorated("class_definition")
        is_method = self._distinguish_decorated("function_definition")
        for i, child in enumerate(class_node.children[-1].children):
            if i == 0 and child.children and child.children[0].type == "string":
                results["class_docstring"] = self._clean_docstring_comments(
                    self.span_select(child.children[0])
                )
            if child.children and child.children[0].type == "assignment":
                results["attributes"]["attribute_expressions"].append(
                    self.span_select(child, indent=False)
                )
            if is_method(child):
                results["methods"].append(self.parse_method_node(child))
            if is_class(child):
                results["attributes"]["classes"].append(self.parse_class_node(child))
        return results
