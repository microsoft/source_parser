# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
javascript.py
Contains functions that find and strip license of file content string
Contains function that checks to see if file is minified

Usage:
    to be used to filter out minified javascript files in data collection
"""

import string
import requests
from source_parser.utils import time_limit

MINIFY_URL = "https://javascript-minifier.com/raw"
INCLUDE_TYPES = set(
    [
        "+",
        "-",
        "*",
        "**",
        "/",
        "%",
        "=",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "**=",
        "==",
        "===",
        "!=",
        "!==",
        ">",
        "<",
        ">=",
        "<=",
        "?",
        "&&",
        "||",
        "&",
        "|",
        "~",
        "^",
        "<<",
        ">>",
        ">>>",
        ",",
        ";",
    ]
)
W_SPACE = set(string.whitespace.encode('utf-8'))
COMPOUND_LITS = ('concatenated_string, string_array', 'chained_string')


def is_minified(parser, indent_fraction=0.05, operator_ws_fraction=0.1, timeout=25):
    """
    Decides if given file name is a minified JavaScript file
    There is a difficulty deciding whether something is minified based on whitespace
    because sometimes licenses are included and licenses include spaces
    ****So not everyone uses .min.js as the minified extension?************
    Parameters
    ----------
    parser: JavascriptParser class object
    indent_fraction : float
        the cutoff for fraction of indented lines in file
    operator_ws_fraction : float
        the cutoff for fraction of operators in INCLUDE_TYPES that have whitespace
        next to them
    Returns
    -------
    boolean
        True : if the fraction of indented lines is less than .05, 5%
            or if the fraction of operators in included_types that have
            whitespace next to them is less than .1, 10%
        False : otherwise
    """
    with time_limit(timeout):
        file_fraction_indented_lines = fraction_of_indented_lines(parser.file_bytes)
        file_ws_fraction = fraction_of_tokens_with_whitespace(parser)
        if (
            file_fraction_indented_lines < indent_fraction
            or file_ws_fraction < operator_ws_fraction
        ):
            return True
    return False


def fraction_of_indented_lines(file_bytes):
    """
    Finds the fraction of indented lines in the file containing file_bytes
    Used as a helper function for is_minified because minified JavaScript
    code often times has a low fraction of indented lines
    Parameters
    ----------
    file_bytes : bytes
        the contents of a file in bytes
    Returns
    -------
    float :
        the fraction of lines in the file that are indented
    """
    num_lines = 0
    num_indented = 0
    for line in file_bytes.splitlines():
        num_lines += 1
        if line and line[0] in string.whitespace.encode("utf-8"):
            num_indented += 1
    if num_lines:
        return num_indented / num_lines
    return 0


def fraction_of_tokens_with_whitespace(parser):
    """
    Used to find the fraction of tokens (in INCLUDED_TYPES)
    that are next to whitespace.
    Used as a helper function to is_minified because minified
    JavaScript code tends to get rid of whitespace characters
    next to the operators in INCLUDED_TYPES

    NOTE: this is copying source_parser.utils.whitespace_tokenize
    but does not save tokens, improving speed memory consumption.

    Parameters
    ----------
    parser : JavascriptParser class object
        updated parser object with the TreeSitter parse tree
        of the file being tested

    Returns
    -------
    fraction : float
        the fraction of the operators in INCLUDED_TYPES that are next to
        whitespace
    """
    file_bytes = parser.file_bytes
    n_bytes = len(file_bytes)
    nodes = list(parser.tree.root_node.children)
    tokens_with_whitespace, included_tokens = 0, 0
    while nodes:
        nxt = nodes.pop(0)

        if (
                not nxt.children
                or (  # since comments/strings are not leaves
                    'string' in str(nxt.type)
                    and str(nxt.type) not in COMPOUND_LITS
                    or 'char' in str(nxt.type)
                )
        ):
            if nxt.type in INCLUDE_TYPES:
                included_tokens += 1
                fin = nxt.end_byte
                # test one char to right for whitespace
                if fin < n_bytes and file_bytes[fin] in W_SPACE:
                    tokens_with_whitespace += 1
            continue
        nodes = nxt.children + nodes

    # prevent divide by zero errors when no tokens present
    return tokens_with_whitespace / max(included_tokens, 1)


def minify_js(file_contents, timeout=60):
    """Minify the file_contents"""
    return requests.post(MINIFY_URL, data={"input": file_contents}, timeout=timeout).text
