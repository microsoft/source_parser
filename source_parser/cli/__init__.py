# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=bare-except,duplicate-code
import logging
import tqdm

logging.getLogger(__name__).addHandler(logging.NullHandler())
REPORT_LOG_LEVEL = logging.WARNING + 1
logging.addLevelName(REPORT_LOG_LEVEL, "REPORT")  # 1 higher than warning


def report(self, message, *args, **kws):
    self._log(REPORT_LOG_LEVEL, message, args, **kws)


logging.Logger.report = report

LOGGER = logging.getLogger(__name__)


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
