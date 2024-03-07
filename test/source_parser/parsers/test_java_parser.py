# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.parsers.java_parser import JavaParser

DIR = "test/assets/java_examples/"


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "AwBrowserContext.java",
            """ Copyright (c) 2013 The Chromium Authors. All rights reserved.""",
        ),
        (DIR + "ExampleUnitTest.java", ""),
        (
            DIR + "TrickyFileComment.java",
            """\nThis is a file comment\n""",
        ),
    ],
)
def test_file_docstring(source, target):
    with open(source, "r") as f:
        jp = JavaParser(f.read())
        assert jp.file_docstring == target


def test_classes_ClassExamples():

    source = DIR + "/ClassExamples.java"
    with open(source, "r") as f:
        jp = JavaParser(f.read())

        class_dict_list = [
            jp._parse_class_node(class_node) for class_node in jp.class_nodes
        ]

        class_1, class_2 = class_dict_list
        assert (
            class_1["original_string"]
            == """public class ClassExample1 {

    /*
     * fields can have javadoc
     */
    private int a;
    private ArrayList<Integer> b;

    public ClassExample1(int a, int c) {
        self.a = a;
    }

    /**
     * This is a function.
     * it does something.
     */
    public void returnA() {
        return self.a;
    }

    /**
     * nested class should be ignored by the parser
     */
    private class InnerClass{
        private int b;
        public InnerClass(int b){
            self.b = b
        }
    }

}"""
        )
        assert (
            class_1["class_docstring"]
            == """
This is Javadoc for ClassExample1

"""
        )
        assert class_1["attributes"]["modifiers"] == "public"

        # print(class_1["name"])
        assert class_1["name"] == "ClassExample1"

        assert class_1["start_point"] == (12, 0)

        assert class_1["end_point"] == (42, 1)

        class_1_field_1, class_1_field_2 = class_1["attributes"]["fields"]

        # print(class_1_field_1.keys())
        # dict_keys(['original_str', 'doc', 'modifiers', 'type', 'name'])
        # print(class_1_field_1)
        assert class_1_field_1["attribute_expression"] == "    private int a;"
        assert (
            class_1_field_1["docstring"]
            == "\nfields can have javadoc\n"
        )
        assert class_1_field_1["modifiers"] == "private"
        assert class_1_field_1["type"] == "int"
        assert class_1_field_1["name"] == "a"

        # print(class_1_field_2)
        assert class_1_field_2["attribute_expression"] == "    private ArrayList<Integer> b;"
        assert class_1_field_2["docstring"] == ""
        assert class_1_field_2["modifiers"] == "private"
        assert class_1_field_2["type"] == "ArrayList<Integer>"
        assert class_1_field_2["name"] == "b"

        # print(class_1)
        class_1_method_1, class_1_method_2 = class_1["methods"]

        # the constructor
        # print(class_1_method_1)
        assert (
            class_1_method_1["original_string"]
            == "    public ClassExample1(int a, int c) {\n        self.a = a;\n    }"
        )
        assert class_1_method_1["docstring"] == ""
        assert class_1_method_1["attributes"]["modifiers"] == "public"
        assert class_1_method_1["attributes"]["return_type"] == ""
        assert class_1_method_1["name"] == "ClassExample1"
        assert class_1_method_1["body"] == "                                       {\n        self.a = a;\n    }"
        assert class_1_method_1["start_point"] == (20, 4)
        assert class_1_method_1["end_point"] == (22, 5)

        # print(class_1_method_2)
        assert (
            class_1_method_2["original_string"]
            == "    public void returnA() {\n        return self.a;\n    }"
        )
        assert (
            class_1_method_2["docstring"]
            == "\nThis is a function.\nit does something.\n"
        )
        assert class_1_method_2["attributes"]["modifiers"] == "public"
        assert class_1_method_2["attributes"]["return_type"] == "void"
        assert class_1_method_2["name"] == "returnA"
        assert class_1_method_2["body"] == "                          {\n        return self.a;\n    }"
        assert class_1_method_2["start_point"] == (28, 4)
        assert class_1_method_2["end_point"] == (30, 5)

        # class_1_fields = class_1["fields"]

        # print("===\n")
        # print(class_2["original_string"])
        assert (
            class_2["original_string"]
            == """class AnotherClass {
    private int a;

    /**
     * this is a constructor
     */
    public AnotherClass(int a) {
        self.a = a;
    }
}"""
        )
        assert class_2["class_docstring"] == ""
        assert class_2["attributes"]["modifiers"] == ""

        assert class_2["name"] == "AnotherClass"

        assert class_2["start_point"] == (44, 0)

        assert class_2["end_point"] == (53, 1)

        (class_2_field_1,) = class_2["attributes"]["fields"]
        assert class_2_field_1["attribute_expression"] == "    private int a;"
        assert class_2_field_1["docstring"] == ""
        assert class_2_field_1["modifiers"] == "private"
        assert class_2_field_1["type"] == "int"
        assert class_2_field_1["name"] == "a"

        (class_2_method_1,) = class_2["methods"]
        # print(class_2_method_1)
        assert (
            class_2_method_1["original_string"]
            == "    public AnotherClass(int a) {\n        self.a = a;\n    }"
        )
        print(class_2_method_1["docstring"])
        assert (
            class_2_method_1["docstring"]
            == """\nthis is a constructor\n"""
        )  # NOTE: first indentation is NOT included, but following indentations ARE included
        assert class_2_method_1["attributes"]["modifiers"] == "public"
        assert class_2_method_1["attributes"]["return_type"] == ""
        assert class_2_method_1["name"] == "AnotherClass"
        assert class_2_method_1["body"] == "                               {\n        self.a = a;\n    }"
        assert class_2_method_1["start_point"] == (50, 4)
        assert class_2_method_1["end_point"] == (52, 5)


def test_MinimalExample():

    source = DIR + "/MinimalExample.java"
    with open(source, "r") as f:
        jp = JavaParser(f.read())

        class_dict_list = [
            jp._parse_class_node(class_node) for class_node in jp.class_nodes
        ]

        # pprint(class_dict_list)
        # print(class_dict_list)
        assert class_dict_list == [
            {
                "original_string": '@MyMarkerNotation\npublic class Class1 {\n\n    /*\n     * Field javadoc\n     */\n    private int a;\n\n    public Class1(int a) {\n        self.a = a;\n    }\n\n    // A function\n    public int returnA() {\n        return self.a;\n    }\n\n    @Marker\n    public static void printHi() {\n        System.out.println("Hi");\n    } \n    \n}',
                "byte_span": (172, 492),
                "start_point": (8, 0),
                "end_point": (30, 1),
                "class_docstring": "\nClass1 javadoc\n",
                "definition": "@MyMarkerNotation\npublic class Class1",
                "name": "Class1",
                "attributes": {
                    "modifiers": "@MyMarkerNotation\npublic",
                    "marker_annotations": ["@MyMarkerNotation"],
                    "non_marker_annotations": ["public"],
                    "comments": [],
                    "fields": [
                        {
                            "attribute_expression": "    private int a;",
                            "docstring": "\nField javadoc\n",
                            "modifiers": "private",
                            "marker_annotations": [],
                            "non_marker_annotations": ["private"],
                            "comments": [],
                            "type": "int",
                            "name": "a",
                            "syntax_pass": True,
                        }
                    ],
                    "classes": [],
                },
                "syntax_pass": True,
                "methods": [
                    {
                        "original_string": "    public Class1(int a) {\n        self.a = a;\n    }",
                        "docstring": "",
                        "attributes": {
                            "modifiers": "public",
                            "marker_annotations": [],
                            "non_marker_annotations": ["public"],
                            "comments": [],
                            "return_type": "",
                            "classes": [],
                        },
                        "name": "Class1",
                        "body": "                         {\n        self.a = a;\n    }",
                        "byte_span": (273, 321),
                        "start_point": (16, 4),
                        "end_point": (18, 5),
                        "signature": "    public Class1(int a)",
                        "syntax_pass": True,
                    },
                    {
                        "original_string": "    public int returnA() {\n        return self.a;\n    }",
                        "docstring": " A function",
                        "attributes": {
                            "modifiers": "public",
                            "marker_annotations": [],
                            "non_marker_annotations": ["public"],
                            "comments": [],
                            "return_type": "int",
                            "classes": [],
                        },
                        "name": "returnA",
                        "body": "                         {\n        return self.a;\n    }",
                        "byte_span": (345, 396),
                        "start_point": (21, 4),
                        "end_point": (23, 5),
                        "signature": "    public int returnA()",
                        "syntax_pass": True,
                    },
                    {
                        "original_string": '    @Marker\n    public static void printHi() {\n        System.out.println("Hi");\n    }',
                        "docstring": "",
                        "attributes": {
                            "modifiers": "@Marker\n    public static",
                            "marker_annotations": ["@Marker"],
                            "non_marker_annotations": ["public", "static"],
                            "comments": [],
                            "return_type": "void",
                            "classes": [],
                        },
                        "name": "printHi",
                        "body": '                                 {\n        System.out.println("Hi");\n    }',
                        "byte_span": (402, 484),
                        "start_point": (25, 4),
                        "end_point": (28, 5),
                        "signature": "    @Marker\n    public static void printHi()",
                        "syntax_pass": True,
                    },
                ],
            }
        ]


def test_NestedClassExample():

    source = DIR + "/NestedClassExample.java"
    with open(source, "r") as f:
        jp = JavaParser(f.read())

        class_dict_list = [
            jp._parse_class_node(class_node) for class_node in jp.class_nodes
        ]

        assert class_dict_list[0]["attributes"]["classes"][0]["name"] == "nested"
        assert (
            class_dict_list[0]["methods"][0]["attributes"]["classes"][0]["name"]
            == "Local"
        )
