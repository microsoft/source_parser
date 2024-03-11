# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=invalid-name

"""
repo_parse

Command line tool for cloning, walking, and parsing source
code in git repos. See command line help dialogue for usage:

    repo_parse -h

"""

import os
import sys
import json
import base64
from pathlib import Path
from itertools import chain, islice
import logging
import argparse

import source_parser.cli
from source_parser.cli import TqdmLoggingHandler
from source_parser.cli import observers
from source_parser.cli.crawler import CrawlCrawler

from source_parser.parsers import PythonParser, JavascriptParser, JavaParser, CppParser, CSharpParser, TypescriptParser

LOG_FMT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"


def load_tasks(repolists):
    tasks = []
    for repolist in repolists:
        with open(repolist, 'r', encoding='utf-8') as file:
            tasks.append(json.load(file))
    return chain(*tasks)


def main():
    if "-v" in sys.argv:
        print(f'{source_parser.__version__}')
        sys.exit()

    LANG_MAP = {
        "python": PythonParser,
        "javascript": JavascriptParser,
        "typescript": TypescriptParser,
        "java": JavaParser,
        "cpp": CppParser,
        "csharp": CSharpParser,
    }

    PARSER = argparse.ArgumentParser(
        description="""
    Take a json file containing a list of dictionaries with key 'url'
    containing a URL to a git repository, and extract files of a given language
    and process them into the structural schema
    """
    )

    PARSER.add_argument(
        "lang",
        type=str,
        help=("Programming language to extract files for and parse accordingly"),
        choices=list(LANG_MAP.keys()),
    )

    PARSER.add_argument(
        "repolist",
        type=str,
        help=(
            "path to one or more JSON files containing a list of dictionaries, each"
            " with a key 'url' containing a git repo URL and optionally 'sha'"
            " specifying the commit hash."
        ),
        nargs="+",
    )

    PARSER.add_argument(
        "outdir",
        type=str,
        help=(
            "directory in which to store the processed data and logs,"
            " which will be saved in formats <lang>-context-YYYY-MM-DD-HHMM.json.gz"
            " and YYYY-MM-DD-crawlercrawler.log, respectively"
        ),
    )

    PARSER.add_argument("-v", help="Print version number")

    PARSER.add_argument(
        "--tmpdir",
        type=str,
        help=(
            "temporary directory in which to place all the cloned git "
            "repositories for walking and reading. Protip: mount a RAMdisk "
            "and point --tmpdir there to remove IO bottlenecks!"
        ),
    )

    PARSER.add_argument(
        "--token",
        type=str,
        help=(
            "Personal Access Token (PAT) for authenticating git cloning, e.g. using Azure DevOps"
        ),
    )

    PARSER.add_argument(
        "--num_workers",
        type=int,
        default=1024,
        help=(
            "The number of tasks to have queued at any time. Setting to a number "
            "less than 0 queues all tasks immediately, which is the fastest, "
            "but can lead to unstable growth in memory consumption. "
            "A good compromise is a 1024-2048 so small tasks which complete "
            "quickly can pass through and large ones can take their time, "
            "but only a finite number of results are queued at a time."
        ),
    )

    PARSER.add_argument(
        "--report_freq",
        type=int,
        default=1000,
        help="The number of tasks completed between statistics reporting",
    )

    PARSER.add_argument(
        "--num_dedupe_procs",
        type=int,
        default=1,
        help=(
            "The number of CPUs dedicated to deduplicating files. "
            "This is in particular important for Javascript repos "
            "which are mostly duplicates, and this prevents "
            "bottlenecks. 2-4 are effective if you see Deduplicator "
            "processes filling up with memory."
        ),
    )

    PARSER.add_argument(
        "--num_save_files",
        type=int,
        default=1,
        help=(
            "The number of save files to distribute writing across. "
            "Useful when repositories produce so much data that one "
            "process is a bottleneck leading to unstable memory usage growth."
        ),
    )

    PARSER.add_argument(
        "--no-logs",
        action="store_false",
        help="turn off storing verbose logs in outdir for debugging and record-keeping",
    )

    PARSER.add_argument(
        "--duplicate_report_file",
        action="store_true",
        help=(
            "If provided, repocontext will write a file "
            "'YYYY-MM-DD-HH-MM-duplicate_file_report.json' "
            "placed in the provided 'outdir' which will contain a JSON "
            "Dict[file_hash] = {'counts': ..., 'relative_path': ..., "
            "'url': ...} for each duplicate file found."
        ),
    )

    PARSER.add_argument(
        "--first_k",
        type=int,
        default=None,
        help="Only process the first k tasks to test or speedup results.",
    )

    ARGS = PARSER.parse_args()

    if not Path(ARGS.outdir).exists():
        Path(ARGS.outdir).mkdir(parents=True)

    CRAWLER = CrawlCrawler(
        [
            observers.RepoContextObserver(
                LANG_MAP[ARGS.lang], ARGS.outdir, tmpdir=ARGS.tmpdir,
            )
        ],
        ARGS.outdir,
    )

    if ARGS.no_logs:
        LOGFILE = Path(ARGS.outdir) / f"{observers.TODAY}-{observers.TIME}-crawlercrawler.log"
        logging.basicConfig(
            level=logging.WARNING,
            format=LOG_FMT,
            datefmt="%m-%d %H:%M",
            filename=LOGFILE,
            filemode="w",
        )

    LOGGER = logging.getLogger("repo_parse")
    LOGGER.setLevel(logging.WARNING)
    CONSOLE = TqdmLoggingHandler(logging.WARNING)  # REPORT
    CONSOLE.setFormatter(logging.Formatter(LOG_FMT))
    LOGGER.addHandler(CONSOLE)

    if ARGS.token:
        LOGGER.report("Setting PAT token environment variable B64_PAT")
        os.environ["B64_PAT"] = base64.b64encode(f":{ARGS.token}".encode('utf-8')).decode('utf-8')
        ARGS.token = ""  # so the token does not leak into the logs

    if ARGS.no_logs:
        LOGGER.report(f"Saving logs up to INFO in {LOGFILE}")

    if ARGS.duplicate_report_file:
        ARGS.duplicate_report_file = f"{observers.TODAY}-{observers.TIME}"

    LOGGER.report(ARGS)

    TASKS = load_tasks(ARGS.repolist)
    if ARGS.first_k:
        TASKS = islice(TASKS, 0, ARGS.first_k)

    CRAWLER.map(
        list(TASKS),  # so tqdm knows the length
        num_dedupe_procs=ARGS.num_dedupe_procs,
        num_save_files=ARGS.num_save_files,
        duplicate_report_file=ARGS.duplicate_report_file,
        num_workers=ARGS.num_workers,
        report_freq=ARGS.report_freq,
    )
