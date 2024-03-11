# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import string
import signal
import hashlib
import logging
from contextlib import contextmanager

LOGGER = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # turn off alarm


def static_hash(str_tuple):
    """
    hash a tuple of bytes or objects serializable with str, get consistent results across runs
    without the hack of turning off the python hash seed
    """
    sha256 = hashlib.sha256()
    for strn in str_tuple:
        sha256.update(str(strn).encode("utf-8"))
    return sha256.hexdigest()


def tokenize(file_bytes, node, whitespace=True):
    """
    Tokenize the source file_contents represented by node
    and optionally include whitespace to the right of each token

    Parameters
    ----------
    file_bytes: bytes
        Bytes of input string to tokenize
    node: TreeSitter.Node
        Root node of tree_sitter tree returned by parsing file_bytes
    whitespace: True/False
        Should whitespace be included to the right of each token?

    Returns
    -------
    tokens, types: List, List
        a list of token strings and a list of corresponding
        token tree_sitter types
    """
    compound_lits = ("concatenated_string, string_array", "chained_string")
    w_space = set(string.whitespace.encode("utf-8"))

    n_bytes = len(file_bytes)
    tokens, types = [], []
    nodes = node.children
    while nodes:
        nxt = nodes.pop(0)
        if not nxt.children or (
            "string" in str(nxt.type)
            and str(nxt.type) not in compound_lits
            or "char" in str(nxt.type)
        ):
            start, finish = nxt.start_byte, nxt.end_byte
            if whitespace:
                # walk right to include right whitespace in token
                while finish < n_bytes:
                    if not file_bytes[finish] in w_space:
                        break
                    finish += 1

            tok = file_bytes[start:finish].decode("utf-8")
            if not tokens:  # indent first token to maintain relative space
                tok = (" " * nxt.start_point[1]) + tok

            tokens.append(tok)
            types.append(nxt.type)
            continue
        nodes = nxt.children + nodes

    return tokens, types


def strip_comments(parser, node=None):
    """
    Return comment free code corresponding to node

    Parameters
    ----------
    parser: LanguageParser object
        Instantiated and file_contents updated parser object
    node: TreeSitter.Node (optiona)
        default is parser.tree.root_node, if provided only
        the part of the file contents corresponding to node
        is returned

    Returns
    -------
    commentless_code: str
        code corresponding to node or parser.tree.root_node
        which has had comments removed
    """
    tokens, types = tokenize(parser.file_bytes, node or parser.tree.root_node,)
    commentless = []
    for tok, typ in zip(tokens, types):
        if typ == "comment":  # preserve whitespace
            newline_index = tok.index("\n")
            commentless.append(tok[newline_index:])
        else:
            commentless.append(tok)
    return "".join(commentless)
