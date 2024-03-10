# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=too-many-public-methods,duplicate-code
"""
jsts_parser.py

Contains a class that uses tree-sitter to parse JavaScript and TypeScript files
into the structured schema specified in source_parser

javascript_parser language-specific output schema for JavaScript file containing a class:
[{
    'docstring': 'comment preceeding class',

    'attributes': {
                 'decorators' : ['@decorator1', '@decorator2', ...]
                 'expression' : ['property1 = value', 'property2 = value', ...]
                 'heritage' : ['extends other_class_name1', ...]
                },

    'methods': [{'attributes': {
                     'decorators' : ['@decorator1', '@decorator2', ...]
                             },

               'docstring': 'comment preceeding method',
            },
              ... ],
}, ... ]

javascript_parser language-specific output schema for file-context:

{
    'contexts' : [
        'import statement 1',
        'import statement 2',
    ]
}
"""
from typing import List, Dict, Union
from source_parser.parsers.language_parser import (
    nodes_are_equal,
    LanguageParser,
    has_correct_syntax,
    children_of_type,
)
from source_parser.parsers.commentutils import strip_c_style_comment_delimiters
from source_parser.langtools.javascript import is_minified


class JSTSParser(LanguageParser):
    """Gathers the elements of the schema of a program in Javascript/Typescript
    There is a manner in which to define a class using a function:
    var ClassName = (function(){})
    As a result of this syntactically being a variable declaration and a function defined inside,
    the parser will extract the function and store it in the methods property.

    Classes can be decorated, @something goes above class declaration
    Properties can be decorated, @something goes above the properites
    Class methods can be decorated, @something goes above the class method
    """

    _method_types = (
        "function_declaration",
        "generator_function_declaration",
        "arrow_function",
        "function",
        "generator_function",
        "method_definition"
    )
    _inside_method_types = (
        "function",
        "generator_function",
        "method_definition",
        "arrow_function"
    )
    _class_types = (
        "class_declaration",
        "class",
    )
    _import_types = (
        "import_statement",
    )

    _function_body_types = (
        "statement_block",
        "binary_expression",
        "ternary_expression",
        "new_expression"
    )

    _name_types = (
        "identifier", "property_identifier",
        "number", "string", "computed_property_name"
    )

    _docstring_types = ("comment",)
    _declaration_types = (
        "variable_declaration",
        "lexical_declaration",
    )
    _expression_types = ("expression_statement",)

    _include_patterns = ("*?.js", "*?.ts")
    _exclude_patterns = ("*.min.js", ".?*")

    @staticmethod
    def get_first_child_of_type(parent, type_string):
        """
        Given a specific type of node, find and return that node
        Parameters
        ----------
        type_node : <Node kind=, start_point=(*,*), end_point=(*,*)>
            kind will depend on the type desired
        type_strings : str, List[str], type of node that represents the desired string
            decorators : "decorator"
        Returns
        -------
        child : tree-sitter node
            <Node kind=type_string, start_point=(*,*), end_point=(*,*)>
        None
            if the node cannot be found
            """
        if isinstance(type_string, str):
            return JSTSParser.get_first_child_of_type(parent, [type_string])
        for child in parent.children:
            if child.type in type_string:
                return child
        return None

    def update(self, file_contents):
        """Update the file being parsed"""
        self.file_bytes = file_contents.encode("utf-8")
        self.tree = self.parser.parse(self.file_bytes)
        # For methods defined as variable declarations
        # the method docstring is the sibling node of the declaration
        # so it's necessary to record the corresponding declaration node of such method
        # key is tuple(start_byte, end_byte) of method
        self._node2declaration = {}
        self._node2name = {}
        self._node2export = {}

    @classmethod
    def get_lang(cls) -> str:
        """Return parser language"""
        return "typescript"

    @property
    def method_types(self):
        """Return method node types"""
        return self._method_types

    @property
    def inside_method_types(self):
        """Return inside method node types"""
        return self._inside_method_types

    @property
    def class_types(self):
        """Return class node types string"""
        return self._class_types

    @property
    def import_types(self):
        """Return import node types"""
        return self._import_types

    @property
    def function_body_types(self):
        """Return function body node types"""
        return self._function_body_types

    @property
    def declaration_types(self):
        """Return declaration node types"""
        return self._declaration_types

    @property
    def expression_types(self):
        """Return expression node types"""
        return self._expression_types

    @property
    def include_patterns(self):
        return self._include_patterns

    @property
    def exclude_patterns(self):
        return self._exclude_patterns

    def preprocess_file(self, file_contents):
        """
        Detect minified javascript with a 25s timeout.
        WARNING: assumes the parser has already been updated!

        Parameters
        ----------
        file_contents: str
            contents of source file

        Returns
        -------
        processed_contents: str
            return and empty string if minified code was
            detected and returns the original contents
            otherwise.

        Raises
        ------
        TimeoutException
            if minified detection takes longer than 25s,
            this exception is raised
        """
        if is_minified(self):
            return ""
        return file_contents

    def get_fn_in_declarations(self, node):
        """
        Extract methods defined inside declarations
        """
        methods = []
        declarations = children_of_type(node, self.declaration_types)

        for declaration in declarations:
            # check if it is a variable_declarator node whose value is a function
            # this will work for functions defined as variables
            declarators = children_of_type(declaration, "variable_declarator")
            if len(declarators) > 0:
                declarator = declarators[0]
            else:
                continue
            value_node = declarator.child_by_field_name("value")
            name_node = declarator.child_by_field_name("name")

            if not value_node:
                continue
            self._node2name[(value_node.start_byte, value_node.end_byte)] = name_node.text.decode('utf-8')

            if value_node.type in self.inside_method_types:
                methods.append(value_node)

                self._node2declaration[(value_node.start_byte, value_node.end_byte)] = declaration
            elif value_node.type in ["object", "parenthesized_expression"] and len(value_node.children) > 0:
                for method_def in children_of_type(value_node, self.inside_method_types):
                    methods.append(method_def)
                    self._node2declaration[(method_def.start_byte, method_def.end_byte)] = declaration
                # If the first child except ( or { is call_expression, the child of call_expression might be a function.
                if value_node.children[1].type == "call_expression" and len(value_node.children[1].children) > 0 \
                        and value_node.children[1].children[0].type in self.inside_method_types:
                    method_def = value_node.children[1].children[0]
                    methods.append(method_def)
                    self._node2declaration[(method_def.start_byte, method_def.end_byte)] = declaration

        return methods

    def get_fn_in_expressions(self, node):
        """
        Extract methods defined inside expression statements.
        """
        methods = []
        expressions = children_of_type(node, self.expression_types)
        for expression in expressions:
            # check if it is an assignment_expression node whose right is a function
            assignments = children_of_type(expression, "assignment_expression")
            if len(assignments) > 0:
                assignment = assignments[0]
            else:
                continue
            right_node = assignment.child_by_field_name("right")
            if not right_node:
                continue
            if right_node.type in self.inside_method_types:
                methods.append(right_node)
                self._node2declaration[(right_node.start_byte, right_node.end_byte)] = expression
        return methods

    def get_fn_in_exports(self, node):
        """
        Extract methods defined inside export statements.
        """

        methods = []
        exports = children_of_type(node, "export_statement")

        for export in exports:
            current_methods = []
            # check for inside methods within the export statement
            current_methods.extend(self.get_fn_in_declarations(export))
            current_methods.extend(self.get_fn_in_expressions(export))

            # check for regular methods within export statement
            current_methods.extend(children_of_type(export, self.method_types))

            # add all the methods found from this export statement to a dictionary
            # mapping the export node to the respective method (similar to self._node2declaration)
            for method in current_methods:
                self._node2export[(method.start_byte, method.end_byte)] = export

            methods.extend(current_methods)

        return methods

    def get_inside_method(self, node):
        """
        Call functions to extract methods defined inside declarations, expression statements and export statements.
        """
        methods = []

        methods.extend(self.get_fn_in_declarations(node))
        methods.extend(self.get_fn_in_expressions(node))
        methods.extend(self.get_fn_in_exports(node))

        return methods

    def get_class_in_declaration(self, node):
        classes = []
        declarations = children_of_type(node, self.declaration_types)
        for declaration in declarations:
            # check if it is a variable_declarator node whose value is a function
            declarators = children_of_type(declaration, "variable_declarator")
            if len(declarators) > 0:
                declarator = declarators[0]
            else:
                continue
            value_node = declarator.child_by_field_name("value")
            if not value_node:
                continue
            if value_node.type in self.class_types:
                classes.append(value_node)
                self._node2declaration[(value_node.start_byte, value_node.end_byte)] = declaration
            elif value_node.type in ["parenthesized_expression"] and len(value_node.children) > 0:
                for class_def in children_of_type(value_node, self.class_types):
                    classes.append(class_def)
                    self._node2declaration[(class_def.start_byte, class_def.end_byte)] = declaration

        return classes

    def get_inside_class(self, node):
        """
        Extract classes defined inside declarations.
        """
        classes = []
        declaration_classes = self.get_class_in_declaration(node)
        classes.extend(declaration_classes)

        exports = children_of_type(node, "export_statement")

        for export in exports:
            exported_classes = []
            exported_classes.extend(self.get_class_in_declaration(export))
            exported_classes.extend(children_of_type(export, self.class_types))

            for exported_class in exported_classes:
                self._node2export[(exported_class.start_byte, exported_class.end_byte)] = export

            classes.extend(exported_classes)

        return classes

    def _extract_class_definition(self, class_node):
        """
        Extract class definition
        """
        definition = []
        start_index = 0
        param_index = 1
        for i, child in enumerate(class_node.children):
            if child.type == "class_heritage":
                param_index = i
                break
        sig = self.span_select(*class_node.children[start_index:param_index + 1])
        definition.append(sig)

        return "\n".join(definition)

    @property
    def method_nodes(self):
        """
        List of top-level child nodes corresponding to methods and methods defined as variable declarations.
        Expect that `self.parse_method_node` will be run on these.
        """
        methods = children_of_type(self.tree.root_node, self.method_types)
        methods.extend(self.get_inside_method(self.tree.root_node))
        return sorted([m for m in methods if len(m.children) > 0], key=lambda x: x.start_byte)

    @property
    def class_nodes(self):
        """
        List of top-level child nodes corresponding to classes and classes define as variable declarations.
        Expect that `self.parse_class_node` will be run on these.
        """
        classes = children_of_type(self.tree.root_node, self.class_types)
        classes.extend(self.get_inside_class(self.tree.root_node))
        return sorted([cs for cs in classes if len(cs.children) > 0], key=lambda x: x.start_byte)

    @property
    def file_docstring(self):
        """
        Retrieve the file_docstring from the file using the parse tree
        In many style guides, the file docstring should be one multi-line comment.
        However, after looking through JavaScript files, sometimes the file
        docstring is made of multiple one-line comments. This function takes care
        of both cases.
        Returns
        -------
        str
            the literal file docstring characters
        """
        docstring_nodes = []
        root_children = self.tree.root_node.children
        if root_children:
            previous_child = root_children[0]
        else:
            return ""
        # if the first node is not a comment, there is no file docstring
        if previous_child.type == "comment":
            docstring = self.span_select(previous_child, indent=False)
            # if first comment is a multiline comment, it is the file docstring
            if docstring[1] == "*":
                return strip_c_style_comment_delimiters(docstring)
            for child in root_children:
                if (
                    child.type == "comment"
                    and previous_child.type == "comment"
                    and (child.start_point[0] - previous_child.end_point[0]) <= 1
                ):
                    docstring_nodes.append(child)
                    previous_child = child
        return strip_c_style_comment_delimiters(
            self.span_select(*docstring_nodes, indent=False)
        )

    @property
    def file_context(self):
        """List of global import"""
        context = []
        for child in self.tree.root_node.children:
            if child.type in self.import_types:
                context.append(self.span_select(child, indent=False))
        return context

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
                'original_string_normed':
                    'code of whole method with string-literal, numeral normalization',
                'signature_normed': 'signature with string-literals/numerals normalized',
                'body_normed': 'code of body with string-literals/numerals normalized',
                'default_arguments': ['arg1': 'default value 1', ...],
                'syntax_pass': 'True/False whether the method is syntactically correct',
                'attributes': [
                        'language_specific_keys': 'language_specific_values',
                    ],
            }
        """
        msg = f"method_node is type {method_node.type}, requires types {self.method_types} and {self.inside_method_types}"
        assert method_node.type in self.method_types + self.inside_method_types, msg
        return self._parse_method_node(method_node)

    def _parse_method_node(self, method_node, parent_node=None):
        """
        See LanguageParser.parse_method_node for documentation
        added default parameter because for methods outside of classes,
        the root node of self.tree is used, for methods inside of classes,
        the parent_node that needs to be used has the type of class body
        """

        method_root_node = None
        if (method_node.start_byte, method_node.end_byte) in self._node2declaration:
            method_root_node = self._node2declaration[(method_node.start_byte, method_node.end_byte)]

        if (method_node.start_byte, method_node.end_byte) in self._node2export:
            method_root_node = self._node2export[(method_node.start_byte, method_node.end_byte)]

        signature, default_arguments = self.get_signature_default_args(
            method_root_node or method_node
        )
        results = {
            "original_string": self.span_select(method_node, indent=False),
            "byte_span": (method_node.start_byte, method_node.end_byte),
            "start_point": (self.starting_point + method_node.start_point[0], method_node.start_point[1]),
            "end_point": (self.starting_point + method_node.end_point[0], method_node.end_point[1]),
            "signature": signature,
            "default_arguments": default_arguments,
            "body": self.span_select(
                self.get_first_child_of_type(method_node, type_string=self.function_body_types),
                indent=False,
            ),
            "attributes": {},
        }
        if method_root_node:
            results["original_string"] = method_root_node.text.decode("utf-8")

        name_node = method_node.child_by_field_name("name")
        if (method_node.start_byte, method_node.end_byte) in self._node2name:
            name = self._node2name[(method_node.start_byte, method_node.end_byte)]
        elif name_node:
            name = self.span_select(name_node, indent=False)
        else:
            name = ""
        results["name"] = name

        children_types = list(map(lambda x: x.type, method_node.children))
        num_decorators = children_types.count('decorator')  # decorators come first
        name_idx = -1
        for i, typ in enumerate(children_types):
            if typ in self._name_types:
                name_idx = i
                break

        if num_decorators:
            results["attributes"]["decorators"] = [
                self.span_select(decorator_node, indent=False)
                for decorator_node in method_node.children[:num_decorators]
            ]
        if name_idx > num_decorators:  # keywords between them!
            results["attributes"]["keywords"] = self.span_select(
                *method_node.children[num_decorators:name_idx],
                indent=False
            )
        if results["name"] == "" and name_idx > 0:
            results["name"] = self.span_select(
                method_node.children[name_idx], indent=False
            )

        results["docstring"] = self.get_docstring(
            parent_node or self.tree.root_node, node_to_compare=method_root_node or method_node
        )

        body_node = method_node.child_by_field_name("body")
        methods = (
            [
                self._parse_method_node(c, body_node)
                for c in sorted(children_of_type(body_node, self.method_types) + self.get_inside_method(body_node), key=lambda x: x.start_byte)
            ]
            if body_node
            else []
        )
        if methods:
            results["methods"] = methods

        try:
            results["syntax_pass"] = has_correct_syntax(method_node)
        except RecursionError:
            results["syntax_pass"] = False

        return results

    def _parse_class_node(self, class_node):
        """See LanguageParser.parse_class_node for documentation"""

        class_root_node = None
        if (class_node.start_byte, class_node.end_byte) in self._node2declaration:
            class_root_node = self._node2declaration[(class_node.start_byte, class_node.end_byte)]
        if (class_node.start_byte, class_node.end_byte) in self._node2export:
            class_root_node = self._node2export[(class_node.start_byte, class_node.end_byte)]

        results = {
            "original_string": self.span_select(class_node, indent=False),
            "definition": self._extract_class_definition(class_node),
            "byte_span": (class_node.start_byte, class_node.end_byte),
            "start_point": (self.starting_point + class_node.start_point[0], class_node.start_point[1]),
            "end_point": (self.starting_point + class_node.end_point[0], class_node.end_point[1]),
            "class_docstring": self.get_docstring(
                parent_node=self.tree.root_node,
                node_to_compare=class_root_node or class_node
            ),
            "attributes": {},
        }

        # only update this for exported nodes. I think we should be doing it for declaration nodes as well,
        # but I don't want to change the functionality too much...
        if (class_node.start_byte, class_node.end_byte) in self._node2export:
            results['original_string'] = self.span_select(class_root_node, indent=False)
        # if class_root_node:
        #     results['original_string'] = self.span_select(class_root_node, indent=False)

        name_node = class_node.child_by_field_name("name")
        results["name"] = (
            self.span_select(name_node, indent=False) if name_node else ""
        )
        if class_root_node and results["name"] == "":
            declarator = children_of_type(class_root_node, "variable_declarator")[0]
            name_node = declarator.child_by_field_name("name")
            results["name"] = (
                self.span_select(name_node, indent=False) if name_node else ""
            )
        results["attributes"]["decorators"] = [
            self.span_select(decorator_node, indent=False)
            for decorator_node in children_of_type(class_node, "decorator")
        ]
        results["attributes"]["heritage"] = [
            self.span_select(child, indent=False)
            for child in children_of_type(class_node, "class_heritage")
        ]
        results["attributes"]["expression"] = [
            self.span_select(child, indent=False)
            for child in children_of_type(
                class_node.children[-1], "public_field_definition"
            )
        ]

        try:
            results["syntax_pass"] = has_correct_syntax(class_node)
        except RecursionError:
            results["syntax_pass"] = False

        class_method_nodes = []
        for child in class_node.children:
            if child.type == "class_body":
                class_body = child
                for grand_child in class_body.children:
                    if grand_child.type == "method_definition":
                        class_method_nodes.append(grand_child)

        parent_node = self.get_first_child_of_type(class_node, type_string="class_body")
        list_of_class_methods_d = []
        for method_node in class_method_nodes:
            class_method_info = self._parse_method_node(method_node, parent_node)
            list_of_class_methods_d.append(class_method_info)
        results["methods"] = list_of_class_methods_d
        return results

    def get_docstring(self, parent_node, node_to_compare):
        """
        Go to the previous sibling of ..._node in the tree,
        and that should be the method/class/class_method docstring
        Parameters
        ----------
        parent_node : tree-sitter Node
            the parent of the node the docstring is related to
            if we are getting a class docstring, then parent is the
            parent of the "class_declaration" tree-sitter node
            <Node kind=, start_point=(*,*), end_point=(*,*)>
            kind will depend upon node_to_compare
        node_to_compare : tree-sitter Node
            <Node kind=, start_point=(*,*), end_point=(*,*)>
        Returns
        -------
        string
            literal string of docstring if present
            otherwise: empty string
        """
        if node_to_compare.parent.type == "export_statement":
            parent_node = node_to_compare.parent
        location = parent_node.children.index(node_to_compare)
        if (
            location > 0
            and parent_node.children[location - 1].type == "comment"
            and not nodes_are_equal(
                parent_node.children[location - 1], self.tree.root_node.children[0]
            )
        ):
            return strip_c_style_comment_delimiters(
                self.span_select(parent_node.children[location - 1], indent=False)
            )
        # there was no docstring
        return ""

    # def get_docstring(self, parent_node, node_to_compare=None):
    #     if parent_node.prev_sibling and parent_node.prev_sibling.type in self._docstring_types:
    #         return strip_c_style_comment_delimiters(self.span_select(parent_node.prev_sibling, indent=False))
    #     return ""

    def get_signature_default_args(self, method_node):
        """
        Parameters
        ----------
        class_function_node or method_node: tree-sitter
            <Node kind=method_definition, start_point=(*,*), end_point=(*,*)>
        Returns
        -------
        signature : str
            the signature of method_node

        default_params: dict
            default params of method_node
        """
        default_params = {}
        signature_nodes = self.tree_recurse(method_node, default_params)[0]

        signature = self.span_select(*signature_nodes, indent=False).replace("=>", "").strip()
        return signature, default_params

    # dfs to get the signature nodes

    def tree_recurse(self, root_node, default_params):
        """
        Recursive DFS to go through all nodes of the method
        and get all the leaves up until the function body

        Parameters
        ---------------
        root_node : tree_sitter Node
            Node to begin recursion (depends on type of function instantiation)
        default_params: dict
            dictionary mapping parameter names & types -> values
        Returns
        ---------------
        leaf_nodes: the leaf nodes of the traversed portion of the tree
        end_found: bool: whether the branch on which to end recursion was reached
        """
        leaf_nodes = []
        if not root_node.children:
            return ([root_node], False)

        body_node = root_node.child_by_field_name("body")
        for child in root_node.children:

            # if we've reached a body node, set signal to stop recursion
            if body_node == child:
                return (leaf_nodes, True)

            # find and return the default parameters
            if child.type == "required_parameter":
                self.get_default_params(child, default_params)

            # else, keep collecting leaf nodes
            new_leaves, end_found = self.tree_recurse(child, default_params)
            leaf_nodes.extend(new_leaves)
            if end_found:
                return (leaf_nodes, end_found)

        # return all leaf nodes collected
        return (leaf_nodes, False)

    def get_default_params(self, param_node, default_param_dict):
        """
        Iterate through the children of the required_parameter node
        to find all the information for the parameters of the function
        being parsed

        Parameters
        -----------------
        param_node: tree_sitter Node of type 'required_parameter'
        default_param_dict: dict
            dictionary mapping parameter names & types -> values

        Returns
        -----------------
        None (updates default_param_dict in place) 
        """
        type_key = ""
        key = ""
        value = ""
        for child in param_node.children:
            if child.type == "identifier":
                key = self.span_select(child, indent=False)
            elif child.type == "type_annotation":
                type_key = self.span_select(child, indent=False)
            else:
                value = self.span_select(child, indent=False)

        default_param_dict[key + type_key] = value
