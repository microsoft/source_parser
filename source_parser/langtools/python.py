# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=deprecated-module
"""
This is a set of tools for processing python source code within a python script
"""

import ast
import lib2to3
import lib2to3.fixes
import lib2to3.refactor
import warnings
import autopep8

from source_parser.utils import time_limit


_ALL_FIXES = [
    f"lib2to3.fixes.fix_{l}"
    for l in lib2to3.refactor.get_all_fix_names("lib2to3.fixes")
]
_TOOL = lib2to3.refactor.RefactoringTool(_ALL_FIXES)


def fix2to3(source_string):
    """
    Attempt to run fixes on python source_string to convert
    from python2 to python3

    Parameters
    ----------
    source_string: str
        string contents of python source code

    Returns
    -------
    fixed_string: str
        source code with all 2to3 fixes applied
    """
    # + "\n" to enable parse, then [:-1] to remove
    return str(_TOOL.refactor_string(source_string + "\n", "<script>"))[:-1]


def attempt_fix(source_string, fixer, timeout):
    """Attempt to fix source_string with fixer in timeout seconds"""
    with time_limit(timeout):
        return fixer(source_string)


def check_python3_attempt_fix(source_string, timeout=25):
    """
    Checks that source_string has correct python3 syntax,
    and attempts to fix common python2 issues and indentation
    issues using 2to3 and autopep8

    Parameters
    ----------
    source_string: str
        string of python source code
    timout: int (optional)
        second allowed for fix attempts

    Returns
    -------
    fixed_source_string: str
        fixed source string or original if no fix needed

    Raises
    ------
    TimeoutException
        if any of the attempted fixes time out
    IndentationError
        if the attemped indentation fix failed to fix
    SyntaxError
        if the attempted 2to3 converstion failed to fix
    """
    fixes = {
        IndentationError: autopep8.fix_code,
        SyntaxError: fix2to3,
        TabError: autopep8.fix_code,
    }
    while fixes:
        try:

            with warnings.catch_warnings():  # don't print SyntaxWarnings
                warnings.simplefilter('ignore')
                ast.parse(source_string)
            break

        except (SyntaxError, TabError) as s_err:  # indents and syntax
            if s_err.__class__ in fixes:

                with warnings.catch_warnings():  # don't print SyntaxWarnings
                    warnings.simplefilter('ignore')
                    source_string = attempt_fix(
                        source_string, fixes.pop(s_err.__class__), timeout
                    )
                continue
            raise s_err
    return source_string


def fix_indentation(source_string, timeout=25):
    """
    Fix indentation to be PEP8 compliant

    Parameters
    ----------
    source_string : str
        string of python source code
    timout: int (optional)
        second allowed for fix attempts

    Returns
    -------
    fixed_source_string : str
        fixed source string

    Raises
    ------
    TimeoutException
        if any of the attempted fixes time out
    """

    with warnings.catch_warnings():  # don't print SyntaxWarnings
        warnings.simplefilter('ignore')
        with time_limit(timeout):
            return autopep8.fix_code(source_string, options={"select": ("E101",)})
