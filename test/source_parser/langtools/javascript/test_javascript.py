# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
test_javascript.py
Usage :
    tests the is_minified function in javascript.py
"""

import pytest
from pathlib import Path
from source_parser.langtools.javascript import is_minified
from source_parser.parsers import JavascriptParser

DIR = Path("test/assets/javascript_examples")


@pytest.mark.parametrize(
    "source, target",
    [
        ("example1.js", False),
        ("example2.js", False),
        ("example3.js", False),
        ("example4.js", False),
        ("example1.js", False),
        ("example5.js", False),
        ("example6.js", False),
        ("example7.js", False),
        ("example8.js", False),
        ("example9.js", False),
        ("example10.js", False),
        ("Abs.js", False),
        ("AverageMean.js", False),
        ("BinarySearchTree.js", False),
        ("Heap.js", False),
        ("Graph2.js", False),
        ("KadaneAlgo.js", False),
        ("SHA1.js", False),
        ("SHA256.js", False),
        ("example8min.js", True),
        ("Kadanemin.js", True),
        ("Queuemin.js", True),
        ("SHA1min.js", True),
        ("example10min.js", True),
        ("example6min.js", True),
        ("jquerydata.js", True),
        ("sparkline.js", True)
    ]
)
def test_is_minified(source, target):
    print("Filename: ", DIR / source)
    answer = is_minified(JavascriptParser(open(DIR / source).read()))
    print(answer)
    print("target")
    print(target)
    assert answer == target
