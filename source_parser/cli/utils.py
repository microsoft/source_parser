# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import shlex
import logging
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, Union

from source_parser.cli.licenses import match_license_file


LOGGER = logging.getLogger(__name__)


def save_logging_in_file(logger, logfile=None, processed_dir=None, level=logging.INFO):
    """ Setup logger to save to logfile as well """
    now = datetime.now()
    today = str(now).split()[0]
    time = f"{now.hour:0>2}{now.minute:0>2}"

    processed_dir = Path(processed_dir)
    if not logfile:
        logfile = processed_dir / f"{today}-{time}-crawlthecrawler.log"
    handler = logging.FileHandler(logfile)
    handler.setLevel(level)
    logger.addHandler(handler)


OPEN_ENCODING_KWARGS = [
    {"encoding": "utf-8-sig"},  # ignore byte-order mark if present
    {"encoding": "utf-16"},
    {"encoding": "latin-1"},
    # fall back on ascii and leave out tokens which couldn't be interpreted
    {"encoding": "ascii", "errors": "ignore"},
]


def load_file(file_path):
    """ Load file with fallback encodings, log warning if it fails """
    for open_kwargs in OPEN_ENCODING_KWARGS:
        try:
            with open(file_path, "r", **open_kwargs) as file:
                file_contents = file.read()
        except (UnicodeDecodeError, UnicodeError) as _:
            continue
        # return first successful decoding
        return file_contents.replace(chr(0), "")  # discard null bytes
    # None of the encodings worked
    raise UnicodeError(f"Failed to decode {file_path}")


def decode(bytestring):
    """ Decode bytes with fallback encodings """
    for decode_kwargs in OPEN_ENCODING_KWARGS:
        try:
            strng = bytestring.decode(**decode_kwargs)
        except (UnicodeDecodeError, UnicodeError) as _:
            continue
        return strng.replace(chr(0), "")  # discard null bytes
    raise UnicodeError("Failed to decode bytes")


def quiet_call(cmd, **kwargs):
    """ execute cmd in a subprocess and hide stdout and stderr """
    return subprocess.call(
        shlex.split(cmd),
        stdout=open(os.devnull, "w", encoding="utf-8"),
        stderr=open(os.devnull, "w", encoding="utf-8"),
        **kwargs,
    )  # call and suppress output


def get_head_commit_hash(repo_directory):
    try:
        return (
            subprocess.check_output(
                shlex.split("git rev-parse HEAD"),
                cwd=repo_directory,
                stderr=open(os.devnull, "w", encoding="utf-8"),
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return ""


def get_repo_data(
    repo_url,
    include: Union[Tuple, str],
    exclude: Union[Tuple, str] = (),
    branch=None,
    commit=None,
    tmpdir_path=None,
    timeout=20,
):
    """
    Clone the git repo at repo_url to directory and
    return metadata and file contents with extension ext

    Parameters
    ----------
    repo_url: str
        URL of git repository
    include: str/Tuple[str]
        one or more unix-like globs to match files, e.g.
        '*?.js' matches all javascript files with non-empty names.
    exclude: ext : str/Tuple[str]
        one or more unix-like globs to exclude files, e.g.
    branch: str
        specify  branch (or commit hash) to clone, defaults to HEAD
    depth: int
        the depth of history to retrieve, default is 1 (no history)
    commit: str
        sha-1 commit hash to retrieve, slower as it requires retrieving
        the history of this commit
    tmpdir_path: str/Path (optional)
        string or Path of directory to place temporary
        directory into
    timeout: int
        number of seconds allowed for cloning the repository

    Raises
    ------
    TimeoutException
        if elapsed time of trying to clone excedes timeout,
        raises TimeoutException

    Returns
    -------
    repo_data: dict
        repo_data{
            'url':  repo_url,
            'commit-hash': 091ab19...,
            'files': [
                'file1-path': 'contents of file1',
                'file2-path': 'contents of file2',
                ...
            ]
        }
    """
    tmpdir_path = str(tmpdir_path) if tmpdir_path is not None else None
    repo_url = repo_url.rstrip("/")  # trailing / messes up repo path below
    results = {"url": repo_url, "files": {}, "license": {}}
    with tempfile.TemporaryDirectory(dir=tmpdir_path) as tmpdir:
        working_dir = Path(tmpdir) / repo_url.split("/")[-1]
        multi_options = [
            "--depth=1",
        ]
        if branch:
            multi_options.append(f"-b {branch}")

        msg = clone_repository(
            repo_url,
            working_dir,
            multi_options=multi_options,
            commit=commit,
            timeout=timeout,
        )

        if msg:
            results["_msg"] = msg
            return results

        results["commit_hash"] = get_head_commit_hash(working_dir)
        if not results["commit_hash"]:
            results["_msg"] = 128  # register as clone failed
            return results

        for label, pathlist in walk(working_dir, include, exclude).items():
            for path in pathlist:
                path = str(path)
                results[label][path] = load_file(working_dir / path)

    return results


def clone_repo_test(repo_url, timeout=20):
    """
    Test whether a repo URL can be cloned by cloning it
    to a temporary directory in a limited time

    Parameters
    ----------
    repo_url : str,
        URL to a git repository

    (optional)
    timeout : int,
        number of seconds to allow, registers a failure if
        cloning takes longer than timeout seconds

    Returns
    -------
    could_clone : True/False
        True if clone was successful, False otherwise
    """
    repo_url = repo_url.rstrip("/")  # trailing / messes up repo path below
    with tempfile.TemporaryDirectory() as tmpdir:

        working_dir = Path(tmpdir) / repo_url.split("/")[-1]
        multi_options = ["--depth=1",]

        msg = clone_repository(
            repo_url,
            working_dir,
            multi_options=multi_options,
            timeout=timeout,
        )

        if msg or not get_head_commit_hash(working_dir):
            return False

    return True


def clone_repository(
    repo_url, directory, multi_options=None, env=None, commit=None, timeout=20
):
    """
    Clone a github repo URL into directory
    NOTE: for cloning Azure DevOps you may set the environment
    variable B64_PAT based on a personal access token, e.g.
        MY_PAT=yourPAT  # replace "yourPAT" with your actual PAT
        export B64_PAT=$(printf "%s"":$MY_PAT" | base64)

    Parameters
    ----------
    repo_url: str
        URL of git repository
    directory: str/Path
        string or Path of directory to place clone into
    multi_options: List[str] (optional)
        list of git clone command line options, defaults
        to ['--depth=1'] to grab first commit only
    env: Dict[str, str] (optional)
        environment variables in which to run git clone,
        defaults to {"GIT_TERMINAL_PROMPT": "0"} to turn off
        username and password prompts
    commit: str
        sha-1 commit hash to retrieve, slower as it requires retrieving
        the history of this commit
    commit: str
        sha-1 commit hash to checkout
    timeout: str
        number of second to allow clone to operate before quitting,
        a cheap heuristic to filter out data-heavy repositories.

    Returns
    -------
    msg: int
        error code, 0 means successful, 124 is a timeout, 128+ is
        some clone failure
    """
    cmdlist = [f"timeout {timeout} git"]
    if "B64_PAT" in os.environ:
        cmdlist.append(f'-c http.extraHeader="Authorization: Basic {os.environ["B64_PAT"]}"')
    cmdlist.append("clone")
    cmdlist.extend(
        multi_options or ["--depth=1",]
    )
    cmdlist.append(f"{repo_url} {directory}")
    msg = quiet_call(
        " ".join(cmdlist), env=env or dict(os.environ, GIT_TERMINAL_PROMPT="0"),
    )
    if msg:
        print(f"{repo_url} returned error {msg}")
        return msg

    if commit:
        cmd = f"timeout {timeout} git fetch origin {commit}"
        msg = quiet_call(
            cmd, env=env or dict(os.environ, GIT_TERMINAL_PROMPT="0"), cwd=directory
        )
        if msg:
            return msg
        msg = quiet_call(f"git checkout {commit}", cwd=directory)

    return msg


def _path_match_any(path, patterns):
    """
    Check if the given path matches any of the provided patterns.

    Parameters
    ----------
    path: str/Path
        The path to be checked.
    patterns: str/Tuple[str]
        One or more unix-like globs to match files.

    Returns
    -------
    bool
        True if the path matches any of the patterns, False otherwise.
    """
    # If patterns is a string, convert it to a tuple
    patterns = (patterns,) if isinstance(patterns, str) else patterns

    # Check if path matches any of the patterns
    return any(path.match(pattern) for pattern in patterns)


def walk(directory, include: Union[Tuple, str], exclude: Union[Tuple, str] = ()):
    """
    Walk directory and find all files ending with extension `ext`
    matching the glob '*?.ext'. Note this does NOT follow symlinks.

    Parameters
    ----------
    directory: str/Path
        string or path-like object of directory being walked
    include: str/Tuple[str]
        one or more unix-like globs to match files, e.g.
        '*?.js' matches all javascript files with non-empty names.
    exclude: str/Tuple[str]
        one or more unix-like globs to exclude files, e.g.

    Returns
    -------
    relevant_files: Dict[str, list[str/Path]]
        keys 'files' is a list of files in directory and
        'licenses' lists license files
    """
    results = {"files": [], "license": []}
    directory = Path(directory)
    queue = list(directory.iterdir())
    while queue:
        path = queue.pop()
        if _path_match_any(path, exclude):
            continue
        if path.is_dir() and not path.is_symlink():
            queue.extend(path.iterdir())
        elif _path_match_any(path, include):
            if path.exists() and not path.is_dir():
                results["files"].append(path.relative_to(directory))
        if match_license_file(path.name):
            if path.exists() and not path.is_dir():
                results["license"].append(path.relative_to(directory))
    return results
