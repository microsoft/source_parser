# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=invalid-name
"""
repo_scrape

command line tool for cloning, walking, and saving
code in git repos. See command line help dialogue for usage:

    repo_scrape -h

"""

import os
import sys
import base64
from pathlib import Path
import logging
from itertools import islice
import argparse
import yaml
from columnize import columnize

import source_parser.cli
from source_parser.cli import TqdmLoggingHandler
from source_parser.cli import observers
from source_parser.cli.crawler import CrawlCrawler
from source_parser.cli.repo_parse import load_tasks

LOG_FMT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"


def main():
    with open(Path(source_parser.__file__).parent / 'languages.yml', 'r', encoding='utf-8') as file:
        LANGS = yaml.load(file, Loader=yaml.BaseLoader)
    GITHUB_LANGS = {}
    for label, value in LANGS.items():
        GITHUB_LANGS[label.replace(' ', '_')] = value

    if "--list-langs" in sys.argv:
        print(columnize(list(GITHUB_LANGS.keys()), displaywidth=88, colsep=',\t', ljust=False))
        sys.exit()

    if "-v" in sys.argv:
        print(f'{source_parser.__version__}')
        sys.exit()

    PARSER = argparse.ArgumentParser(
        description="""
    Take a json file containing a list of dictionaries with key 'url'
    containing a URL to a git repository, and extract files of a given language
    as defined by GitHub file extensions or a custom glob pattern. You must
    provide either a --lang flag or --include patterns.
    """
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

    GROUP = PARSER.add_mutually_exclusive_group(required=True)

    GROUP.add_argument(
        "--langs",
        type=str,
        help=(
            "Programming languages to extract files for and parse accordingly."
            " Use '--list-langs' to see language options"
        ),
        nargs="+",
    )

    PARSER.add_argument(
        "--all-extensions",
        action="store_true",
        help="Include all extensions beyond the primary one defined by GitHub's linguist package",
    )

    PARSER.add_argument(
        "--list-langs",
        help="Print all the --langs options and quit",
    )

    PARSER.add_argument("-v", help="Print version number")

    PARSER.add_argument(
        "--token",
        type=str,
        help=(
            "Personal Access Token (PAT) for authenticating git cloning, e.g. using Azure DevOps"
        ),
    )

    GROUP.add_argument(
        "--include",
        type=str,
        help="comma separated list of glob patterns of files to scrape",
    )

    PARSER.add_argument(
        "--label",
        type=str,
        help="Custom label tag for saved filenames, defaults to 'lang' or 'files'"
    )

    PARSER.add_argument(
        "--exclude",
        type=str,
        default=".?*",
        help="comma separated list of glob patterns of files to exclude",
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

    if ARGS.langs:
        MSG = f"arguments lang {ARGS.langs} contains an invalid choice. see reposcrape --list-langs"
        assert set(ARGS.langs).issubset(GITHUB_LANGS), MSG
        INCLUDE_PATTERNS = []
        for lang in ARGS.langs:
            EXTS = GITHUB_LANGS[lang]['extensions']
            if not ARGS.all_extensions:
                EXTS = EXTS[:1]
            INCLUDE_PATTERNS.extend([f'*?{ext}' for ext in EXTS])

        if not ARGS.label:
            ARGS.label = '-'.join([l.casefold() for l in ARGS.langs])
    else:
        INCLUDE_PATTERNS = ARGS.include.split(',')
        assert all(INCLUDE_PATTERNS), "Check --include for repeated ','"

    if ARGS.exclude:
        EXCLUDE_PATTERNS = ARGS.exclude.split(',')
        assert all(EXCLUDE_PATTERNS), "Check --exclude for repeated ','"

    if not ARGS.label:
        ARGS.label = 'files'

    if not Path(ARGS.outdir).exists():
        Path(ARGS.outdir).mkdir(parents=True)

    if ARGS.tmpdir and not Path(ARGS.tmpdir).exists():
        Path(ARGS.tmpdir).mkdir(parents=True)

    CRAWLER = CrawlCrawler(
        [
            observers.RepoObserver(
                INCLUDE_PATTERNS, EXCLUDE_PATTERNS, ARGS.outdir, label=ARGS.label, tmpdir=ARGS.tmpdir,
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

    LOGGER = logging.getLogger("repocontext")
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
