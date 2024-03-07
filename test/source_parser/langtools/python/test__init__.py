# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.langtools.python import check_python3_attempt_fix


@pytest.mark.parametrize("test_input,expected",
        [
            ("print 1\n", "print(1)\n"),
            ("  print(1)\n", "print(1)\n"),
            ("  print 1\n", "print(1)\n"),
        ]
)

def test_python3_attempt_fix(test_input, expected):
    assert check_python3_attempt_fix(test_input) == expected
