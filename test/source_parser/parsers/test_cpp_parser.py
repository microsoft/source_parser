# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.parsers import CppParser

DIR = "test/assets/cpp_examples/"


def create_cpp_parser(source):
    with open(source, 'r', encoding='utf-8') as file:
        cp = CppParser(file.read())
    return cp


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "ComplexClass.cpp",
            """Written by celbree""",
        ),
        (
            DIR + "ConstructorFunction.cpp",
            """This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.""",
        ),
        (
            DIR + "SimpleClass.cpp",
            "",
        ),
    ],
)
def test_file_docstring(source, target):
    cp = create_cpp_parser(source)
    assert cp.schema["file_docstring"] == target


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "InNamespaces.cpp",
            [
                "#include <iostream>",
                "#include <vector>",
                "#include \"hi.h\"",
                "#define pi 3.1415",
            ],
        ),
        (
            DIR + "SimpleClass.cpp",
            [
                "#Using <system.dll>"
            ],
        ),
    ],
)
def test_context(source, target):
    cp = create_cpp_parser(source)
    assert cp.schema["contexts"] == target


def test_classes():
    source = DIR + "ComplexClass.cpp"
    cp = create_cpp_parser(source)

    classes = cp.schema['classes']
    assert len(classes) == 1

    cl = classes[0]

    assert cl["original_string"] == """class FirstClass{
public:
    vector<int> x;
    // a variable
    inline int y;
    FirstClass(int x): x(x) {}
    bool func(const vector<double>& values);
    static int static_func(int a=0){
        return a;
    }
private:
    auto at;
    /*
     * a private member function
     */
    vector<int> private_func(int i, int j) const{
        vector<int> v;
        v.push_back(i);
        return v;
    }
}"""

    assert cl["docstring"] == "This is the first class"

    assert cl["name"] == "FirstClass"

    assert cl["body"] == """{
public:
    vector<int> x;
    // a variable
    inline int y;
    FirstClass(int x): x(x) {}
    bool func(const vector<double>& values);
    static int static_func(int a=0){
        return a;
    }
private:
    auto at;
    /*
     * a private member function
     */
    vector<int> private_func(int i, int j) const{
        vector<int> v;
        v.push_back(i);
        return v;
    }
}"""

    assert cl["start_point"] == (7, 0)

    assert cl["end_point"] == (27, 1)

    f1, f2, f3, f4 = cl["attributes"]["fields"]

    assert f1["original_string"] == """vector<int> x;"""
    assert f1["type"] == "vector<int>"
    assert f1["annotations"] == ["public"]

    assert f2["original_string"] == """inline int y;"""
    assert f2["type"] == "int"
    assert f2["annotations"] == ["public", "inline"]
    assert f2["docstring"] == "a variable"

    assert f3["original_string"] == """bool func(const vector<double>& values);"""
    assert f3["type"] == "bool"
    assert f3["annotations"] == ["public"]

    assert f4["original_string"] == """auto at;"""
    assert f4["type"] == "auto"
    assert f4["annotations"] == ["private"]


def test_methods():
    source = DIR + "InNamespaces.cpp"
    cp = create_cpp_parser(source)

    m1, m2, m3 = cp.schema['methods']

    assert m1["original_string"] == """int main(){
    return 0;
}"""
    assert m1["signature"] == "int main()"
    assert m1["body"] == """{
    return 0;
}"""
    assert m1["name"] == "main"
    assert m1["attributes"]["return_type"] == "int"
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["start_point"] == (41, 0)
    assert m1["end_point"] == (43, 1)

    assert m2["original_string"] == """bool cmp(const int& a, const int& b) const {
        return a < b;
    }"""
    assert m2["signature"] == "bool cmp(const int& a, const int& b) const"
    assert m2["body"] == """{
        return a < b;
    }"""
    assert m2["name"] == "cmp"
    assert m2["docstring"] == "First cmp"
    assert m2["attributes"]["return_type"] == "bool"
    assert m2["attributes"]["namespace_prefix"] == "first_namespace::"
    assert m2["attributes"]["annotations"] == ["const"]
    assert m2["start_point"] == (11, 4)
    assert m2["end_point"] == (13, 5)

    assert m3["original_string"] == """auto cmp(const int& a, const int& b){
            return a < b;
        }"""
    assert m3["signature"] == "auto cmp(const int& a, const int& b)"
    assert m3["body"] == """{
            return a < b;
        }"""
    assert m3["name"] == "cmp"
    assert m3["docstring"] == "Second cmp"
    assert m3["attributes"]["return_type"] == "auto"
    assert m3["attributes"]["namespace_prefix"] == "first_namespace::second_namespace::"
    assert m3["attributes"]["annotations"] == []
    assert m3["start_point"] == (35, 8)
    assert m3["end_point"] == (37, 9)


def test_wrong_examples():
    source = DIR + "LongList.cpp"
    cp = create_cpp_parser(source)

    m = cp.schema['methods'][0]
    assert m["syntax_pass"] is False


def test_constructor_function():
    source = DIR + "ConstructorFunction.cpp"
    cp = create_cpp_parser(source)

    m1, m2 = cp.schema["methods"]

    assert m1["original_string"] == """ModelConsumer::ModelConsumer(llvm::StringMap<Stmt *> &Bodies)
    : Bodies(Bodies) {}"""
    assert m1["body"] == "{}"
    assert m1["name"] == "ModelConsumer::ModelConsumer"
    assert m1["signature"] == """ModelConsumer::ModelConsumer(llvm::StringMap<Stmt *> &Bodies)
    : Bodies(Bodies)"""
    assert m1["docstring"] == "It's a constructor"
    assert m1["attributes"]["return_type"] == ""
    assert m1["attributes"]["annotations"] == []

    assert m2["original_string"] == """ModelConsumer::~ModelConsumer(void) {}"""
    assert m2["body"] == "{}"
    assert m2["name"] == "ModelConsumer::~ModelConsumer"
    assert m2["signature"] == """ModelConsumer::~ModelConsumer(void)"""
    assert m2["docstring"] == "It's a deconstructor"
    assert m2["attributes"]["return_type"] == ""
    assert m2["attributes"]["annotations"] == []
