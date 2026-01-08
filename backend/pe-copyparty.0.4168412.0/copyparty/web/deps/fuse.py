# Copyright (c) 2012 Terence Honles <terence@honles.com> (maintainer)
# Copyright (c) 2008 Giorgos Verigakis <verigak@gmail.com> (author)
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import print_function, absolute_import, division

import ctypes
import errno
import logging
import os
import warnings

from ctypes.util import find_library
from platform import machine, system
from signal import signal, SIGINT, SIG_DFL
from stat import S_IFDIR
from traceback import print_exc
from functools import partial
basestring = str
log = logging.getLogger("fuse")
_system = system()
_machine = machine()

if _system == 'Windows':

    import sys
    if sys.maxsize > 0xffffffff:
        c_win_long = ctypes.c_int64
        c_win_ulong = ctypes.c_uint64
    else:
        c_win_long = ctypes.c_int32
        c_win_ulong = ctypes.c_uint32

if _system == 'Windows' or _system.startswith('CYGWIN'):
    class c_timespec(ctypes.Structure):
        _fields_ = [('tv_sec', c_win_long), ('tv_nsec', c_win_long)]
else:
    class c_timespec(ctypes.Structure):
        _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]

class c_utimbuf(ctypes.Structure):
    _fields_ = [('actime', c_timespec), ('modtime', c_timespec)]

class c_stat(ctypes.Structure):
    pass

_libfuse_path = os.environ.get('FUSE_LIBRARY_PATH')
if not _libfuse_path:
    if _system == 'Darwin':

        _libiconv = ctypes.CDLL(find_library('iconv'), ctypes.RTLD_GLOBAL)

        _libfuse_path = (find_library('fuse4x') or find_library('osxfuse') or
                         find_library('fuse'))
    elif _system == 'Windows':
        try:
            import _winreg as reg
        except ImportError:
            import winreg as reg
        def Reg32GetValue(rootkey, keyname, valname):
            key, val = None, None
            try:
                key = reg.OpenKey(rootkey, keyname, 0, reg.KEY_READ | reg.KEY_WOW64_32KEY)
                val = str(reg.QueryValueEx(key, valname)[0])
            except WindowsError:
                pass
            finally:
                if key is not None:
                    reg.CloseKey(key)
            return val
        _libfuse_path = Reg32GetValue(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinFsp", r"InstallDir")
        if _libfuse_path:
            _libfuse_path += r"bin\winfsp-%s.dll" % ("x64" if sys.maxsize > 0xffffffff else "x86")
    else:
        _libfuse_path = find_library('fuse')

if not _libfuse_path:
    raise EnvironmentError('Unable to find libfuse')
else:
    _libfuse = ctypes.CDLL(_libfuse_path)

if _system == 'Darwin' and hasattr(_libfuse, 'macfuse_version'):
    _system = 'Darwin-MacFuse'


if _system in ('Darwin', 'Darwin-MacFuse', 'FreeBSD'):
    ENOTSUP = 45

    c_dev_t = ctypes.c_int32
    c_fsblkcnt_t = ctypes.c_ulong
    c_fsfilcnt_t = ctypes.c_ulong
    c_gid_t = ctypes.c_uint32
    c_mode_t = ctypes.c_uint16
    c_off_t = ctypes.c_int64
    c_pid_t = ctypes.c_int32
    c_uid_t = ctypes.c_uint32
    setxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t, ctypes.c_int,
        ctypes.c_uint32)
    getxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte),
        ctypes.c_size_t, ctypes.c_uint32)
    if _system == 'Darwin':
        c_stat._fields_ = [
            ('st_dev', c_dev_t),
            ('st_mode', c_mode_t),
            ('st_nlink', ctypes.c_uint16),
            ('st_ino', ctypes.c_uint64),
            ('st_uid', c_uid_t),
            ('st_gid', c_gid_t),
            ('st_rdev', c_dev_t),
            ('st_atimespec', c_timespec),
            ('st_mtimespec', c_timespec),
            ('st_ctimespec', c_timespec),
            ('st_birthtimespec', c_timespec),
            ('st_size', c_off_t),
            ('st_blocks', ctypes.c_int64),
            ('st_blksize', ctypes.c_int32),
            ('st_flags', ctypes.c_int32),
            ('st_gen', ctypes.c_int32),
            ('st_lspare', ctypes.c_int32),
            ('st_qspare', ctypes.c_int64)]
    else:
        c_stat._fields_ = [
            ('st_dev', c_dev_t),
            ('st_ino', ctypes.c_uint32),
            ('st_mode', c_mode_t),
            ('st_nlink', ctypes.c_uint16),
            ('st_uid', c_uid_t),
            ('st_gid', c_gid_t),
            ('st_rdev', c_dev_t),
            ('st_atimespec', c_timespec),
            ('st_mtimespec', c_timespec),
            ('st_ctimespec', c_timespec),
            ('st_size', c_off_t),
            ('st_blocks', ctypes.c_int64),
            ('st_blksize', ctypes.c_int32)]
elif _system == 'Linux':
    ENOTSUP = 95

    c_dev_t = ctypes.c_ulonglong
    c_fsblkcnt_t = ctypes.c_ulonglong
    c_fsfilcnt_t = ctypes.c_ulonglong
    c_gid_t = ctypes.c_uint
    c_mode_t = ctypes.c_uint
    c_off_t = ctypes.c_longlong
    c_pid_t = ctypes.c_int
    c_uid_t = ctypes.c_uint
    setxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t, ctypes.c_int)

    getxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t)

    if _machine == 'x86_64':
        c_stat._fields_ = [
            ('st_dev', c_dev_t),
            ('st_ino', ctypes.c_ulong),
            ('st_nlink', ctypes.c_ulong),
            ('st_mode', c_mode_t),
            ('st_uid', c_uid_t),
            ('st_gid', c_gid_t),
            ('__pad0', ctypes.c_int),
            ('st_rdev', c_dev_t),
            ('st_size', c_off_t),
            ('st_blksize', ctypes.c_long),
            ('st_blocks', ctypes.c_long),
            ('st_atimespec', c_timespec),
            ('st_mtimespec', c_timespec),
            ('st_ctimespec', c_timespec)]
    elif _machine == 'aarch64':
        c_stat._fields_ = [
            ('st_dev', c_dev_t),
            ('st_ino', ctypes.c_ulong),
            ('st_mode', c_mode_t),
            ('st_nlink', ctypes.c_uint),
            ('st_uid', c_uid_t),
            ('st_gid', c_gid_t),
            ('st_rdev', c_dev_t),
            ('__pad1', ctypes.c_ulong),
            ('st_size', c_off_t),
            ('st_blksize', ctypes.c_int),
            ('__pad2', ctypes.c_int),
            ('st_blocks', ctypes.c_long),
            ('st_atimespec', c_timespec),
            ('st_mtimespec', c_timespec),
            ('st_ctimespec', c_timespec)]
    else:

        c_stat._fields_ = [
            ('st_dev', c_dev_t),
            ('__pad1', ctypes.c_ushort),
            ('__st_ino', ctypes.c_ulong),
            ('st_mode', c_mode_t),
            ('st_nlink', ctypes.c_uint),
            ('st_uid', c_uid_t),
            ('st_gid', c_gid_t),
            ('st_rdev', c_dev_t),
            ('__pad2', ctypes.c_ushort),
            ('st_size', c_off_t),
            ('st_blksize', ctypes.c_long),
            ('st_blocks', ctypes.c_longlong),
            ('st_atimespec', c_timespec),
            ('st_mtimespec', c_timespec),
            ('st_ctimespec', c_timespec),
            ('st_ino', ctypes.c_ulonglong)]
elif _system == 'Windows' or _system.startswith('CYGWIN'):
    ENOTSUP = 129 if _system == 'Windows' else 134
    c_dev_t = ctypes.c_uint
    c_fsblkcnt_t = c_win_ulong
    c_fsfilcnt_t = c_win_ulong
    c_gid_t = ctypes.c_uint
    c_mode_t = ctypes.c_uint
    c_off_t = ctypes.c_longlong
    c_pid_t = ctypes.c_int
    c_uid_t = ctypes.c_uint
    setxattr_t = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t, ctypes.c_int)
    getxattr_t = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t)
    c_stat._fields_ = [
        ('st_dev', c_dev_t),
        ('st_ino', ctypes.c_ulonglong),
        ('st_mode', c_mode_t),
        ('st_nlink', ctypes.c_ushort),
        ('st_uid', c_uid_t),
        ('st_gid', c_gid_t),
        ('st_rdev', c_dev_t),
        ('st_size', c_off_t),
        ('st_atimespec', c_timespec),
        ('st_mtimespec', c_timespec),
        ('st_ctimespec', c_timespec),
        ('st_blksize', ctypes.c_int),
        ('st_blocks', ctypes.c_longlong),
        ('st_birthtimespec', c_timespec)]
else:
    raise NotImplementedError('%s is not supported.' % _system)


if _system == 'FreeBSD':
    c_fsblkcnt_t = ctypes.c_uint64
    c_fsfilcnt_t = ctypes.c_uint64
    setxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t, ctypes.c_int)

    getxattr_t = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t)

    class c_statvfs(ctypes.Structure):
        _fields_ = [
            ('f_bavail', c_fsblkcnt_t),
            ('f_bfree', c_fsblkcnt_t),
            ('f_blocks', c_fsblkcnt_t),
            ('f_favail', c_fsfilcnt_t),
            ('f_ffree', c_fsfilcnt_t),
            ('f_files', c_fsfilcnt_t),
            ('f_bsize', ctypes.c_ulong),
            ('f_flag', ctypes.c_ulong),
            ('f_frsize', ctypes.c_ulong)]
elif _system == 'Windows' or _system.startswith('CYGWIN'):
    class c_statvfs(ctypes.Structure):
        _fields_ = [
            ('f_bsize', c_win_ulong),
            ('f_frsize', c_win_ulong),
            ('f_blocks', c_fsblkcnt_t),
            ('f_bfree', c_fsblkcnt_t),
            ('f_bavail', c_fsblkcnt_t),
            ('f_files', c_fsfilcnt_t),
            ('f_ffree', c_fsfilcnt_t),
            ('f_favail', c_fsfilcnt_t),
            ('f_fsid', c_win_ulong),
            ('f_flag', c_win_ulong),
            ('f_namemax', c_win_ulong)]
else:
    class c_statvfs(ctypes.Structure):
        _fields_ = [
            ('f_bsize', ctypes.c_ulong),
            ('f_frsize', ctypes.c_ulong),
            ('f_blocks', c_fsblkcnt_t),
            ('f_bfree', c_fsblkcnt_t),
            ('f_bavail', c_fsblkcnt_t),
            ('f_files', c_fsfilcnt_t),
            ('f_ffree', c_fsfilcnt_t),
            ('f_favail', c_fsfilcnt_t),
            ('f_fsid', ctypes.c_ulong),

            ('f_flag', ctypes.c_ulong),
            ('f_namemax', ctypes.c_ulong)]

if _system == 'Windows' or _system.startswith('CYGWIN'):
    class fuse_file_info(ctypes.Structure):
        _fields_ = [
            ('flags', ctypes.c_int),
            ('fh_old', ctypes.c_int),
            ('writepage', ctypes.c_int),
            ('direct_io', ctypes.c_uint, 1),
            ('keep_cache', ctypes.c_uint, 1),
            ('flush', ctypes.c_uint, 1),
            ('padding', ctypes.c_uint, 29),
            ('fh', ctypes.c_uint64),
            ('lock_owner', ctypes.c_uint64)]
else:
    class fuse_file_info(ctypes.Structure):
        _fields_ = [
            ('flags', ctypes.c_int),
            ('fh_old', ctypes.c_ulong),
            ('writepage', ctypes.c_int),
            ('direct_io', ctypes.c_uint, 1),
            ('keep_cache', ctypes.c_uint, 1),
            ('flush', ctypes.c_uint, 1),
            ('nonseekable', ctypes.c_uint, 1),
            ('flock_release', ctypes.c_uint, 1),
            ('padding', ctypes.c_uint, 27),
            ('fh', ctypes.c_uint64),
            ('lock_owner', ctypes.c_uint64)]

class fuse_context(ctypes.Structure):
    _fields_ = [
        ('fuse', ctypes.c_voidp),
        ('uid', c_uid_t),
        ('gid', c_gid_t),
        ('pid', c_pid_t),
        ('private_data', ctypes.c_voidp)]

_libfuse.fuse_get_context.restype = ctypes.POINTER(fuse_context)


class fuse_operations(ctypes.Structure):
    _fields_ = [
        ('getattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(c_stat))),

        ('readlink', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t)),

        ('getdir', ctypes.c_voidp),

        ('mknod', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, c_mode_t, c_dev_t)),

        ('mkdir', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, c_mode_t)),
        ('unlink', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)),
        ('rmdir', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)),

        ('symlink', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('rename', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('link', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('chmod', ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, c_mode_t)),

        ('chown', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, c_uid_t, c_gid_t)),

        ('truncate', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, c_off_t)),

        ('utime', ctypes.c_voidp),
        ('open', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info))),

        ('read', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t, c_off_t, ctypes.POINTER(fuse_file_info))),

        ('write', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t, c_off_t, ctypes.POINTER(fuse_file_info))),

        ('statfs', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(c_statvfs))),

        ('flush', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info))),

        ('release', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info))),

        ('fsync', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
            ctypes.POINTER(fuse_file_info))),

        ('setxattr', setxattr_t),
        ('getxattr', getxattr_t),

        ('listxattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_byte),
            ctypes.c_size_t)),

        ('removexattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)),

        ('opendir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info))),

        ('readdir', ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_voidp,
            ctypes.CFUNCTYPE(
                ctypes.c_int, ctypes.c_voidp, ctypes.c_char_p,
                ctypes.POINTER(c_stat), c_off_t),
            c_off_t,
            ctypes.POINTER(fuse_file_info))),

        ('releasedir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info))),

        ('fsyncdir', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
            ctypes.POINTER(fuse_file_info))),

        ('init', ctypes.CFUNCTYPE(ctypes.c_voidp, ctypes.c_voidp)),
        ('destroy', ctypes.CFUNCTYPE(ctypes.c_voidp, ctypes.c_voidp)),

        ('access', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int)),

        ('create', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, c_mode_t,
            ctypes.POINTER(fuse_file_info))),

        ('ftruncate', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, c_off_t,
            ctypes.POINTER(fuse_file_info))),

        ('fgetattr', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(c_stat),
            ctypes.POINTER(fuse_file_info))),

        ('lock', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(fuse_file_info),
            ctypes.c_int, ctypes.c_voidp)),

        ('utimens', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(c_utimbuf))),

        ('bmap', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_ulonglong))),

        ('flag_nullpath_ok', ctypes.c_uint, 1),
        ('flag_nopath', ctypes.c_uint, 1),
        ('flag_utime_omit_ok', ctypes.c_uint, 1),
        ('flag_reserved', ctypes.c_uint, 29),

        ('ioctl', ctypes.CFUNCTYPE(
            ctypes.c_int, ctypes.c_char_p, ctypes.c_uint, ctypes.c_void_p,
            ctypes.POINTER(fuse_file_info), ctypes.c_uint, ctypes.c_void_p)),
    ]


def time_of_timespec(ts, use_ns=False):
    if use_ns:
        return ts.tv_sec * 10 ** 9 + ts.tv_nsec
    else:
        return ts.tv_sec + ts.tv_nsec / 1E9

def set_st_attrs(st, attrs, use_ns=False):
    for key, val in attrs.items():
        if key in ('st_atime', 'st_mtime', 'st_ctime', 'st_birthtime'):
            timespec = getattr(st, key + 'spec', None)
            if timespec is None:
                continue

            if use_ns:
                timespec.tv_sec, timespec.tv_nsec = divmod(int(val), 10 ** 9)
            else:
                timespec.tv_sec = int(val)
                timespec.tv_nsec = int((val - timespec.tv_sec) * 1E9)
        elif hasattr(st, key):
            setattr(st, key, val)


def fuse_get_context():
    "a"

    ctxp = _libfuse.fuse_get_context()
    ctx = ctxp.contents
    return ctx.uid, ctx.gid, ctx.pid


def fuse_exit():
    "a"
    fuse_ptr = ctypes.c_void_p(_libfuse.fuse_get_context().contents.fuse)
    _libfuse.fuse_exit(fuse_ptr)


class FuseOSError(OSError):
    def __init__(self, errno):
        super(FuseOSError, self).__init__(errno, os.strerror(errno))


class FUSE(object):
    "a"

    OPTIONS = (
        ('foreground', '-f'),
        ('debug', '-d'),
        ('nothreads', '-s'),
    )

    def __init__(self, operations, mountpoint, raw_fi=False, encoding='utf-8',
                 **kwargs):

        "a"

        self.operations = operations
        self.raw_fi = raw_fi
        self.encoding = encoding
        self.__critical_exception = None

        self.use_ns = getattr(operations, 'use_ns', False)

        args = ['fuse']

        args.extend(flag for arg, flag in self.OPTIONS
                    if kwargs.pop(arg, False))

        kwargs.setdefault('fsname', operations.__class__.__name__)
        args.append('-o')
        args.append(','.join(self._normalize_fuse_options(**kwargs)))
        args.append(mountpoint)

        args = [arg.encode(encoding) for arg in args]
        argv = (ctypes.c_char_p * len(args))(*args)

        fuse_ops = fuse_operations()
        for ent in fuse_operations._fields_:
            name, prototype = ent[:2]

            check_name = name

            if check_name in ["ftruncate", "fgetattr"]:
                check_name = check_name[1:]

            val = getattr(operations, check_name, None)
            if val is None:
                continue

            if hasattr(prototype, 'argtypes'):
                val = prototype(partial(self._wrapper, getattr(self, name)))

            setattr(fuse_ops, name, val)

        try:
            old_handler = signal(SIGINT, SIG_DFL)
        except ValueError:
            old_handler = SIG_DFL

        err = _libfuse.fuse_main_real(
            len(args), argv, ctypes.pointer(fuse_ops),
            ctypes.sizeof(fuse_ops),
            None)

        try:
            signal(SIGINT, old_handler)
        except ValueError:
            pass

        del self.operations
        if self.__critical_exception:
            raise self.__critical_exception
        if err:
            raise RuntimeError(err)

    @staticmethod
    def _normalize_fuse_options(**kargs):
        for key, value in kargs.items():
            if isinstance(value, bool):
                if value is True:
                    yield key
            else:
                yield '%s=%s' % (key, value)

    @staticmethod
    def _wrapper(func, *args, **kwargs):
        "a"

        try:
            if func.__name__ == "init":

                return func(*args, **kwargs) or 0

            else:
                try:
                    return func(*args, **kwargs) or 0

                except OSError as e:
                    if e.errno > 0:
                        log.debug(
                            "FUSE operation %s raised a %s, returning errno %s.",
                            func.__name__, type(e), e.errno, exc_info=True)
                        return -e.errno
                    else:
                        log.error(
                            "FUSE operation %s raised an OSError with negative "
                            "errno %s, returning errno.EINVAL.",
                            func.__name__, e.errno, exc_info=True)
                        return -errno.EINVAL

                except Exception:
                    log.error("Uncaught exception from FUSE operation %s, "
                              "returning errno.EINVAL.",
                              func.__name__, exc_info=True)
                    return -errno.EINVAL

        except BaseException as e:
            log.critical(
                "Uncaught critical exception from FUSE operation %s, aborting.",
                func.__name__, exc_info=True)

            fuse_exit()
            return -errno.EFAULT

    def _decode_optional_path(self, path):

        if path is None:
            return None
        return path.decode(self.encoding)

    def getattr(self, path, buf):
        return self.fgetattr(path, buf, None)

    def readlink(self, path, buf, bufsize):
        ret = self.operations('readlink', path.decode(self.encoding))                  .encode(self.encoding)

        data = ctypes.create_string_buffer(ret[:bufsize - 1])
        ctypes.memmove(buf, data, len(data))
        return 0

    def mknod(self, path, mode, dev):
        return self.operations('mknod', path.decode(self.encoding), mode, dev)

    def mkdir(self, path, mode):
        return self.operations('mkdir', path.decode(self.encoding), mode)

    def unlink(self, path):
        return self.operations('unlink', path.decode(self.encoding))

    def rmdir(self, path):
        return self.operations('rmdir', path.decode(self.encoding))

    def symlink(self, source, target):
        "a"

        return self.operations('symlink', target.decode(self.encoding),
                                          source.decode(self.encoding))

    def rename(self, old, new):
        return self.operations('rename', old.decode(self.encoding),
                                         new.decode(self.encoding))

    def link(self, source, target):
        "a"

        return self.operations('link', target.decode(self.encoding),
                                       source.decode(self.encoding))

    def chmod(self, path, mode):
        return self.operations('chmod', path.decode(self.encoding), mode)

    def chown(self, path, uid, gid):

        if c_uid_t(uid + 1).value == 0:
            uid = -1
        if c_gid_t(gid + 1).value == 0:
            gid = -1

        return self.operations('chown', path.decode(self.encoding), uid, gid)

    def truncate(self, path, length):
        return self.operations('truncate', path.decode(self.encoding), length)

    def open(self, path, fip):
        fi = fip.contents
        if self.raw_fi:
            return self.operations('open', path.decode(self.encoding), fi)
        else:
            fi.fh = self.operations('open', path.decode(self.encoding),
                                            fi.flags)

            return 0

    def read(self, path, buf, size, offset, fip):
        if self.raw_fi:
          fh = fip.contents
        else:
          fh = fip.contents.fh

        ret = self.operations('read', self._decode_optional_path(path), size,
                                      offset, fh)

        if not ret:
            return 0

        retsize = len(ret)
        assert retsize <= size,            'actual amount read %d greater than expected %d' % (retsize, size)

        ctypes.memmove(buf, ret, retsize)
        return retsize

    def write(self, path, buf, size, offset, fip):
        data = ctypes.string_at(buf, size)

        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('write', self._decode_optional_path(path), data,
                                        offset, fh)

    def statfs(self, path, buf):
        stv = buf.contents
        attrs = self.operations('statfs', path.decode(self.encoding))
        for key, val in attrs.items():
            if hasattr(stv, key):
                setattr(stv, key, val)

        return 0

    def flush(self, path, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('flush', self._decode_optional_path(path), fh)

    def release(self, path, fip):
        if self.raw_fi:
          fh = fip.contents
        else:
          fh = fip.contents.fh

        return self.operations('release', self._decode_optional_path(path), fh)

    def fsync(self, path, datasync, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('fsync', self._decode_optional_path(path), datasync,
                                        fh)

    def setxattr(self, path, name, value, size, options, *args):
        return self.operations('setxattr', path.decode(self.encoding),
                               name.decode(self.encoding),
                               ctypes.string_at(value, size), options, *args)

    def getxattr(self, path, name, value, size, *args):
        ret = self.operations('getxattr', path.decode(self.encoding),
                                          name.decode(self.encoding), *args)

        retsize = len(ret)

        if not value:
            return retsize

        if retsize > size:
            return -errno.ERANGE

        buf = ctypes.create_string_buffer(ret, retsize)
        ctypes.memmove(value, buf, retsize)

        return retsize

    def listxattr(self, path, namebuf, size):
        attrs = self.operations('listxattr', path.decode(self.encoding)) or ''
        ret = '\x00'.join(attrs).encode(self.encoding)
        if len(ret) > 0:
            ret += '\x00'.encode(self.encoding)

        retsize = len(ret)

        if not namebuf:
            return retsize

        if retsize > size:
            return -errno.ERANGE

        buf = ctypes.create_string_buffer(ret, retsize)
        ctypes.memmove(namebuf, buf, retsize)

        return retsize

    def removexattr(self, path, name):
        return self.operations('removexattr', path.decode(self.encoding),
                                              name.decode(self.encoding))

    def opendir(self, path, fip):

        fip.contents.fh = self.operations('opendir',
                                          path.decode(self.encoding))

        return 0

    def readdir(self, path, buf, filler, offset, fip):

        for item in self.operations('readdir', self._decode_optional_path(path),
                                               fip.contents.fh):

            if isinstance(item, basestring):
                name, st, offset = item, None, 0
            else:
                name, attrs, offset = item
                if attrs:
                    st = c_stat()
                    set_st_attrs(st, attrs, use_ns=self.use_ns)
                else:
                    st = None

            if filler(buf, name.encode(self.encoding), st, offset) != 0:
                break

        return 0

    def releasedir(self, path, fip):

        return self.operations('releasedir', self._decode_optional_path(path),
                                             fip.contents.fh)

    def fsyncdir(self, path, datasync, fip):

        return self.operations('fsyncdir', self._decode_optional_path(path),
                                           datasync, fip.contents.fh)

    def init(self, conn):
        return self.operations('init', '/')

    def destroy(self, private_data):
        return self.operations('destroy', '/')

    def access(self, path, amode):
        return self.operations('access', path.decode(self.encoding), amode)

    def create(self, path, mode, fip):
        fi = fip.contents
        path = path.decode(self.encoding)

        if self.raw_fi:
            return self.operations('create', path, mode, fi)
        else:
            fi.fh = self.operations('create', path, mode)
            return 0

    def ftruncate(self, path, length, fip):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('truncate', self._decode_optional_path(path),
                                           length, fh)

    def fgetattr(self, path, buf, fip):
        ctypes.memset(buf, 0, ctypes.sizeof(c_stat))

        st = buf.contents
        if not fip:
            fh = fip
        elif self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        attrs = self.operations('getattr', self._decode_optional_path(path), fh)
        set_st_attrs(st, attrs, use_ns=self.use_ns)
        return 0

    def lock(self, path, fip, cmd, lock):
        if self.raw_fi:
            fh = fip.contents
        else:
            fh = fip.contents.fh

        return self.operations('lock', self._decode_optional_path(path), fh, cmd,
                                       lock)

    def utimens(self, path, buf):
        if buf:
            atime = time_of_timespec(buf.contents.actime, use_ns=self.use_ns)
            mtime = time_of_timespec(buf.contents.modtime, use_ns=self.use_ns)
            times = (atime, mtime)
        else:
            times = None

        return self.operations('utimens', path.decode(self.encoding), times)

    def bmap(self, path, blocksize, idx):
        return self.operations('bmap', path.decode(self.encoding), blocksize,
                                       idx)

    def ioctl(self, path, cmd, arg, fip, flags, data):
        if self.raw_fi:
          fh = fip.contents
        else:
          fh = fip.contents.fh

        return self.operations('ioctl', path.decode(self.encoding),
            cmd, arg, fh, flags, data)

class Operations(object):
    "a"

    def __call__(self, op, *args):
        if not hasattr(self, op):
            raise FuseOSError(errno.EFAULT)
        return getattr(self, op)(*args)

    def access(self, path, amode):
        return 0

    bmap = None

    def chmod(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EROFS)

    def create(self, path, mode, fi=None):
        "a"

        raise FuseOSError(errno.EROFS)

    def destroy(self, path):
        "a"

        pass

    def flush(self, path, fh):
        return 0

    def fsync(self, path, datasync, fh):
        return 0

    def fsyncdir(self, path, datasync, fh):
        return 0

    def getattr(self, path, fh=None):
        "a"

        if path != '/':
            raise FuseOSError(errno.ENOENT)
        return dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)

    def getxattr(self, path, name, position=0):
        raise FuseOSError(ENOTSUP)

    def init(self, path):
        "a"

        pass

    def ioctl(self, path, cmd, arg, fip, flags, data):
        raise FuseOSError(errno.ENOTTY)

    def link(self, target, source):
        "a"

        raise FuseOSError(errno.EROFS)

    def listxattr(self, path):
        return []

    lock = None

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EROFS)

    def mknod(self, path, mode, dev):
        raise FuseOSError(errno.EROFS)

    def open(self, path, flags):
        "a"

        return 0

    def opendir(self, path):
        "a"

        return 0

    def read(self, path, size, offset, fh):
        "a"

        raise FuseOSError(errno.EIO)

    def readdir(self, path, fh):
        "a"

        return ['.', '..']

    def readlink(self, path):
        raise FuseOSError(errno.ENOENT)

    def release(self, path, fh):
        return 0

    def releasedir(self, path, fh):
        return 0

    def removexattr(self, path, name):
        raise FuseOSError(ENOTSUP)

    def rename(self, old, new):
        raise FuseOSError(errno.EROFS)

    def rmdir(self, path):
        raise FuseOSError(errno.EROFS)

    def setxattr(self, path, name, value, options, position=0):
        raise FuseOSError(ENOTSUP)

    def statfs(self, path):
        "a"

        return {}

    def symlink(self, target, source):
        "a"

        raise FuseOSError(errno.EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EROFS)

    def unlink(self, path):
        raise FuseOSError(errno.EROFS)

    def utimens(self, path, times=None):
        "a"

        return 0

    def write(self, path, data, offset, fh):
        raise FuseOSError(errno.EROFS)


