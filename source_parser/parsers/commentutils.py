# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=dangerous-default-value

import re

LEADING_HASHTAG_COMMENT_PLAINTEXT_REGEX = re.compile(
    r"^([ \t]*#.*\n)*\n*([ \t]*#.*\n)*\n*"
)
LEADING_C_STYLE_COMMENT_PLAINTEXT_REGEX = re.compile(
    r"^\/\*+.*?\*\/\n*", flags=re.DOTALL
)
LEADING_SLASH_COMMENT_PLAINTEXT_REGEX = re.compile(r"^([ \t]*//.*\n)*\n*")


def strip_c_style_comment_delimiters(comment: str) -> str:
    comment_lines = comment.splitlines()
    cleaned_lines = []
    for l in comment_lines:
        l = l.lstrip()
        if l.endswith(" */"):
            l = l[:-3]
        elif l.endswith("*/"):
            l = l[:-2]
        if l.startswith("* "):
            l = l[2:]
        elif l.startswith("/**"):
            l = l[3:]
        elif l.startswith("/*"):
            l = l[2:]
        elif l.startswith("///"):
            l = l[3:]
        elif l.startswith("//"):
            l = l[2:]
        elif l.startswith("*"):
            l = l[1:]
        cleaned_lines.append(l)
    return "\n".join(cleaned_lines)


def get_leading_comment(
    text,
    comment_regexes=[
        LEADING_C_STYLE_COMMENT_PLAINTEXT_REGEX,
        LEADING_SLASH_COMMENT_PLAINTEXT_REGEX,
        LEADING_HASHTAG_COMMENT_PLAINTEXT_REGEX,
    ],
):
    """
    locates a potential location for a license in a file string
    extracts and returns the potential license if regex match found
    Parameters
    ----------
    text : string
        the contents of a file
    comment_regexes : list of regular expressions
        license regular expressions
    Returns
    -------
    string
        string of potential license if regex match exists
        else, empty string"""
    for regex in comment_regexes:
        match = re.match(regex, text)
        if match is not None:
            _, comment_end = match.span()
            if comment_end > 0:
                return text[:comment_end]
    return ""


def strip_plaintext_license(
    plain_text,
    comment_regexes=[
        LEADING_C_STYLE_COMMENT_PLAINTEXT_REGEX,
        LEADING_SLASH_COMMENT_PLAINTEXT_REGEX,
        LEADING_HASHTAG_COMMENT_PLAINTEXT_REGEX,
    ],
):
    """
    Uses get_leading_comment to find potential license
    checks that potential license is a license
    Strips the license off of a file string
    Parameters
    ----------
    plain_text : string
        contents of a file
    comment_regexes : list of regular expressions
        regexes can be seen at the top of this file
    Returns
    -------
    string
        if a license was found on the original file string,
        the license will be taken off and the rest of the
        file string will be returned
        if a license was not found on original string
        the original string is returned """
    leading_comment = get_leading_comment(plain_text, comment_regexes)
    if re.search("license|copyright", leading_comment, flags=re.IGNORECASE) is not None:
        return plain_text[len(leading_comment):], plain_text[: len(leading_comment)]
    return plain_text, ""
