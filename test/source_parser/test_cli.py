# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from importlib.metadata import distribution
import subprocess
import sys

import pytest

from source_parser import __version__


@pytest.mark.parametrize(
    "command,argument",
    [
        ("repo_parse", "-v"),
        ("repo_parse", "--help"),
        ("repo_scrape", "-v"),
        ("repo_scrape", "--help"),
        ("repo_scrape", "--list-langs"),
    ],
)
def test_console_entry_points(command, argument):
    entry_point = next(
        entry for entry in distribution("source_parser").entry_points
        if entry.group == "console_scripts" and entry.name == command
    )
    module, function = entry_point.value.split(":")
    result = subprocess.run(
        [sys.executable, "-c", f"from {module} import {function}; {function}()", argument],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    if argument == "-v":
        assert result.stdout.strip() == __version__
    elif argument == "--list-langs":
        assert "Python" in result.stdout
    else:
        assert "usage:" in result.stdout
