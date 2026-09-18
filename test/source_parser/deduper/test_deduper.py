# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import Counter
from unittest.mock import patch

import pytest
from datasketch import MinHash

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
def test_deduper(test_input, expected):
    deduper = Deduper()
    deduped = []
    for d in test_input:
        if not deduper.query(d):
            deduper.add(d)
            deduped.append(d)
    assert deduped == expected


@pytest.mark.parametrize("new_hash", [True, False])
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
def test_code_deduper(test_input, expected, new_hash):
    deduper = CodeDeduper(language="python")
    deduped = []
    for d in test_input:
        if not deduper.query(d):
            deduper.add(d, new_hash=new_hash)
            deduped.append(d)
    assert deduped == expected


@pytest.mark.parametrize("operation", ["add", "query"])
@pytest.mark.parametrize(
    "source",
    [
        "",
        "# only a comment\n",
        "value = 1\nvalue += 1\n" * 10,
        "def f(first, second):\n    return first + second + 42\n",
        "caf\u00e9 = 'snowman: \u2603'\ncaf\u00e9 += 'snowman: \u2603'\n",
    ],
)
def test_code_deduper_preserves_fingerprints(source, operation):
    deduper = CodeDeduper(language="python", num_perm=32)
    tokens = deduper._process_data(source)
    counts = Counter(tokens)
    expected_set = MinHash(num_perm=32)
    expected_mset = MinHash(num_perm=32)
    for token in tokens:
        expected_set.update(token.encode("utf8"))
        expected_mset.update((token + str(counts[token])).encode("utf8"))

    deduper.query("previous = 'fingerprint must be cleared'\n")
    getattr(deduper, operation)(source)

    assert deduper.m_set == expected_set
    assert deduper.m_mset == expected_mset


@pytest.mark.parametrize("operation", ["add", "query"])
def test_code_deduper_counts_tokens_once(operation):
    deduper = CodeDeduper(language="python")
    source = "value = 1\nvalue += 1\n"

    with patch("source_parser.deduper.Counter", wraps=Counter) as counter:
        getattr(deduper, operation)(source)

    counter.assert_called_once()


@pytest.mark.parametrize("operation", ["add", "query"])
def test_code_deduper_hashes_distinct_tokens_once(operation):
    deduper = CodeDeduper(language="python")
    source = "value = 1\nvalue += 1\n"

    with patch.object(deduper.m_set, "update", wraps=deduper.m_set.update) as update_set, \
            patch.object(deduper.m_mset, "update", wraps=deduper.m_mset.update) as update_mset:
        getattr(deduper, operation)(source)

    assert update_set.call_count == 2
    assert update_mset.call_count == 2


def test_code_deduper_reuses_query_without_reparsing():
    deduper = CodeDeduper(language="python")
    source = "def f(value):\n    return value + 1\n"
    assert not deduper.query(source)

    with patch.object(deduper, "_process_data", wraps=deduper._process_data) as process_data:
        deduper.add(source, new_hash=False)

    process_data.assert_not_called()
    assert deduper.query(source)
