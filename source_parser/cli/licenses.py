# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
licenses.py

Tool containing a list of regex heuristics for detecting license
files.
"""

import re


# Gets notices
LEGAL_FILES_REGEX = r"(AUTHORS|NOTICE|LEGAL)(?:\..*)?\Z"

PREFERRED_EXT_REGEX = r"\.[md|markdown|txt|html]\Z"

# Regex to match any extension except .spdx or .header
OTHER_EXT_REGEX = r"\.(?!spdx|header|gemspec)[^./]+\Z"

# Regex to match, LICENSE, LICENCE, unlicense, etc.
LICENSE_REGEX = r"(un)?licen[sc]e"

# Regex to match COPYING, COPYRIGHT, etc.
COPYING_REGEX = r"copy(ing|right)"

# Regex to match OFL.
OFL_REGEX = r"ofl"

# BSD + PATENTS patent file
PATENTS_REGEX = r"patents"

REGEX_LICENSES = [
    LEGAL_FILES_REGEX,
    LICENSE_REGEX + r"\Z",
    LICENSE_REGEX + PREFERRED_EXT_REGEX,
    COPYING_REGEX + r"\Z",
    COPYING_REGEX + PREFERRED_EXT_REGEX,
    LICENSE_REGEX + OTHER_EXT_REGEX,
    COPYING_REGEX + OTHER_EXT_REGEX,
    LICENSE_REGEX + r"[-_]",
    COPYING_REGEX + r"[-_]",
    r"[-_]" + LICENSE_REGEX,
    r"[-_]" + COPYING_REGEX,
    OFL_REGEX + PREFERRED_EXT_REGEX,
    OFL_REGEX + OTHER_EXT_REGEX,
    OFL_REGEX + r"\Z",
    PATENTS_REGEX + r"\Z",
    PATENTS_REGEX + OTHER_EXT_REGEX,
]

RE_LICENSE_FILE = re.compile("|".join([f"(?:{r})" for r in REGEX_LICENSES]))


def match_license_file(filename):
    """
    Match license filenames with regex patterns

    Parameters
    ----------
    filename: str/Path
        path to candidate filename

    Returns
    -------
    True/False
    """
    if RE_LICENSE_FILE.match(filename.lower()):
        return True
    return False
