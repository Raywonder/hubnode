# -*- coding: utf-8 -*-
"""
markupsafe
~~~~~~~~~~

Implements an escape function and a Markup string to replace HTML
special characters with safe representations.

:copyright: 2010 Pallets
:license: BSD-3-Clause
"""
import re
import string

from ._compat import int_types
from ._compat import iteritems
from ._compat import Mapping
from ._compat import PY2
from ._compat import string_types
from ._compat import text_type
from ._compat import unichr

__version__ = "1.1.1"

__all__ = ["Markup", "soft_unicode", "escape", "escape_silent"]

_striptags_re = re.compile(r"(<!--.*?-->|<[^>]*>)")
_entity_re = re.compile(r"&([^& ;]+);")


class Markup(text_type):
    "a"

    __slots__ = ()

    def __new__(cls, base=u"", encoding=None, errors="strict"):
        if hasattr(base, "__html__"):
            base = base.__html__()
        if encoding is None:
            return text_type.__new__(cls, base)
        return text_type.__new__(cls, base, encoding, errors)

    def __html__(self):
        return self

    def __add__(self, other):
        if isinstance(other, string_types) or hasattr(other, "__html__"):
            return self.__class__(super(Markup, self).__add__(self.escape(other)))
        return NotImplemented

    def __radd__(self, other):
        if hasattr(other, "__html__") or isinstance(other, string_types):
            return self.escape(other).__add__(self)
        return NotImplemented

    def __mul__(self, num):
        if isinstance(num, int_types):
            return self.__class__(text_type.__mul__(self, num))
        return NotImplemented

    __rmul__ = __mul__

    def __mod__(self, arg):
        if isinstance(arg, tuple):
            arg = tuple(_MarkupEscapeHelper(x, self.escape) for x in arg)
        else:
            arg = _MarkupEscapeHelper(arg, self.escape)
        return self.__class__(text_type.__mod__(self, arg))

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, text_type.__repr__(self))

    def join(self, seq):
        return self.__class__(text_type.join(self, map(self.escape, seq)))

    join.__doc__ = text_type.join.__doc__

    def split(self, *args, **kwargs):
        return list(map(self.__class__, text_type.split(self, *args, **kwargs)))

    split.__doc__ = text_type.split.__doc__

    def rsplit(self, *args, **kwargs):
        return list(map(self.__class__, text_type.rsplit(self, *args, **kwargs)))

    rsplit.__doc__ = text_type.rsplit.__doc__

    def splitlines(self, *args, **kwargs):
        return list(map(self.__class__, text_type.splitlines(self, *args, **kwargs)))

    splitlines.__doc__ = text_type.splitlines.__doc__

    def unescape(self):
        "a"
        from ._constants import HTML_ENTITIES

        def handle_match(m):
            name = m.group(1)
            if name in HTML_ENTITIES:
                return unichr(HTML_ENTITIES[name])
            try:
                if name[:2] in ("#x", "#X"):
                    return unichr(int(name[2:], 16))
                elif name.startswith("#"):
                    return unichr(int(name[1:]))
            except ValueError:
                pass

            return m.group()

        return _entity_re.sub(handle_match, text_type(self))

    def striptags(self):
        "a"
        stripped = u" ".join(_striptags_re.sub("", self).split())
        return Markup(stripped).unescape()

    @classmethod
    def escape(cls, s):
        "a"
        rv = escape(s)
        if rv.__class__ is not cls:
            return cls(rv)
        return rv

    def make_simple_escaping_wrapper(name):
        orig = getattr(text_type, name)

        def func(self, *args, **kwargs):
            args = _escape_argspec(list(args), enumerate(args), self.escape)
            _escape_argspec(kwargs, iteritems(kwargs), self.escape)
            return self.__class__(orig(self, *args, **kwargs))

        func.__name__ = orig.__name__
        func.__doc__ = orig.__doc__
        return func

    for method in (
        "__getitem__",
        "capitalize",
        "title",
        "lower",
        "upper",
        "replace",
        "ljust",
        "rjust",
        "lstrip",
        "rstrip",
        "center",
        "strip",
        "translate",
        "expandtabs",
        "swapcase",
        "zfill",
    ):
        locals()[method] = make_simple_escaping_wrapper(method)

    def partition(self, sep):
        return tuple(map(self.__class__, text_type.partition(self, self.escape(sep))))

    def rpartition(self, sep):
        return tuple(map(self.__class__, text_type.rpartition(self, self.escape(sep))))

    def format(self, *args, **kwargs):
        formatter = EscapeFormatter(self.escape)
        kwargs = _MagicFormatMapping(args, kwargs)
        return self.__class__(formatter.vformat(self, args, kwargs))

    def __html_format__(self, format_spec):
        if format_spec:
            raise ValueError("Unsupported format specification " "for Markup.")
        return self

    if hasattr(text_type, "__getslice__"):
        __getslice__ = make_simple_escaping_wrapper("__getslice__")

    del method, make_simple_escaping_wrapper


class _MagicFormatMapping(Mapping):
    "a"

    def __init__(self, args, kwargs):
        self._args = args
        self._kwargs = kwargs
        self._last_index = 0

    def __getitem__(self, key):
        if key == "":
            idx = self._last_index
            self._last_index += 1
            try:
                return self._args[idx]
            except LookupError:
                pass
            key = str(idx)
        return self._kwargs[key]

    def __iter__(self):
        return iter(self._kwargs)

    def __len__(self):
        return len(self._kwargs)


if hasattr(text_type, "format"):

    class EscapeFormatter(string.Formatter):
        def __init__(self, escape):
            self.escape = escape

        def format_field(self, value, format_spec):
            if hasattr(value, "__html_format__"):
                rv = value.__html_format__(format_spec)
            elif hasattr(value, "__html__"):
                if format_spec:
                    raise ValueError(
                        "Format specifier {0} given, but {1} does not"
                        " define __html_format__. A class that defines"
                        " __html__ must define __html_format__ to work"
                        " with format specifiers.".format(format_spec, type(value))
                    )
                rv = value.__html__()
            else:

                rv = string.Formatter.format_field(self, value, text_type(format_spec))
            return text_type(self.escape(rv))


def _escape_argspec(obj, iterable, escape):
    "a"
    for key, value in iterable:
        if hasattr(value, "__html__") or isinstance(value, string_types):
            obj[key] = escape(value)
    return obj


class _MarkupEscapeHelper(object):
    "a"

    def __init__(self, obj, escape):
        self.obj = obj
        self.escape = escape

    def __getitem__(self, item):
        return _MarkupEscapeHelper(self.obj[item], self.escape)

    def __str__(self):
        return text_type(self.escape(self.obj))

    __unicode__ = __str__

    def __repr__(self):
        return str(self.escape(repr(self.obj)))

    def __int__(self):
        return int(self.obj)

    def __float__(self):
        return float(self.obj)

try:
    from ._speedups import escape, escape_silent, soft_unicode
except ImportError:
    from ._native import escape, escape_silent, soft_unicode

if not PY2:
    soft_str = soft_unicode
    __all__.append("soft_str")
