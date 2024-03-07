# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import gzip
import json
from pathlib import Path
import logging
import lz4.frame
from ._version import __version__

logging.getLogger(__name__).addHandler(logging.NullHandler())
REPORT_LOG_LEVEL = logging.WARNING + 1
logging.addLevelName(REPORT_LOG_LEVEL, "REPORT")  # 1 higher than warning


def report(self, message, *args, **kws):
    self._log(REPORT_LOG_LEVEL, message, args, **kws)


logging.Logger.report = report

LOGGER = logging.getLogger(__name__)


OPEN_PROTOCOLS = {
    '.gz': gzip.open,
    'gzip': gzip.open,
    '.lz4': lz4.frame.open,
    'lz4': lz4.frame.open,
}


def load_zip_json(filename, head=None, thin=None):
    """
    Load files created by SaveComments and other children of Observer.
    Loads *.json.gz files and *.json.lz4 files, which are not technically json,
    but are json separated by newlines. Yields one line at a time for
    iterative processing.

    Parameters
    ----------
    filename : str
    head : int, optional
        only read and return the first head elements
    thin : int, optional
        only read and return every thin-th element

    Yields
    -------
    dat: Union[List,Dict,Tuple]
        individual parsed JSON elements
    """

    open_protocol = OPEN_PROTOCOLS[Path(filename).suffix]
    with open_protocol(filename, "rb") as fin:
        lineno = 0
        while head is None or lineno < head:
            try:
                line = fin.readline()
            except (OSError, EOFError) as o_err:
                LOGGER.warning(
                    "Data lost decompressing line raised %s: %s",
                    type(o_err), o_err
                )
                break
            if not line:
                break
            if thin is None or lineno % thin == 0:
                yield json.loads(line.decode('utf-8'))
            lineno += 1
