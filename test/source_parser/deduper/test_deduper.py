# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.deduper import Deduper, CodeDeduper


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            ],
            [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            ],
        ),
        (
            [
                ["XXX", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
                ["a", "XXX", "c", "d", "e", "f", "g", "h", "i"],
            ],
            [
                ["XXX", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            ],
        ),
        (
            [
                ["XXX", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
                ["a", "XXX", "c", "d", "e", "f", "g", "h", "i"] * 100,
            ],
            [
                ["XXX", "2", "3", "4", "5", "6", "7", "8", "9"],
                ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            ],
        ),
    ],
)
def test_Deduper(test_input, expected):
    deduper = Deduper()
    deduped = []
    for d in test_input:
        if not deduper.query(d):
            deduper.add(d)
            deduped.append(d)
    assert deduped == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            [
                "def g():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
                "def f():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
                "def g():\n VAR=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
                "def g():\n x=1\n y=2\n return x+y+10",
            ],
            [
                'def g():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y',
                'def g():\n x=1\n y=2\n return x+y+10',
            ],
        ),
    ],
)
def test_CodeDeduper(test_input, expected):
    deduper = CodeDeduper(language="python")
    deduped = []
    for d in test_input:
        if not deduper.query(d):
            deduper.add(d)
            deduped.append(d)
    assert deduped == expected
