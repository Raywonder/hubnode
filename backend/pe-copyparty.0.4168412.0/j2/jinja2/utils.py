# -*- coding: utf-8 -*-
import json
import os
import re
import warnings
from collections import deque
from random import choice
from random import randrange
from string import ascii_letters as _letters
from string import digits as _digits
from threading import Lock

from markupsafe import escape
from markupsafe import Markup

from ._compat import abc
from ._compat import string_types
from ._compat import text_type
from ._compat import url_quote

missing = type("MissingType", (), {"__repr__": lambda x: "missing"})()

internal_code = set()

concat = u"".join

_slash_escape = "\\/" not in json.dumps("/")


def contextfunction(f):
    "a"
    f.contextfunction = True
    return f


def evalcontextfunction(f):
    "a"
    f.evalcontextfunction = True
    return f


def environmentfunction(f):
    "a"
    f.environmentfunction = True
    return f


def internalcode(f):
    "a"
    internal_code.add(f.__code__)
    return f


def is_undefined(obj):
    "a"
    from .runtime import Undefined

    return isinstance(obj, Undefined)


def consume(iterable):
    "a"
    for _ in iterable:
        pass


def clear_caches():
    "a"
    from .environment import _spontaneous_environments
    from .lexer import _lexer_cache

    _spontaneous_environments.clear()
    _lexer_cache.clear()


def import_string(import_name, silent=False):
    "a"
    try:
        if ":" in import_name:
            module, obj = import_name.split(":", 1)
        elif "." in import_name:
            module, _, obj = import_name.rpartition(".")
        else:
            return __import__(import_name)
        return getattr(__import__(module, None, None, [obj]), obj)
    except (ImportError, AttributeError):
        if not silent:
            raise


def open_if_exists(filename, mode="rb"):
    "a"
    if not os.path.isfile(filename):
        return None

    return open(filename, mode)


def object_type_repr(obj):
    "a"
    if obj is None:
        return "None"
    elif obj is Ellipsis:
        return "Ellipsis"

    cls = type(obj)

    if cls.__module__ in ("__builtin__", "builtins"):
        name = cls.__name__
    else:
        name = cls.__module__ + "." + cls.__name__

    return "%s object" % name


def pformat(obj, verbose=False):
    "a"
    try:
        from pretty import pretty

        return pretty(obj, verbose=verbose)
    except ImportError:
        from pprint import pformat

        return pformat(obj)


def urlize(text, trim_url_limit=None, rel=None, target=None):
    "a"
    trim_url = (
        lambda x, limit=trim_url_limit: limit is not None
        and (x[:limit] + (len(x) >= limit and "..." or ""))
        or x
    )
    words = re.split(r"(\s+)", text_type(escape(text)))
    rel_attr = rel and ' rel="%s"' % text_type(escape(rel)) or ""
    target_attr = target and ' target="%s"' % escape(target) or ""

    for i, word in enumerate(words):
        head, middle, tail = "", word, ""
        match = re.match(r"^([(<]|&lt;)+", middle)

        if match:
            head = match.group()
            middle = middle[match.end() :]

        if middle.endswith((")", ">", ".", ",", "\n", "&gt;")):
            match = re.search(r"([)>.,\n]|&gt;)+$", middle)

            if match:
                tail = match.group()
                middle = middle[: match.start()]

        if middle.startswith("www.") or (
            "@" not in middle
            and not middle.startswith("http://")
            and not middle.startswith("https://")
            and len(middle) > 0
            and middle[0] in _letters + _digits
            and (
                middle.endswith(".org")
                or middle.endswith(".net")
                or middle.endswith(".com")
            )
        ):
            middle = '<a href="http://%s"%s%s>%s</a>' % (
                middle,
                rel_attr,
                target_attr,
                trim_url(middle),
            )

        if middle.startswith("http://") or middle.startswith("https://"):
            middle = '<a href="%s"%s%s>%s</a>' % (
                middle,
                rel_attr,
                target_attr,
                trim_url(middle),
            )

        if (
            "@" in middle
            and not middle.startswith("www.")
            and ":" not in middle
            and re.match(r"^\S+@\w[\w.-]*\.\w+$", middle)
        ):
            middle = '<a href="mailto:%s">%s</a>' % (middle, middle)

        words[i] = head + middle + tail

    return u"".join(words)


def unicode_urlencode(obj, charset="utf-8", for_qs=False):
    "a"
    if not isinstance(obj, string_types):
        obj = text_type(obj)

    if isinstance(obj, text_type):
        obj = obj.encode(charset)

    safe = b"" if for_qs else b"/"
    rv = url_quote(obj, safe)

    if not isinstance(rv, text_type):
        rv = rv.decode("utf-8")

    if for_qs:
        rv = rv.replace("%20", "+")

    return rv


class LRUCache(object):
    "a"


    def __init__(self, capacity):
        self.capacity = capacity
        self._mapping = {}
        self._queue = deque()
        self._postinit()

    def _postinit(self):

        self._popleft = self._queue.popleft
        self._pop = self._queue.pop
        self._remove = self._queue.remove
        self._wlock = Lock()
        self._append = self._queue.append

    def __getstate__(self):
        return {
            "capacity": self.capacity,
            "_mapping": self._mapping,
            "_queue": self._queue,
        }

    def __setstate__(self, d):
        self.__dict__.update(d)
        self._postinit()

    def __getnewargs__(self):
        return (self.capacity,)

    def copy(self):
        "a"
        rv = self.__class__(self.capacity)
        rv._mapping.update(self._mapping)
        rv._queue.extend(self._queue)
        return rv

    def get(self, key, default=None):
        "a"
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        "a"
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def clear(self):
        "a"
        self._wlock.acquire()
        try:
            self._mapping.clear()
            self._queue.clear()
        finally:
            self._wlock.release()

    def __contains__(self, key):
        "a"
        return key in self._mapping

    def __len__(self):
        "a"
        return len(self._mapping)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self._mapping)

    def __getitem__(self, key):
        "a"
        self._wlock.acquire()
        try:
            rv = self._mapping[key]
            if self._queue[-1] != key:
                try:
                    self._remove(key)
                except ValueError:

                    pass
                self._append(key)
            return rv
        finally:
            self._wlock.release()

    def __setitem__(self, key, value):
        "a"
        self._wlock.acquire()
        try:
            if key in self._mapping:
                self._remove(key)
            elif len(self._mapping) == self.capacity:
                del self._mapping[self._popleft()]
            self._append(key)
            self._mapping[key] = value
        finally:
            self._wlock.release()

    def __delitem__(self, key):
        "a"
        self._wlock.acquire()
        try:
            del self._mapping[key]
            try:
                self._remove(key)
            except ValueError:
                pass
        finally:
            self._wlock.release()

    def items(self):
        "a"
        result = [(key, self._mapping[key]) for key in list(self._queue)]
        result.reverse()
        return result

    def iteritems(self):
        "a"
        warnings.warn(
            "'iteritems()' will be removed in version 3.0. Use"
            " 'iter(cache.items())' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self.items())

    def values(self):
        "a"
        return [x[1] for x in self.items()]

    def itervalue(self):
        "a"
        warnings.warn(
            "'itervalue()' will be removed in version 3.0. Use"
            " 'iter(cache.values())' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self.values())

    def itervalues(self):
        "a"
        warnings.warn(
            "'itervalues()' will be removed in version 3.0. Use"
            " 'iter(cache.values())' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self.values())

    def keys(self):
        "a"
        return list(self)

    def iterkeys(self):
        "a"
        warnings.warn(
            "'iterkeys()' will be removed in version 3.0. Use"
            " 'iter(cache.keys())' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(self)

    def __iter__(self):
        return reversed(tuple(self._queue))

    def __reversed__(self):
        "a"
        return iter(tuple(self._queue))

    __copy__ = copy


abc.MutableMapping.register(LRUCache)


def select_autoescape(
    enabled_extensions=("html", "htm", "xml"),
    disabled_extensions=(),
    default_for_string=True,
    default=False,
):
    "a"
    enabled_patterns = tuple("." + x.lstrip(".").lower() for x in enabled_extensions)
    disabled_patterns = tuple("." + x.lstrip(".").lower() for x in disabled_extensions)

    def autoescape(template_name):
        if template_name is None:
            return default_for_string
        template_name = template_name.lower()
        if template_name.endswith(enabled_patterns):
            return True
        if template_name.endswith(disabled_patterns):
            return False
        return default

    return autoescape


def htmlsafe_json_dumps(obj, dumper=None, **kwargs):
    "a"
    if dumper is None:
        dumper = json.dumps
    rv = (
        dumper(obj, **kwargs)
        .replace(u"<", u"\\u003c")
        .replace(u">", u"\\u003e")
        .replace(u"&", u"\\u0026")
        .replace(u"'", u"\\u0027")
    )
    return Markup(rv)


class Cycler(object):
    "a"

    def __init__(self, *items):
        if not items:
            raise RuntimeError("at least one item has to be provided")
        self.items = items
        self.pos = 0

    def reset(self):
        "a"
        self.pos = 0

    @property
    def current(self):
        "a"
        return self.items[self.pos]

    def next(self):
        "a"
        rv = self.current
        self.pos = (self.pos + 1) % len(self.items)
        return rv

    __next__ = next


class Joiner(object):
    "a"

    def __init__(self, sep=u", "):
        self.sep = sep
        self.used = False

    def __call__(self):
        if not self.used:
            self.used = True
            return u""
        return self.sep


class Namespace(object):
    "a"

    def __init__(*args, **kwargs):
        self, args = args[0], args[1:]
        self.__attrs = dict(*args, **kwargs)

    def __getattribute__(self, name):

        if name in {"_Namespace__attrs", "__class__"}:
            return object.__getattribute__(self, name)
        try:
            return self.__attrs[name]
        except KeyError:
            raise AttributeError(name)

    def __setitem__(self, name, value):
        self.__attrs[name] = value

    def __repr__(self):
        return "<Namespace %r>" % self.__attrs

try:
    exec("async def _():\n async for _ in ():\n  yield _")
    have_async_gen = True
except SyntaxError:
    have_async_gen = False


def soft_unicode(s):
    from markupsafe import soft_unicode

    warnings.warn(
        "'jinja2.utils.soft_unicode' will be removed in version 3.0."
        " Use 'markupsafe.soft_unicode' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return soft_unicode(s)
