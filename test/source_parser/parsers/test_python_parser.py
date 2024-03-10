# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from source_parser.parsers import PythonParser

DIR = "test/assets/python_examples/"


def test_methods():
    source = DIR + "iMath.py"
    with open(source, "r", encoding='utf-8') as f:
        cp = PythonParser(f.read())

        methods = cp.schema["methods"]
        assert len(methods) == 25

        m1 = methods[0]

    assert m1["original_string"] == "def multiply_images(image1, image2):\n    return image1 * image2"
    assert m1["body"] == "    return image1 * image2"
    assert m1["signature"] == "def multiply_images(image1, image2):"
    assert m1["start_point"] == (65, 0)
    assert m1["end_point"] == (66, 26)

    m2 = methods[1]
    assert m2["signature"] == "def iMath(image, operation, *args):"
    assert m2["start_point"] == (69, 0)
    assert m2["end_point"] == (106, 19)
