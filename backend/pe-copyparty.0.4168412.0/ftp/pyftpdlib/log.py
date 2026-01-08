# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"a"

import logging
import re
import sys
import time


try:
    import curses
except ImportError:
    curses = None

from ._compat import PY3
from ._compat import unicode

logger = logging.getLogger('pyftpdlib')


def _stderr_supports_color():
    color = False
    if curses is not None and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color

LEVEL = logging.INFO
PREFIX = '[%(levelname)1.1s %(asctime)s]'
PREFIX_MPROC = '[%(levelname)1.1s %(asctime)s %(process)s]'
COLOURED = _stderr_supports_color()
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class LogFormatter(logging.Formatter):
    "a"

    PREFIX = PREFIX

    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._coloured = COLOURED and _stderr_supports_color()
        if self._coloured:
            curses.setupterm()

            fg_color = (
                curses.tigetstr("setaf") or curses.tigetstr("setf") or ""
            )
            if not PY3:
                fg_color = unicode(fg_color, "ascii")
            self._colors = {

                logging.DEBUG: unicode(curses.tparm(fg_color, 4), "ascii"),

                logging.INFO: unicode(curses.tparm(fg_color, 2), "ascii"),

                logging.WARNING: unicode(curses.tparm(fg_color, 3), "ascii"),

                logging.ERROR: unicode(curses.tparm(fg_color, 1), "ascii"),
            }
            self._normal = unicode(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as err:
            record.message = "Bad message (%r): %r" % (err, record.__dict__)

        record.asctime = time.strftime(
            TIME_FORMAT, self.converter(record.created)
        )
        prefix = self.PREFIX % record.__dict__
        if self._coloured:
            prefix = (
                self._colors.get(record.levelno, self._normal)
                + prefix
                + self._normal
            )

        try:
            message = unicode(record.message)
        except UnicodeDecodeError:
            message = repr(record.message)

        formatted = prefix + " " + message
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted = formatted.rstrip() + "\n" + record.exc_text
        return formatted.replace("\n", "\n    ")


def debug(s, inst=None):
    s = "[debug] " + s
    if inst is not None:
        s += " (%r)" % inst
    logger.debug(s)


def is_logging_configured():
    if logging.getLogger('pyftpdlib').handlers:
        return True
    return bool(logging.root.handlers)



def config_logging(level=LEVEL, prefix=PREFIX, other_loggers=None):

    key_names = set(
        re.findall(
            r'(?<!%)%\(([^)]+)\)[-# +0-9.hlL]*[diouxXeEfFgGcrs]', prefix
        )
    )
    if "process" not in key_names:
        logging.logProcesses = False
    if "processName" not in key_names:
        logging.logMultiprocessing = False
    if "thread" not in key_names and "threadName" not in key_names:
        logging.logThreads = False
    if (
        "filename" not in key_names
        and "pathname" not in key_names
        and "lineno" not in key_names
        and "module" not in key_names
    ):

        logging._srcfile = None

    handler = logging.StreamHandler()
    formatter = LogFormatter()
    formatter.PREFIX = prefix
    handler.setFormatter(formatter)
    loggers = [logging.getLogger('pyftpdlib')]
    if other_loggers is not None:
        loggers.extend(other_loggers)
    for log in loggers:
        log.setLevel(level)
        log.addHandler(handler)
