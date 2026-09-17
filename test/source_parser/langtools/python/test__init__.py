# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import ast

import pytest
from source_parser.langtools.python import check_python3_attempt_fix, fix2to3


@pytest.mark.parametrize("test_input,expected",
        [
            ("print 1\n", "print(1)\n"),
            ("  print(1)\n", "print(1)\n"),
            ("  print 1\n", "print(1)\n"),
        ]
)

def test_python3_attempt_fix(test_input, expected):
    assert check_python3_attempt_fix(test_input) == expected


def test_conversion_preserves_missing_final_newline():
    assert fix2to3("print 'hello'") == "print('hello')"


def test_python2_exception_conversion():
    source = "try:\n    pass\nexcept ValueError, error:\n    print error\n"
    converted = check_python3_attempt_fix(source)

    ast.parse(converted)
    assert "except ValueError as error:" in converted
    assert "print(error)" in converted


def test_modern_python_bypasses_legacy_conversion():
    source = "match value:\n    case 1:\n        print('one')\n"

    assert check_python3_attempt_fix(source) == source
