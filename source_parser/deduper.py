# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
deduper.py

This module contains two classes to be used for finding near
duplicates in a corpus.

Examples
--------

Usage example of Deduper:

>>> train_data = [["X", "2", "3", "4", "5", "6", "7", "8", "9"],
...             ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
...             ["A", "B", "C", "1"]]
>>> test_data = [
...         ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
...         ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
...         ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
...         ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
...       ]
>>> deduper = Deduper()
>>> deduped = []
>>> for d in train_data:
>>>     deduper.add(d)
>>> for d in test_data:
>>>     if deduper.query(d) is False:
>>>         deduper.add(d)
>>>         deduped.append(d)
>>> print(deduped)
[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']]

Another example of Deduper:

The above example stores training data as reference set and query over test data to find duplicates in test data against training.
Sometimes the training data could be very large and storing training data can lead to OOM. 
The following snippets also find duplicates in test data against training, but save memory by storing test data as reference set instead.

>>> deduper = Deduper(record_duplicates=True, get_key_func=your_hash_function)
>>> deduped = []
>>> for d in test_data:
>>>     deduper.add(d)
>>> for d in train_data:
>>>     deduper.query(d)
>>> duplicated_keys = deduper.keys_of_duplicates()
>>> # loop over test data again to save only non-duplicate data
>>> all_test_keys = set()
>>> for d in test_data:
>>>     key = get_key_from_token_list(d)
>>>     if key in all_test_keys:
>>>         continue
>>>     else:
>>>         all_test_keys.add(key)
>>>     if key not in duplicated_keys:
>>>         deduped.append(d)
>>> print(deduped)
[['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']]

Usage example of CodeDeduper:

>>> train_data = [
...             "def g():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
...             "def f():\n z+=3 + 4\n return z - 1",
...         ]
>>> test_data = [
...            "def g():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
...             "def f():\n x=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
...             "def g():\n VAR=1\n y=2\n z+=3\n a+=4\n b+=5\n c+=6\n return x+y",
...             "def g():\n x=1\n y=2\n return x+y+10",
...         ]
>>> deduper = CodeDeduper(language= "python")
>>> deduped = []
>>> for d in train_data:
>>>     deduper.add(d)
>>> for d in test_data:
>>>     if deduper.query(d) is False:
>>>         deduper.add(d)
>>>         deduped.append(d)
>>> print(deduped)
['def g():\n x=1\n y=2\n return x+y+10']
"""
from collections import Counter
from datasketch import MinHash, MinHashLSH

from tree_sitter import Parser
from source_parser.utils import tokenize
from source_parser.tree_sitter import get_language, LanguageId, lang2lits

# pylint: disable=too-many-instance-attributes


class Deduper:
    """
    Detect approximate duplicates in a list of lists of strings.
    """

    def __init__(self, threshold=0.8, num_perm=128, weights=(0.5, 0.5), record_duplicates=False, get_key_func=None):
        """
        Initialize Deduper.

        Parameters
        ----------
        threshold: float, optional
            Duplicates are defined as sets with Jaccard similarity greater than threshold.
        num_perm: int, optional
            See documentation of MinHashLSH.
        weights:  tuple, optional
            See documentation of MinHashLSH.
        record_duplicates: True/False
            Whether to remember the keys of all duplicates in the reference dataset.
        get_key_func: function takes input a list of tokens, and output a string as key, optional
            A function that map data points to keys. If None, then use the index as key.
        """
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm, weights=weights)
        self.idx = 0
        self.m = MinHash(num_perm=self.num_perm)
        self.record_duplicates = record_duplicates
        self.get_key_func = get_key_func
        self.duplicates_keys = set()

    def add(self, d, new_hash=True):
        """
        Add a single example or a list of examples.

        Parameters
        ---------
        new_hash: True/False
            Should this datapoint by minhashed from scratch?
            Set to False if the datapoint was
            already queried.
        """
        if new_hash:
            self.m.clear()
            for t in d:
                self.m.update(t.encode("utf8"))
        if self.get_key_func is not None:
            self.lsh.insert(self.get_key_func(d), self.m, check_duplication=False)
        else:
            self.lsh.insert(self.idx, self.m)
        self.idx += 1

    def query(self, d):
        """Check if an example is a duplicate."""
        self.m.clear()
        for t in d:
            self.m.update(t.encode("utf8"))
        candidates = self.lsh.query(self.m)
        if len(candidates) > 0:
            if self.record_duplicates:
                for cand in candidates:
                    self.duplicates_keys.add(cand)
            return True
        return False

    def keys_of_duplicates(self):
        """Return set of keys of duplicates."""
        return self.duplicates_keys


class CodeDeduper:
    """
    Detect approximate duplicates in a collection of code strings.

    Notes
    -----
    Following [1], this class defines two fingerprints for each piece of code:
    a set and a multiset of the literals and identifiers. It finds examples
    that are similar in both fingerprints.

    References
    ----------
    [1] Miltiadis Allamanis. The adverse effects of code duplication in machine
    learning models of code. In Proceedings of the 2019 ACM SIGPLAN
    International Symposium on New Ideas, New Paradigms, and
    Reflections on Programming and Software, pp. 143–153, 2019.
    """

    def __init__(
        self,
        language,
        threshold_set=0.8,
        threshold_mset=0.7,
        num_perm=128,
        weights=(0.5, 0.5),
    ):
        """
        Initialize CodeDeduper.

        Parameters
        ----------
        language: string
            The code input language.
        threshold_set: float, optional
            Threshold of Jaccard similarity for detecting clones
            between the set fingerprint.
        threshold_mset: float, optional
            Threshold of Jaccard similarity for detecting clones
            between the multiset fingerprint.
        num_perm: int, optional
            See documentation of MinHashLSH.
        weights: tuple, optional
            See documentation of MinHashLSH.
        """
        self.threshold_set = threshold_set
        self.threshold_mset = threshold_mset
        self.num_perm = num_perm
        self.lsh_set = MinHashLSH(
            threshold=threshold_set, num_perm=num_perm, weights=weights
        )
        self.lsh_mset = MinHashLSH(
            threshold=threshold_mset, num_perm=num_perm, weights=weights
        )
        self.parser = Parser()
        self.parser.set_language(get_language(language.lower()))
        self.literals = [
            item
            for sublist in lang2lits[LanguageId[language.upper()]]
            for item in sublist
        ]
        self._idx = 0
        self.m_set = MinHash(num_perm=self.num_perm)
        self.m_mset = MinHash(num_perm=self.num_perm)

    def add(self, d, new_hash=True):
        """
        Add a single example or a list of examples.

        Parameters
        ---------
        new_hash: True/False
            Should this datapoint by minhashed from scratch?
            Set to False if the datapoint was
            already queried.
        """
        tokens = self._process_data(d)
        tokens_mset = [t + str(Counter(tokens)[t]) for t in tokens]
        if new_hash:
            self.m_set.clear()
            self.m_mset.clear()
            for t in tokens:
                self.m_set.update(t.encode("utf8"))
            for t in tokens_mset:
                self.m_mset.update(t.encode("utf8"))
        self.lsh_set.insert(self._idx, self.m_set)
        self.lsh_mset.insert(self._idx, self.m_mset)
        self._idx += 1

    def query(self, d):
        """Check if an example is a duplicate."""
        tokens = self._process_data(d)
        tokens_mset = [t + str(Counter(tokens)[t]) for t in tokens]
        self.m_set.clear()
        self.m_mset.clear()
        for t in tokens:
            self.m_set.update(t.encode("utf8"))
        for t in tokens_mset:
            self.m_mset.update(t.encode("utf8"))
        return len(set(self.lsh_set.query(self.m_set)) & set(self.lsh_mset.query(self.m_mset))) > 0

    def _process_data(self, d):
        """Tokenize code string and return only identifiers and literals."""
        file_bytes = d.encode("utf8")
        root_node = self.parser.parse(file_bytes).root_node
        tokens, types = tokenize(file_bytes, root_node, whitespace=False)
        return [
            tokens[i]
            for i in range(len(tokens))
            if types[i] in self.literals or "identifier" in types[i]
        ]
# pylint: enable=too-many-instance-attributes
