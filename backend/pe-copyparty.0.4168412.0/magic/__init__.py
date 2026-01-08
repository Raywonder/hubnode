"a"

import sys
import glob
import ctypes
import ctypes.util
import threading
import logging

from ctypes import c_char_p, c_int, c_size_t, c_void_p, byref, POINTER

_real_open = open


class MagicException(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)
        self.message = message


class Magic(object):
    "a"

    def __init__(self, mime=False, magic_file=None, mime_encoding=False,
                 keep_going=False, uncompress=False, raw=False, extension=False):
        "a"
        self.flags = MAGIC_NONE
        if mime:
            self.flags |= MAGIC_MIME_TYPE
        if mime_encoding:
            self.flags |= MAGIC_MIME_ENCODING
        if keep_going:
            self.flags |= MAGIC_CONTINUE
        if uncompress:
            self.flags |= MAGIC_COMPRESS
        if raw:
            self.flags |= MAGIC_RAW
        if extension:
            self.flags |= MAGIC_EXTENSION

        self.cookie = magic_open(self.flags)
        self.lock = threading.Lock()

        magic_load(self.cookie, magic_file)

        if extension and (not _has_version or version() < 524):
            raise NotImplementedError('MAGIC_EXTENSION is not supported in this version of libmagic')

        if _has_param:
            try:
                self.setparam(MAGIC_PARAM_NAME_MAX, 64)
            except MagicException as e:

                pass

    def from_buffer(self, buf):
        "a"
        with self.lock:
            try:

                if type(buf) == str and str != bytes:
                    buf = buf.encode('utf-8', errors='replace')
                return maybe_decode(magic_buffer(self.cookie, buf))
            except MagicException as e:
                return self._handle509Bug(e)

    def from_file(self, filename):

        with _real_open(filename):
            pass

        with self.lock:
            try:
                return maybe_decode(magic_file(self.cookie, filename))
            except MagicException as e:
                return self._handle509Bug(e)

    def from_descriptor(self, fd):
        with self.lock:
            try:
                return maybe_decode(magic_descriptor(self.cookie, fd))
            except MagicException as e:
                return self._handle509Bug(e)

    def _handle509Bug(self, e):

        if e.message is None and (self.flags & MAGIC_MIME_TYPE):
            return "application/octet-stream"
        else:
            raise e

    def setparam(self, param, val):
        return magic_setparam(self.cookie, param, val)

    def getparam(self, param):
        return magic_getparam(self.cookie, param)

    def __del__(self):

        if hasattr(self, 'cookie') and self.cookie and magic_close:
            magic_close(self.cookie)
            self.cookie = None


_instances = {}


def _get_magic_type(mime):
    i = _instances.get(mime)
    if i is None:
        i = _instances[mime] = Magic(mime=mime)
    return i


def from_file(filename, mime=False):
    "a"
    m = _get_magic_type(mime)
    return m.from_file(filename)


def from_buffer(buffer, mime=False):
    "a"
    m = _get_magic_type(mime)
    return m.from_buffer(buffer)


def from_descriptor(fd, mime=False):
    "a"
    m = _get_magic_type(mime)
    return m.from_descriptor(fd)

from . import loader
libmagic = loader.load_lib()

magic_t = ctypes.c_void_p


def errorcheck_null(result, func, args):
    if result is None:
        err = magic_error(args[0])
        raise MagicException(err)
    else:
        return result


def errorcheck_negative_one(result, func, args):
    if result == -1:
        err = magic_error(args[0])
        raise MagicException(err)
    else:
        return result

def maybe_decode(s):

    if str == bytes:
        return s
    else:

        return s.decode('utf-8', 'backslashreplace')


try:
    from os import PathLike
    def unpath(filename):
        if isinstance(filename, PathLike):
            return filename.__fspath__()
        else:
            return filename
except ImportError:
    def unpath(filename):
        return filename

def coerce_filename(filename):
    if filename is None:
        return None

    filename = unpath(filename)

    is_unicode = (sys.version_info[0] <= 2 and
                 isinstance(filename, unicode)) or                 (sys.version_info[0] >= 3 and
                  isinstance(filename, str))
    if is_unicode:
        return filename.encode('utf-8', 'surrogateescape')
    else:
        return filename


magic_open = libmagic.magic_open
magic_open.restype = magic_t
magic_open.argtypes = [c_int]

magic_close = libmagic.magic_close
magic_close.restype = None
magic_close.argtypes = [magic_t]

magic_error = libmagic.magic_error
magic_error.restype = c_char_p
magic_error.argtypes = [magic_t]

magic_errno = libmagic.magic_errno
magic_errno.restype = c_int
magic_errno.argtypes = [magic_t]

_magic_file = libmagic.magic_file
_magic_file.restype = c_char_p
_magic_file.argtypes = [magic_t, c_char_p]
_magic_file.errcheck = errorcheck_null


def magic_file(cookie, filename):
    return _magic_file(cookie, coerce_filename(filename))


_magic_buffer = libmagic.magic_buffer
_magic_buffer.restype = c_char_p
_magic_buffer.argtypes = [magic_t, c_void_p, c_size_t]
_magic_buffer.errcheck = errorcheck_null


def magic_buffer(cookie, buf):
    return _magic_buffer(cookie, buf, len(buf))


magic_descriptor = libmagic.magic_descriptor
magic_descriptor.restype = c_char_p
magic_descriptor.argtypes = [magic_t, c_int]
magic_descriptor.errcheck = errorcheck_null

_magic_descriptor = libmagic.magic_descriptor
_magic_descriptor.restype = c_char_p
_magic_descriptor.argtypes = [magic_t, c_int]
_magic_descriptor.errcheck = errorcheck_null


def magic_descriptor(cookie, fd):
    return _magic_descriptor(cookie, fd)


_magic_load = libmagic.magic_load
_magic_load.restype = c_int
_magic_load.argtypes = [magic_t, c_char_p]
_magic_load.errcheck = errorcheck_negative_one


def magic_load(cookie, filename):
    return _magic_load(cookie, coerce_filename(filename))


magic_setflags = libmagic.magic_setflags
magic_setflags.restype = c_int
magic_setflags.argtypes = [magic_t, c_int]

magic_check = libmagic.magic_check
magic_check.restype = c_int
magic_check.argtypes = [magic_t, c_char_p]

magic_compile = libmagic.magic_compile
magic_compile.restype = c_int
magic_compile.argtypes = [magic_t, c_char_p]

_has_param = False
if hasattr(libmagic, 'magic_setparam') and hasattr(libmagic, 'magic_getparam'):
    _has_param = True
    _magic_setparam = libmagic.magic_setparam
    _magic_setparam.restype = c_int
    _magic_setparam.argtypes = [magic_t, c_int, POINTER(c_size_t)]
    _magic_setparam.errcheck = errorcheck_negative_one

    _magic_getparam = libmagic.magic_getparam
    _magic_getparam.restype = c_int
    _magic_getparam.argtypes = [magic_t, c_int, POINTER(c_size_t)]
    _magic_getparam.errcheck = errorcheck_negative_one


def magic_setparam(cookie, param, val):
    if not _has_param:
        raise NotImplementedError("magic_setparam not implemented")
    v = c_size_t(val)
    return _magic_setparam(cookie, param, byref(v))


def magic_getparam(cookie, param):
    if not _has_param:
        raise NotImplementedError("magic_getparam not implemented")
    val = c_size_t()
    _magic_getparam(cookie, param, byref(val))
    return val.value


_has_version = False
if hasattr(libmagic, "magic_version"):
    _has_version = True
    magic_version = libmagic.magic_version
    magic_version.restype = c_int
    magic_version.argtypes = []


def version():
    if not _has_version:
        raise NotImplementedError("magic_version not implemented")
    return magic_version()


MAGIC_NONE = 0x000000
MAGIC_DEBUG = 0x000001
MAGIC_SYMLINK = 0x000002
MAGIC_COMPRESS = 0x000004
MAGIC_DEVICES = 0x000008
MAGIC_MIME_TYPE = 0x000010
MAGIC_MIME_ENCODING = 0x000400

MAGIC_MIME = 0x000010
MAGIC_EXTENSION = 0x1000000

MAGIC_CONTINUE = 0x000020
MAGIC_CHECK = 0x000040
MAGIC_PRESERVE_ATIME = 0x000080
MAGIC_RAW = 0x000100
MAGIC_ERROR = 0x000200

MAGIC_NO_CHECK_COMPRESS = 0x001000
MAGIC_NO_CHECK_TAR = 0x002000
MAGIC_NO_CHECK_SOFT = 0x004000
MAGIC_NO_CHECK_APPTYPE = 0x008000
MAGIC_NO_CHECK_ELF = 0x010000
MAGIC_NO_CHECK_ASCII = 0x020000
MAGIC_NO_CHECK_TROFF = 0x040000
MAGIC_NO_CHECK_FORTRAN = 0x080000
MAGIC_NO_CHECK_TOKENS = 0x100000

MAGIC_PARAM_INDIR_MAX = 0
MAGIC_PARAM_NAME_MAX = 1
MAGIC_PARAM_ELF_PHNUM_MAX = 2
MAGIC_PARAM_ELF_SHNUM_MAX = 3
MAGIC_PARAM_ELF_NOTES_MAX = 4
MAGIC_PARAM_REGEX_MAX = 5
MAGIC_PARAM_BYTES_MAX = 6

