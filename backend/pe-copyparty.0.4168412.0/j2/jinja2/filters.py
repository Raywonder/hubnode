# -*- coding: utf-8 -*-
"a"
import math
import random
import re
import warnings
from collections import namedtuple
from itertools import chain
from itertools import groupby

from markupsafe import escape
from markupsafe import Markup
from markupsafe import soft_unicode

from ._compat import abc
from ._compat import imap
from ._compat import iteritems
from ._compat import string_types
from ._compat import text_type
from .exceptions import FilterArgumentError
from .runtime import Undefined
from .utils import htmlsafe_json_dumps
from .utils import pformat
from .utils import unicode_urlencode
from .utils import urlize

_word_re = re.compile(r"\w+", re.UNICODE)
_word_beginning_split_re = re.compile(r"([-\s\(\{\[\<]+)", re.UNICODE)


def contextfilter(f):
    "a"
    f.contextfilter = True
    return f


def evalcontextfilter(f):
    "a"
    f.evalcontextfilter = True
    return f


def environmentfilter(f):
    "a"
    f.environmentfilter = True
    return f


def ignore_case(value):
    "a"
    return value.lower() if isinstance(value, string_types) else value


def make_attrgetter(environment, attribute, postprocess=None, default=None):
    "a"
    attribute = _prepare_attribute_parts(attribute)

    def attrgetter(item):
        for part in attribute:
            item = environment.getitem(item, part)

            if default and isinstance(item, Undefined):
                item = default

        if postprocess is not None:
            item = postprocess(item)

        return item

    return attrgetter


def make_multi_attrgetter(environment, attribute, postprocess=None):
    "a"
    attribute_parts = (
        attribute.split(",") if isinstance(attribute, string_types) else [attribute]
    )
    attribute = [
        _prepare_attribute_parts(attribute_part) for attribute_part in attribute_parts
    ]

    def attrgetter(item):
        items = [None] * len(attribute)
        for i, attribute_part in enumerate(attribute):
            item_i = item
            for part in attribute_part:
                item_i = environment.getitem(item_i, part)

            if postprocess is not None:
                item_i = postprocess(item_i)

            items[i] = item_i
        return items

    return attrgetter


def _prepare_attribute_parts(attr):
    if attr is None:
        return []
    elif isinstance(attr, string_types):
        return [int(x) if x.isdigit() else x for x in attr.split(".")]
    else:
        return [attr]


def do_forceescape(value):
    "a"
    if hasattr(value, "__html__"):
        value = value.__html__()
    return escape(text_type(value))


def do_urlencode(value):
    "a"
    if isinstance(value, string_types) or not isinstance(value, abc.Iterable):
        return unicode_urlencode(value)

    if isinstance(value, dict):
        items = iteritems(value)
    else:
        items = iter(value)

    return u"&".join(
        "%s=%s" % (unicode_urlencode(k, for_qs=True), unicode_urlencode(v, for_qs=True))
        for k, v in items
    )


@evalcontextfilter
def do_replace(eval_ctx, s, old, new, count=None):
    "a"
    if count is None:
        count = -1
    if not eval_ctx.autoescape:
        return text_type(s).replace(text_type(old), text_type(new), count)
    if (
        hasattr(old, "__html__")
        or hasattr(new, "__html__")
        and not hasattr(s, "__html__")
    ):
        s = escape(s)
    else:
        s = soft_unicode(s)
    return s.replace(soft_unicode(old), soft_unicode(new), count)


def do_upper(s):
    "a"
    return soft_unicode(s).upper()


def do_lower(s):
    "a"
    return soft_unicode(s).lower()


@evalcontextfilter
def do_xmlattr(_eval_ctx, d, autospace=True):
    "a"
    rv = u" ".join(
        u'%s="%s"' % (escape(key), escape(value))
        for key, value in iteritems(d)
        if value is not None and not isinstance(value, Undefined)
    )
    if autospace and rv:
        rv = u" " + rv
    if _eval_ctx.autoescape:
        rv = Markup(rv)
    return rv


def do_capitalize(s):
    "a"
    return soft_unicode(s).capitalize()


def do_title(s):
    "a"
    return "".join(
        [
            item[0].upper() + item[1:].lower()
            for item in _word_beginning_split_re.split(soft_unicode(s))
            if item
        ]
    )


def do_dictsort(value, case_sensitive=False, by="key", reverse=False):
    "a"
    if by == "key":
        pos = 0
    elif by == "value":
        pos = 1
    else:
        raise FilterArgumentError('You can only sort by either "key" or "value"')

    def sort_func(item):
        value = item[pos]

        if not case_sensitive:
            value = ignore_case(value)

        return value

    return sorted(value.items(), key=sort_func, reverse=reverse)


@environmentfilter
def do_sort(environment, value, reverse=False, case_sensitive=False, attribute=None):
    "a"
    key_func = make_multi_attrgetter(
        environment, attribute, postprocess=ignore_case if not case_sensitive else None
    )
    return sorted(value, key=key_func, reverse=reverse)


@environmentfilter
def do_unique(environment, value, case_sensitive=False, attribute=None):
    "a"
    getter = make_attrgetter(
        environment, attribute, postprocess=ignore_case if not case_sensitive else None
    )
    seen = set()

    for item in value:
        key = getter(item)

        if key not in seen:
            seen.add(key)
            yield item


def _min_or_max(environment, value, func, case_sensitive, attribute):
    it = iter(value)

    try:
        first = next(it)
    except StopIteration:
        return environment.undefined("No aggregated item, sequence was empty.")

    key_func = make_attrgetter(
        environment, attribute, postprocess=ignore_case if not case_sensitive else None
    )
    return func(chain([first], it), key=key_func)


@environmentfilter
def do_min(environment, value, case_sensitive=False, attribute=None):
    "a"
    return _min_or_max(environment, value, min, case_sensitive, attribute)


@environmentfilter
def do_max(environment, value, case_sensitive=False, attribute=None):
    "a"
    return _min_or_max(environment, value, max, case_sensitive, attribute)


def do_default(value, default_value=u"", boolean=False):
    "a"
    if isinstance(value, Undefined) or (boolean and not value):
        return default_value
    return value


@evalcontextfilter
def do_join(eval_ctx, value, d=u"", attribute=None):
    "a"
    if attribute is not None:
        value = imap(make_attrgetter(eval_ctx.environment, attribute), value)

    if not eval_ctx.autoescape:
        return text_type(d).join(imap(text_type, value))

    if not hasattr(d, "__html__"):
        value = list(value)
        do_escape = False
        for idx, item in enumerate(value):
            if hasattr(item, "__html__"):
                do_escape = True
            else:
                value[idx] = text_type(item)
        if do_escape:
            d = escape(d)
        else:
            d = text_type(d)
        return d.join(value)

    return soft_unicode(d).join(imap(soft_unicode, value))


def do_center(value, width=80):
    "a"
    return text_type(value).center(width)


@environmentfilter
def do_first(environment, seq):
    "a"
    try:
        return next(iter(seq))
    except StopIteration:
        return environment.undefined("No first item, sequence was empty.")


@environmentfilter
def do_last(environment, seq):
    "a"
    try:
        return next(iter(reversed(seq)))
    except StopIteration:
        return environment.undefined("No last item, sequence was empty.")


@contextfilter
def do_random(context, seq):
    "a"
    try:
        return random.choice(seq)
    except IndexError:
        return context.environment.undefined("No random item, sequence was empty.")


def do_filesizeformat(value, binary=False):
    "a"
    bytes = float(value)
    base = binary and 1024 or 1000
    prefixes = [
        (binary and "KiB" or "kB"),
        (binary and "MiB" or "MB"),
        (binary and "GiB" or "GB"),
        (binary and "TiB" or "TB"),
        (binary and "PiB" or "PB"),
        (binary and "EiB" or "EB"),
        (binary and "ZiB" or "ZB"),
        (binary and "YiB" or "YB"),
    ]
    if bytes == 1:
        return "1 Byte"
    elif bytes < base:
        return "%d Bytes" % bytes
    else:
        for i, prefix in enumerate(prefixes):
            unit = base ** (i + 2)
            if bytes < unit:
                return "%.1f %s" % ((base * bytes / unit), prefix)
        return "%.1f %s" % ((base * bytes / unit), prefix)


def do_pprint(value, verbose=False):
    "a"
    return pformat(value, verbose=verbose)


@evalcontextfilter
def do_urlize(
    eval_ctx, value, trim_url_limit=None, nofollow=False, target=None, rel=None
):
    "a"
    policies = eval_ctx.environment.policies
    rel = set((rel or "").split() or [])
    if nofollow:
        rel.add("nofollow")
    rel.update((policies["urlize.rel"] or "").split())
    if target is None:
        target = policies["urlize.target"]
    rel = " ".join(sorted(rel)) or None
    rv = urlize(value, trim_url_limit, rel=rel, target=target)
    if eval_ctx.autoescape:
        rv = Markup(rv)
    return rv


def do_indent(s, width=4, first=False, blank=False, indentfirst=None):
    "a"
    if indentfirst is not None:
        warnings.warn(
            "The 'indentfirst' argument is renamed to 'first' and will"
            " be removed in version 3.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        first = indentfirst

    indention = u" " * width
    newline = u"\n"

    if isinstance(s, Markup):
        indention = Markup(indention)
        newline = Markup(newline)

    s += newline

    if blank:
        rv = (newline + indention).join(s.splitlines())
    else:
        lines = s.splitlines()
        rv = lines.pop(0)

        if lines:
            rv += newline + newline.join(
                indention + line if line else line for line in lines
            )

    if first:
        rv = indention + rv

    return rv


@environmentfilter
def do_truncate(env, s, length=255, killwords=False, end="...", leeway=None):
    "a"
    if leeway is None:
        leeway = env.policies["truncate.leeway"]
    assert length >= len(end), "expected length >= %s, got %s" % (len(end), length)
    assert leeway >= 0, "expected leeway >= 0, got %s" % leeway
    if len(s) <= length + leeway:
        return s
    if killwords:
        return s[: length - len(end)] + end
    result = s[: length - len(end)].rsplit(" ", 1)[0]
    return result + end


@environmentfilter
def do_wordwrap(
    environment,
    s,
    width=79,
    break_long_words=True,
    wrapstring=None,
    break_on_hyphens=True,
):
    "a"

    import textwrap

    if not wrapstring:
        wrapstring = environment.newline_sequence

    return wrapstring.join(
        [
            wrapstring.join(
                textwrap.wrap(
                    line,
                    width=width,
                    expand_tabs=False,
                    replace_whitespace=False,
                    break_long_words=break_long_words,
                    break_on_hyphens=break_on_hyphens,
                )
            )
            for line in s.splitlines()
        ]
    )


def do_wordcount(s):
    "a"
    return len(_word_re.findall(soft_unicode(s)))


def do_int(value, default=0, base=10):
    "a"
    try:
        if isinstance(value, string_types):
            return int(value, base)
        return int(value)
    except (TypeError, ValueError):

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def do_float(value, default=0.0):
    "a"
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def do_format(value, *args, **kwargs):
    "a"
    if args and kwargs:
        raise FilterArgumentError(
            "can't handle positional and keyword arguments at the same time"
        )
    return soft_unicode(value) % (kwargs or args)


def do_trim(value, chars=None):
    "a"
    return soft_unicode(value).strip(chars)


def do_striptags(value):
    "a"
    if hasattr(value, "__html__"):
        value = value.__html__()
    return Markup(text_type(value)).striptags()


def do_slice(value, slices, fill_with=None):
    "a"
    seq = list(value)
    length = len(seq)
    items_per_slice = length // slices
    slices_with_extra = length % slices
    offset = 0
    for slice_number in range(slices):
        start = offset + slice_number * items_per_slice
        if slice_number < slices_with_extra:
            offset += 1
        end = offset + (slice_number + 1) * items_per_slice
        tmp = seq[start:end]
        if fill_with is not None and slice_number >= slices_with_extra:
            tmp.append(fill_with)
        yield tmp


def do_batch(value, linecount, fill_with=None):
    "a"
    tmp = []
    for item in value:
        if len(tmp) == linecount:
            yield tmp
            tmp = []
        tmp.append(item)
    if tmp:
        if fill_with is not None and len(tmp) < linecount:
            tmp += [fill_with] * (linecount - len(tmp))
        yield tmp


def do_round(value, precision=0, method="common"):
    "a"
    if method not in {"common", "ceil", "floor"}:
        raise FilterArgumentError("method must be common, ceil or floor")
    if method == "common":
        return round(value, precision)
    func = getattr(math, method)
    return func(value * (10 ** precision)) / (10 ** precision)

_GroupTuple = namedtuple("_GroupTuple", ["grouper", "list"])
_GroupTuple.__repr__ = tuple.__repr__
_GroupTuple.__str__ = tuple.__str__


@environmentfilter
def do_groupby(environment, value, attribute):
    "a"
    expr = make_attrgetter(environment, attribute)
    return [
        _GroupTuple(key, list(values))
        for key, values in groupby(sorted(value, key=expr), expr)
    ]


@environmentfilter
def do_sum(environment, iterable, attribute=None, start=0):
    "a"
    if attribute is not None:
        iterable = imap(make_attrgetter(environment, attribute), iterable)
    return sum(iterable, start)


def do_list(value):
    "a"
    return list(value)


def do_mark_safe(value):
    "a"
    return Markup(value)


def do_mark_unsafe(value):
    "a"
    return text_type(value)


def do_reverse(value):
    "a"
    if isinstance(value, string_types):
        return value[::-1]
    try:
        return reversed(value)
    except TypeError:
        try:
            rv = list(value)
            rv.reverse()
            return rv
        except TypeError:
            raise FilterArgumentError("argument must be iterable")


@environmentfilter
def do_attr(environment, obj, name):
    "a"
    try:
        name = str(name)
    except UnicodeError:
        pass
    else:
        try:
            value = getattr(obj, name)
        except AttributeError:
            pass
        else:
            if environment.sandboxed and not environment.is_safe_attribute(
                obj, name, value
            ):
                return environment.unsafe_undefined(obj, name)
            return value
    return environment.undefined(obj=obj, name=name)


@contextfilter
def do_map(*args, **kwargs):
    "a"
    seq, func = prepare_map(args, kwargs)
    if seq:
        for item in seq:
            yield func(item)


@contextfilter
def do_select(*args, **kwargs):
    "a"
    return select_or_reject(args, kwargs, lambda x: x, False)


@contextfilter
def do_reject(*args, **kwargs):
    "a"
    return select_or_reject(args, kwargs, lambda x: not x, False)


@contextfilter
def do_selectattr(*args, **kwargs):
    "a"
    return select_or_reject(args, kwargs, lambda x: x, True)


@contextfilter
def do_rejectattr(*args, **kwargs):
    "a"
    return select_or_reject(args, kwargs, lambda x: not x, True)


@evalcontextfilter
def do_tojson(eval_ctx, value, indent=None):
    "a"
    policies = eval_ctx.environment.policies
    dumper = policies["json.dumps_function"]
    options = policies["json.dumps_kwargs"]
    if indent is not None:
        options = dict(options)
        options["indent"] = indent
    return htmlsafe_json_dumps(value, dumper=dumper, **options)


def prepare_map(args, kwargs):
    context = args[0]
    seq = args[1]
    default = None

    if len(args) == 2 and "attribute" in kwargs:
        attribute = kwargs.pop("attribute")
        default = kwargs.pop("default", None)
        if kwargs:
            raise FilterArgumentError(
                "Unexpected keyword argument %r" % next(iter(kwargs))
            )
        func = make_attrgetter(context.environment, attribute, default=default)
    else:
        try:
            name = args[2]
            args = args[3:]
        except LookupError:
            raise FilterArgumentError("map requires a filter argument")

        def func(item):
            return context.environment.call_filter(
                name, item, args, kwargs, context=context
            )

    return seq, func


def prepare_select_or_reject(args, kwargs, modfunc, lookup_attr):
    context = args[0]
    seq = args[1]
    if lookup_attr:
        try:
            attr = args[2]
        except LookupError:
            raise FilterArgumentError("Missing parameter for attribute name")
        transfunc = make_attrgetter(context.environment, attr)
        off = 1
    else:
        off = 0

        def transfunc(x):
            return x

    try:
        name = args[2 + off]
        args = args[3 + off :]

        def func(item):
            return context.environment.call_test(name, item, args, kwargs)

    except LookupError:
        func = bool

    return seq, lambda item: modfunc(func(transfunc(item)))


def select_or_reject(args, kwargs, modfunc, lookup_attr):
    seq, func = prepare_select_or_reject(args, kwargs, modfunc, lookup_attr)
    if seq:
        for item in seq:
            if func(item):
                yield item


FILTERS = {
    "abs": abs,
    "attr": do_attr,
    "batch": do_batch,
    "capitalize": do_capitalize,
    "center": do_center,
    "count": len,
    "d": do_default,
    "default": do_default,
    "dictsort": do_dictsort,
    "e": escape,
    "escape": escape,
    "filesizeformat": do_filesizeformat,
    "first": do_first,
    "float": do_float,
    "forceescape": do_forceescape,
    "format": do_format,
    "groupby": do_groupby,
    "indent": do_indent,
    "int": do_int,
    "join": do_join,
    "last": do_last,
    "length": len,
    "list": do_list,
    "lower": do_lower,
    "map": do_map,
    "min": do_min,
    "max": do_max,
    "pprint": do_pprint,
    "random": do_random,
    "reject": do_reject,
    "rejectattr": do_rejectattr,
    "replace": do_replace,
    "reverse": do_reverse,
    "round": do_round,
    "safe": do_mark_safe,
    "select": do_select,
    "selectattr": do_selectattr,
    "slice": do_slice,
    "sort": do_sort,
    "string": soft_unicode,
    "striptags": do_striptags,
    "sum": do_sum,
    "title": do_title,
    "trim": do_trim,
    "truncate": do_truncate,
    "unique": do_unique,
    "upper": do_upper,
    "urlencode": do_urlencode,
    "urlize": do_urlize,
    "wordcount": do_wordcount,
    "wordwrap": do_wordwrap,
    "xmlattr": do_xmlattr,
    "tojson": do_tojson,
}
