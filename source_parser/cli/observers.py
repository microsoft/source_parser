# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
observers.py

This module contains an observer which clones, walks, and parses
git repositories, handles errors, and accumulates statistics.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from source_parser import __version__
from source_parser.cli.utils import get_repo_data
from source_parser.utils import static_hash, time_limit, TimeoutException

NOW = datetime.now()
TODAY = str(NOW).split()[0]
TIME = f"{NOW.hour:0>2}{NOW.minute:0>2}"

LOGGER = logging.getLogger(__name__)


class Observer(ABC):
    """Observer base class"""

    savefile = ''

    @abstractmethod
    def notify(self, statistics, task, timeout):
        """notify observer to complete new task and aggregate statistics"""

    def speak(self):
        """Give a generic message"""
        LOGGER.info("Saving in %s", self.savefile)


class RepoContextObserver(Observer):
    """
    Observer which clones git repositories, crawls for file
    types, and applied structural parsers to them, saving in one
    final file.
    """

    savefile_template = "{}-v{}-context-{}-{}.json.{}"  # LANG, VERSION, TODAY, TIME, ext

    # statistics collected by this observer
    statistic_labels = (
        "schema_parse_failed",
        "git_clone_failed",
        "git_clone_timeout",
        "repos_with_no_relevant_files",
        "preprocess_timeout",
        "relevant_files",
        "relevant_files_with_structures",
        "number_of_methods",
        "number_of_classes",
        "number_of_lines",
        "number_of_chars",
        "preprocess_failed",
        "preprocess_filtered",
        "parser_timeout",
        "duplicate_items",
    )

    def __init__(
            self, parser_class, processed_dir, savefile=None, tmpdir=None, **kwargs
    ):
        """
        Parameters
        ----------
        parser_class: LanguageParser
            Language-specific subclass of LanguageParser,
            not an instance but the class itself
        processed_dir: str
            location in which to save processed data and logs
        savefile: str (optional)
            savefile name
        tmpdir: str (optional)
            location in which to spawn temporary directories
        """
        self.parser_class = parser_class
        self.tmpdir = tmpdir
        self.set_save_location(processed_dir, savefile, **kwargs)

    def set_save_location(self, processed_dir, savefile=None, **kwargs):
        """Set the save location using the template and processed_dir"""
        self.processed_dir = Path(processed_dir)
        self.savefile = self.processed_dir / (
            savefile
            or self.savefile_template.format(
                self.parser_class.get_lang(),
                __version__,
                TODAY,
                TIME,
                kwargs.get("compression", "lz4"),
            )
        )

    def notify(self, statistics, task, timeout=20):
        """
        Act on a given task and collect statistics, returning result

        Parameters
        ----------
        statistics: dict
            dictionary of statistic labels and integer entries
            to be modified in place by notify
        task: dict
            with key 'url' containing a valid git repo URL, optionall
            a 'license' key with a string label for the lience of the repo.
        parser: LanguageParser
            instantiated language parser object for parsing files
        timeout: int (optional)
            time limit on git cloning before giving up (filters
            data filled repositories)

        Returns
        -------
        results, error_msgs: list, list
            list of source_parser schema dictionaries for each
            file found (does not return files which lacked structures)
            and list of error messages found while processing the task.
        """
        parser = self.parser_class()

        url = task["url"].rstrip("/")
        repo_data = get_repo_data(
            url,
            include=parser.include_patterns,
            exclude=parser.exclude_patterns,
            tmpdir_path=self.tmpdir,
            timeout=timeout,
            commit=task.get('sha')
        )

        msg = repo_data.pop("_msg", 0)
        if msg == 124:
            statistics["git_clone_timeout"] += 1
            return [], []
        if msg >= 128:
            statistics["git_clone_failed"] += 1
            return [], []

        if "commit_hash" not in repo_data:
            statistics["git_clone_failed"] += 1
            return [], []
        if not repo_data["files"]:
            statistics["repos_with_no_relevant_files"] += 1
            return [], []

        statistics["relevant_files"] += len(repo_data["files"])

        repo_schema = {
            "url": url,
            "repo_name": "/".join(url.split("/")[-2:]),
            "commit_hash": repo_data["commit_hash"],
            "license": {
                "label": task.get("license", None),
                "files": [
                    # NOTE: I am not saving license contents for now to save space!
                    {"relative_path": rel_path, "file_contents": "", }
                    for rel_path, contents in repo_data["license"].items()
                ],
            },
        }

        results = []
        error_msgs = []
        for rel_path, file_contents in repo_data["files"].items():

            try:
                processed_contents = parser.preprocess_file(file_contents)
                parser.update(processed_contents)
                if not processed_contents:
                    statistics["preprocess_filtered"] += 1
                    continue
            except TimeoutException:
                statistics["preprocess_timeout"] += 1
                continue
            except Exception as e_err:
                statistics["preprocess_failed"] += 1
                error_msgs.append(
                    f"\n\tFile {url}/{rel_path} raised {type(e_err)}: {e_err}\n"
                )
                continue

            statistics["number_of_lines"] += processed_contents.count("\n")
            statistics["number_of_chars"] += len(processed_contents)

            try:
                try:
                    with time_limit(timeout):
                        schema = parser.schema
                except TimeoutException:
                    statistics["parser_timeout"] += 1
                    continue

                if not any(schema.values()):
                    continue  # don't save files without features

                statistics["relevant_files_with_structures"] += 1
                statistics["number_of_methods"] += len(schema["methods"])
                statistics["number_of_classes"] += len(schema["classes"])
                file_results = {
                    "relative_path": rel_path,
                    "original_string": processed_contents,
                }
                file_results.update(schema)
                file_results.update(repo_schema)
                results.append(file_results)

            except Exception as e_err:  #
                statistics["schema_parse_failed"] += 1
                error_msgs.append(
                    f"\n\tFile {url}/{rel_path} raised {type(e_err)}: {e_err}\n"
                )

        return results, error_msgs


class RepoObserver(Observer):
    """
    Observer which clones git repositories, crawls for file
    types, and saves all files matching desired file types
    """

    # .format(LANG, TODAY, TIME, ext)
    savefile_template = "reposcrape-{}-v-{}-context-{}-{}.json.{}"

    # statistics collected by this observer
    statistic_labels = (
        "git_clone_failed",
        "git_clone_timeout",
        "repos_with_no_relevant_files",
        "relevant_files",
        "number_of_lines",
        "number_of_chars",
        "empty_files",
        "duplicate_items",
    )

    def __init__(
            self,
            include_patterns,
            exclude_patterns,
            processed_dir,
            label="files",
            savefile=None,
            tmpdir=None,
            **kwargs,
    ):
        """
        Parameters
        ----------
        include_patterns: Union[Tuple,Str]
            either a single string or tuple of string glob patterns to include
        exclude: Union[Tuple,Str]
            either a single string or tuple of string glob patterns to exclude
        processed_dir: str
            location in which to save processed data and logs
        label: str (optional)
            optional label for savefile to helpfully annotate contents, e.g.
            if include is '*?.md', a helpful label would be 'markdown'
        savefile: str (optional)
            savefile name
        tmpdir: str (optional)
            location in which to spawn temporary directories
        """
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.label = label
        self.tmpdir = tmpdir
        self.set_save_location(processed_dir, savefile, **kwargs)

    def set_save_location(self, processed_dir, savefile=None, **kwargs):
        """Set the save location using the template and processed_dir"""
        self.processed_dir = Path(processed_dir)
        self.savefile = self.processed_dir / (
            savefile
            or self.savefile_template.format(
                self.label, __version__, TODAY, TIME, kwargs.get("compression", "lz4")
            )
        )

    def notify(self, statistics, task, timeout=20):
        """
        Act on a given task and collect statistics, returning result

        Parameters
        ----------
        statistics: dict
            dictionary of statistic labels and integer entries
            to be modified in place by notify
        task: dict
            with key 'url' containing a valid git repo URL, optionall
            a 'license' key with a string label for the lience of the repo.
        timeout: int (optional)
            time limit on git cloning before giving up (filters
            data filled repositories)

        Returns
        -------
        results, error_msgs: list, list
            list of source_parser schema dictionaries for each
            file found (does not return files which lacked structures)
            and list of error messages found while processing the task.
        """
        url = task["url"].rstrip("/")
        repo_data = get_repo_data(
            url,
            include=self.include_patterns,
            exclude=self.exclude_patterns,
            tmpdir_path=self.tmpdir,
            timeout=timeout,
            commit=task.get('sha')
        )

        msg = repo_data.pop("_msg", 0)
        if msg == 124:
            statistics["git_clone_timeout"] += 1
            return [], []
        if msg >= 128:
            statistics["git_clone_failed"] += 1
            return [], []

        if "commit_hash" not in repo_data:
            statistics["git_clone_failed"] += 1
            return [], []
        if not repo_data["files"]:
            statistics["repos_with_no_relevant_files"] += 1
            return [], []

        statistics["relevant_files"] += len(repo_data["files"])

        repo_schema = {
            "url": url,
            "repo_name": "/".join(url.split("/")[-2:]),
            "commit_hash": repo_data["commit_hash"],
            "license": {
                "label": task.get("license", None),
                "files": [
                    {"relative_path": rel_path, "file_contents": "", }
                    for rel_path, contents in repo_data["license"].items()
                ],
            },
        }

        results = []
        error_msgs = []
        for rel_path, file_contents in repo_data["files"].items():

            if not file_contents:
                statistics["empty_files"] += 1
                continue

            statistics["number_of_lines"] += file_contents.count("\n")
            statistics["number_of_chars"] += len(file_contents)

            file_results = {
                "relative_path": rel_path,
                "original_string": file_contents,
                "file_hash": static_hash(file_contents),  # REQUIRED!
            }
            file_results.update(repo_schema)
            results.append(file_results)

        return results, error_msgs
