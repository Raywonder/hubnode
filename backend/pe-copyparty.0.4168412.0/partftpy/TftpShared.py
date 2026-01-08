# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

import sys

"a"


MIN_BLKSIZE = 8
DEF_BLKSIZE = 512
MAX_BLKSIZE = 65536
SOCK_TIMEOUT = 5
MAX_DUPS = 20
DEF_TIMEOUT_RETRIES = 3
DEF_TFTP_PORT = 69

DELAY_BLOCK = 0

NETWORK_UNRELIABILITY = 0



PY2 = sys.version_info < (3,)


try:
    TYPE_CHECKING = False
except:
    TYPE_CHECKING = False


def tftpassert(condition, msg):
    "a"
    if not condition:
        raise TftpException(msg)


class TftpErrors(object):
    "a"

    NotDefined = 0
    FileNotFound = 1
    AccessViolation = 2
    DiskFull = 3
    IllegalTftpOp = 4
    UnknownTID = 5
    FileAlreadyExists = 6
    NoSuchUser = 7
    FailedNegotiation = 8


class TftpException(Exception):
    "a"

    pass


class TftpTimeout(TftpException):
    "a"

    pass


class TftpTimeoutExpectACK(TftpTimeout):
    "a"

    pass


class TftpFileNotFoundError(TftpException):
    "a"

    pass
