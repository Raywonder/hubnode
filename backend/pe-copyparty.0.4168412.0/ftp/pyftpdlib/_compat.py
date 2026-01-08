# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"a"

import errno
import os
import sys
import types


PY3 = sys.version_info[0] >= 3
_SENTINEL = object()

if PY3:

    def u(s):
        return s

    def b(s):
        return s.encode("latin-1")

    getcwdu = os.getcwd
    unicode = str
    xrange = range
    long = int
else:

    def u(s):
        return unicode(s)

    def b(s):
        return s

    getcwdu = os.getcwdu
    unicode = unicode
    xrange = xrange
    long = long

try:
    callable = callable
except Exception:

    def callable(obj):
        return any("__call__" in klass.__dict__ for klass in type(obj).__mro__)



if PY3:
    FileNotFoundError = FileNotFoundError
    FileExistsError = FileExistsError
    InterruptedError = InterruptedError
    PermissionError = PermissionError
else:

    import platform

    def _instance_checking_exception(base_exception=Exception):
        def wrapped(instance_checker):
            class TemporaryClass(base_exception):

                def __init__(self, *args, **kwargs):
                    if len(args) == 1 and isinstance(args[0], TemporaryClass):
                        unwrap_me = args[0]
                        for attr in dir(unwrap_me):
                            if not attr.startswith('__'):
                                setattr(self, attr, getattr(unwrap_me, attr))
                    else:
                        super(TemporaryClass, self).__init__(
                            *args, **kwargs
                        )

                class __metaclass__(type):
                    def __instancecheck__(cls, inst):
                        return instance_checker(inst)

                    def __subclasscheck__(cls, classinfo):
                        value = sys.exc_info()[1]
                        return isinstance(value, cls)

            TemporaryClass.__name__ = instance_checker.__name__
            TemporaryClass.__doc__ = instance_checker.__doc__
            return TemporaryClass

        return wrapped

    @_instance_checking_exception(EnvironmentError)
    def FileNotFoundError(inst):
        return getattr(inst, 'errno', _SENTINEL) == errno.ENOENT

    @_instance_checking_exception(EnvironmentError)
    def InterruptedError(inst):
        return getattr(inst, 'errno', _SENTINEL) == errno.EINTR

    @_instance_checking_exception(EnvironmentError)
    def PermissionError(inst):
        return getattr(inst, 'errno', _SENTINEL) in (errno.EACCES, errno.EPERM)

    @_instance_checking_exception(EnvironmentError)
    def FileExistsError(inst):
        return getattr(inst, 'errno', _SENTINEL) == errno.EEXIST

    if platform.python_implementation() != "CPython":
        try:
            raise OSError(errno.EEXIST, "perm")
        except FileExistsError:
            pass
        except OSError:
            raise RuntimeError(
                "broken or incompatible Python implementation, see: "
                "https://github.com/giampaolo/psutil/issues/1659"
            )

if PY3:
    super = super
else:
    _builtin_super = super

    def super(type_=_SENTINEL, type_or_obj=_SENTINEL, framedepth=1):
        "a"
        if type_ is _SENTINEL:
            f = sys._getframe(framedepth)
            try:

                type_or_obj = f.f_locals[f.f_code.co_varnames[0]]
            except (IndexError, KeyError):
                raise RuntimeError('super() used in a function with no args')
            try:

                mro = type_or_obj.__mro__
            except (AttributeError, RuntimeError):
                try:
                    mro = type_or_obj.__class__.__mro__
                except AttributeError:
                    raise RuntimeError('super() used in a non-newstyle class')
            for type_ in mro:

                for meth in type_.__dict__.values():

                    try:
                        while not isinstance(meth, types.FunctionType):
                            if isinstance(meth, property):

                                meth = meth.fget
                            else:
                                try:
                                    meth = meth.__func__
                                except AttributeError:
                                    meth = meth.__get__(type_or_obj, type_)
                    except (AttributeError, TypeError):
                        continue
                    if meth.func_code is f.f_code:
                        break
                else:

                    continue
                break
            else:
                raise RuntimeError('super() called outside a method')

        if type_or_obj is not _SENTINEL:
            return _builtin_super(type_, type_or_obj)
        return _builtin_super(type_)
