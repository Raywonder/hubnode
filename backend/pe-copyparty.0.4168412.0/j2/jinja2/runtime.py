# -*- coding: utf-8 -*-
"a"
import sys
from itertools import chain
from types import MethodType

from markupsafe import escape
from markupsafe import Markup
from markupsafe import soft_unicode

from ._compat import abc
from ._compat import imap
from ._compat import implements_iterator
from ._compat import implements_to_string
from ._compat import iteritems
from ._compat import PY2
from ._compat import string_types
from ._compat import text_type
from ._compat import with_metaclass
from .exceptions import TemplateNotFound
from .exceptions import TemplateRuntimeError
from .exceptions import UndefinedError
from .nodes import EvalContext
from .utils import concat
from .utils import evalcontextfunction
from .utils import internalcode
from .utils import missing
from .utils import Namespace
from .utils import object_type_repr

exported = [
    "LoopContext",
    "TemplateReference",
    "Macro",
    "Markup",
    "TemplateRuntimeError",
    "missing",
    "concat",
    "escape",
    "markup_join",
    "unicode_join",
    "to_string",
    "identity",
    "TemplateNotFound",
    "Namespace",
    "Undefined",
]

to_string = text_type


def identity(x):
    "a"
    return x


def markup_join(seq):
    "a"
    buf = []
    iterator = imap(soft_unicode, seq)
    for arg in iterator:
        buf.append(arg)
        if hasattr(arg, "__html__"):
            return Markup(u"").join(chain(buf, iterator))
    return concat(buf)


def unicode_join(seq):
    "a"
    return concat(imap(text_type, seq))


def new_context(
    environment,
    template_name,
    blocks,
    vars=None,
    shared=None,
    globals=None,
    locals=None,
):
    "a"
    if vars is None:
        vars = {}
    if shared:
        parent = vars
    else:
        parent = dict(globals or (), **vars)
    if locals:

        if shared:
            parent = dict(parent)
        for key, value in iteritems(locals):
            if value is not missing:
                parent[key] = value
    return environment.context_class(environment, parent, template_name, blocks)


class TemplateReference(object):
    "a"

    def __init__(self, context):
        self.__context = context

    def __getitem__(self, name):
        blocks = self.__context.blocks[name]
        return BlockReference(name, self.__context, blocks, 0)

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.__context.name)


def _get_func(x):
    return getattr(x, "__func__", x)


class ContextMeta(type):
    def __new__(mcs, name, bases, d):
        rv = type.__new__(mcs, name, bases, d)
        if bases == ():
            return rv

        resolve = _get_func(rv.resolve)
        default_resolve = _get_func(Context.resolve)
        resolve_or_missing = _get_func(rv.resolve_or_missing)
        default_resolve_or_missing = _get_func(Context.resolve_or_missing)

        if (
            resolve is not default_resolve
            and resolve_or_missing is default_resolve_or_missing
        ):
            rv._legacy_resolve_mode = True
        elif (
            resolve is default_resolve
            and resolve_or_missing is default_resolve_or_missing
        ):
            rv._fast_resolve_mode = True

        return rv


def resolve_or_missing(context, key, missing=missing):
    if key in context.vars:
        return context.vars[key]
    if key in context.parent:
        return context.parent[key]
    return missing


class Context(with_metaclass(ContextMeta)):
    "a"

    _legacy_resolve_mode = False
    _fast_resolve_mode = False

    def __init__(self, environment, parent, name, blocks):
        self.parent = parent
        self.vars = {}
        self.environment = environment
        self.eval_ctx = EvalContext(self.environment, name)
        self.exported_vars = set()
        self.name = name

        self.blocks = dict((k, [v]) for k, v in iteritems(blocks))

        if self._fast_resolve_mode:
            self.resolve_or_missing = MethodType(resolve_or_missing, self)

    def super(self, name, current):
        "a"
        try:
            blocks = self.blocks[name]
            index = blocks.index(current) + 1
            blocks[index]
        except LookupError:
            return self.environment.undefined(
                "there is no parent block called %r." % name, name="super"
            )
        return BlockReference(name, self, blocks, index)

    def get(self, key, default=None):
        "a"
        try:
            return self[key]
        except KeyError:
            return default

    def resolve(self, key):
        "a"
        if self._legacy_resolve_mode:
            rv = resolve_or_missing(self, key)
        else:
            rv = self.resolve_or_missing(key)
        if rv is missing:
            return self.environment.undefined(name=key)
        return rv

    def resolve_or_missing(self, key):
        "a"
        if self._legacy_resolve_mode:
            rv = self.resolve(key)
            if isinstance(rv, Undefined):
                rv = missing
            return rv
        return resolve_or_missing(self, key)

    def get_exported(self):
        "a"
        return dict((k, self.vars[k]) for k in self.exported_vars)

    def get_all(self):
        "a"
        if not self.vars:
            return self.parent
        if not self.parent:
            return self.vars
        return dict(self.parent, **self.vars)

    @internalcode
    def call(__self, __obj, *args, **kwargs):
        "a"
        if __debug__:
            __traceback_hide__ = True

        if hasattr(__obj, "__call__"):
            fn = __obj.__call__
            for fn_type in (
                "contextfunction",
                "evalcontextfunction",
                "environmentfunction",
            ):
                if hasattr(fn, fn_type):
                    __obj = fn
                    break

        if callable(__obj):
            if getattr(__obj, "contextfunction", False) is True:
                args = (__self,) + args
            elif getattr(__obj, "evalcontextfunction", False) is True:
                args = (__self.eval_ctx,) + args
            elif getattr(__obj, "environmentfunction", False) is True:
                args = (__self.environment,) + args
        try:
            return __obj(*args, **kwargs)
        except StopIteration:
            return __self.environment.undefined(
                "value was undefined because "
                "a callable raised a "
                "StopIteration exception"
            )

    def derived(self, locals=None):
        "a"
        context = new_context(
            self.environment, self.name, {}, self.get_all(), True, None, locals
        )
        context.eval_ctx = self.eval_ctx
        context.blocks.update((k, list(v)) for k, v in iteritems(self.blocks))
        return context

    def _all(meth):
        def proxy(self):
            return getattr(self.get_all(), meth)()

        proxy.__doc__ = getattr(dict, meth).__doc__
        proxy.__name__ = meth
        return proxy

    keys = _all("keys")
    values = _all("values")
    items = _all("items")

    if PY2:
        iterkeys = _all("iterkeys")
        itervalues = _all("itervalues")
        iteritems = _all("iteritems")
    del _all

    def __contains__(self, name):
        return name in self.vars or name in self.parent

    def __getitem__(self, key):
        "a"
        item = self.resolve_or_missing(key)
        if item is missing:
            raise KeyError(key)
        return item

    def __repr__(self):
        return "<%s %s of %r>" % (
            self.__class__.__name__,
            repr(self.get_all()),
            self.name,
        )


abc.Mapping.register(Context)


class BlockReference(object):
    "a"

    def __init__(self, name, context, stack, depth):
        self.name = name
        self._context = context
        self._stack = stack
        self._depth = depth

    @property
    def super(self):
        "a"
        if self._depth + 1 >= len(self._stack):
            return self._context.environment.undefined(
                "there is no parent block called %r." % self.name, name="super"
            )
        return BlockReference(self.name, self._context, self._stack, self._depth + 1)

    @internalcode
    def __call__(self):
        rv = concat(self._stack[self._depth](self._context))
        if self._context.eval_ctx.autoescape:
            rv = Markup(rv)
        return rv


@implements_iterator
class LoopContext(object):
    "a"

    index0 = -1

    _length = None
    _after = missing
    _current = missing
    _before = missing
    _last_changed_value = missing

    def __init__(self, iterable, undefined, recurse=None, depth0=0):
        "a"
        self._iterable = iterable
        self._iterator = self._to_iterator(iterable)
        self._undefined = undefined
        self._recurse = recurse

        self.depth0 = depth0

    @staticmethod
    def _to_iterator(iterable):
        return iter(iterable)

    @property
    def length(self):
        "a"
        if self._length is not None:
            return self._length

        try:
            self._length = len(self._iterable)
        except TypeError:
            iterable = list(self._iterator)
            self._iterator = self._to_iterator(iterable)
            self._length = len(iterable) + self.index + (self._after is not missing)

        return self._length

    def __len__(self):
        return self.length

    @property
    def depth(self):
        "a"
        return self.depth0 + 1

    @property
    def index(self):
        "a"
        return self.index0 + 1

    @property
    def revindex0(self):
        "a"
        return self.length - self.index

    @property
    def revindex(self):
        "a"
        return self.length - self.index0

    @property
    def first(self):
        "a"
        return self.index0 == 0

    def _peek_next(self):
        "a"
        if self._after is not missing:
            return self._after

        self._after = next(self._iterator, missing)
        return self._after

    @property
    def last(self):
        "a"
        return self._peek_next() is missing

    @property
    def previtem(self):
        "a"
        if self.first:
            return self._undefined("there is no previous item")

        return self._before

    @property
    def nextitem(self):
        "a"
        rv = self._peek_next()

        if rv is missing:
            return self._undefined("there is no next item")

        return rv

    def cycle(self, *args):
        "a"
        if not args:
            raise TypeError("no items for cycling given")

        return args[self.index0 % len(args)]

    def changed(self, *value):
        "a"
        if self._last_changed_value != value:
            self._last_changed_value = value
            return True

        return False

    def __iter__(self):
        return self

    def __next__(self):
        if self._after is not missing:
            rv = self._after
            self._after = missing
        else:
            rv = next(self._iterator)

        self.index0 += 1
        self._before = self._current
        self._current = rv
        return rv, self

    @internalcode
    def __call__(self, iterable):
        "a"
        if self._recurse is None:
            raise TypeError(
                "The loop must have the 'recursive' marker to be called recursively."
            )

        return self._recurse(iterable, self._recurse, depth=self.depth)

    def __repr__(self):
        return "<%s %d/%d>" % (self.__class__.__name__, self.index, self.length)


class Macro(object):
    "a"

    def __init__(
        self,
        environment,
        func,
        name,
        arguments,
        catch_kwargs,
        catch_varargs,
        caller,
        default_autoescape=None,
    ):
        self._environment = environment
        self._func = func
        self._argument_count = len(arguments)
        self.name = name
        self.arguments = arguments
        self.catch_kwargs = catch_kwargs
        self.catch_varargs = catch_varargs
        self.caller = caller
        self.explicit_caller = "caller" in arguments
        if default_autoescape is None:
            default_autoescape = environment.autoescape
        self._default_autoescape = default_autoescape

    @internalcode
    @evalcontextfunction
    def __call__(self, *args, **kwargs):

        if args and isinstance(args[0], EvalContext):
            autoescape = args[0].autoescape
            args = args[1:]
        else:
            autoescape = self._default_autoescape

        arguments = list(args[: self._argument_count])
        off = len(arguments)

        found_caller = False

        if off != self._argument_count:
            for name in self.arguments[len(arguments) :]:
                try:
                    value = kwargs.pop(name)
                except KeyError:
                    value = missing
                if name == "caller":
                    found_caller = True
                arguments.append(value)
        else:
            found_caller = self.explicit_caller

        if self.caller and not found_caller:
            caller = kwargs.pop("caller", None)
            if caller is None:
                caller = self._environment.undefined("No caller defined", name="caller")
            arguments.append(caller)

        if self.catch_kwargs:
            arguments.append(kwargs)
        elif kwargs:
            if "caller" in kwargs:
                raise TypeError(
                    "macro %r was invoked with two values for "
                    "the special caller argument.  This is "
                    "most likely a bug." % self.name
                )
            raise TypeError(
                "macro %r takes no keyword argument %r"
                % (self.name, next(iter(kwargs)))
            )
        if self.catch_varargs:
            arguments.append(args[self._argument_count :])
        elif len(args) > self._argument_count:
            raise TypeError(
                "macro %r takes not more than %d argument(s)"
                % (self.name, len(self.arguments))
            )

        return self._invoke(arguments, autoescape)

    def _invoke(self, arguments, autoescape):
        "a"
        rv = self._func(*arguments)
        if autoescape:
            rv = Markup(rv)
        return rv

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.name is None and "anonymous" or repr(self.name),
        )


@implements_to_string
class Undefined(object):
    "a"

    __slots__ = (
        "_undefined_hint",
        "_undefined_obj",
        "_undefined_name",
        "_undefined_exception",
    )

    def __init__(self, hint=None, obj=missing, name=None, exc=UndefinedError):
        self._undefined_hint = hint
        self._undefined_obj = obj
        self._undefined_name = name
        self._undefined_exception = exc

    @property
    def _undefined_message(self):
        "a"
        if self._undefined_hint:
            return self._undefined_hint

        if self._undefined_obj is missing:
            return "%r is undefined" % self._undefined_name

        if not isinstance(self._undefined_name, string_types):
            return "%s has no element %r" % (
                object_type_repr(self._undefined_obj),
                self._undefined_name,
            )

        return "%r has no attribute %r" % (
            object_type_repr(self._undefined_obj),
            self._undefined_name,
        )

    @internalcode
    def _fail_with_undefined_error(self, *args, **kwargs):
        "a"
        raise self._undefined_exception(self._undefined_message)

    @internalcode
    def __getattr__(self, name):
        if name[:2] == "__":
            raise AttributeError(name)
        return self._fail_with_undefined_error()

    __add__ = (
        __radd__
    ) = (
        __mul__
    ) = (
        __rmul__
    ) = (
        __div__
    ) = (
        __rdiv__
    ) = (
        __truediv__
    ) = (
        __rtruediv__
    ) = (
        __floordiv__
    ) = (
        __rfloordiv__
    ) = (
        __mod__
    ) = (
        __rmod__
    ) = (
        __pos__
    ) = (
        __neg__
    ) = (
        __call__
    ) = (
        __getitem__
    ) = (
        __lt__
    ) = (
        __le__
    ) = (
        __gt__
    ) = (
        __ge__
    ) = (
        __int__
    ) = (
        __float__
    ) = (
        __complex__
    ) = __pow__ = __rpow__ = __sub__ = __rsub__ = _fail_with_undefined_error

    def __eq__(self, other):
        return type(self) is type(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(type(self))

    def __str__(self):
        return u""

    def __len__(self):
        return 0

    def __iter__(self):
        if 0:
            yield None

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__

    def __repr__(self):
        return "Undefined"


def make_logging_undefined(logger=None, base=None):
    "a"
    if logger is None:
        import logging

        logger = logging.getLogger(__name__)
        logger.addHandler(logging.StreamHandler(sys.stderr))
    if base is None:
        base = Undefined

    def _log_message(undef):
        if undef._undefined_hint is None:
            if undef._undefined_obj is missing:
                hint = "%s is undefined" % undef._undefined_name
            elif not isinstance(undef._undefined_name, string_types):
                hint = "%s has no element %s" % (
                    object_type_repr(undef._undefined_obj),
                    undef._undefined_name,
                )
            else:
                hint = "%s has no attribute %s" % (
                    object_type_repr(undef._undefined_obj),
                    undef._undefined_name,
                )
        else:
            hint = undef._undefined_hint
        logger.warning("Template variable warning: %s", hint)

    class LoggingUndefined(base):
        def _fail_with_undefined_error(self, *args, **kwargs):
            try:
                return base._fail_with_undefined_error(self, *args, **kwargs)
            except self._undefined_exception as e:
                logger.error("Template variable error: %s", str(e))
                raise e

        def __str__(self):
            rv = base.__str__(self)
            _log_message(self)
            return rv

        def __iter__(self):
            rv = base.__iter__(self)
            _log_message(self)
            return rv

        if PY2:

            def __nonzero__(self):
                rv = base.__nonzero__(self)
                _log_message(self)
                return rv

            def __unicode__(self):
                rv = base.__unicode__(self)
                _log_message(self)
                return rv

        else:

            def __bool__(self):
                rv = base.__bool__(self)
                _log_message(self)
                return rv

    return LoggingUndefined

class ChainableUndefined(Undefined):
    "a"

    __slots__ = ()

    def __html__(self):
        return self.__str__()

    def __getattr__(self, _):
        return self

    __getitem__ = __getattr__


@implements_to_string
class DebugUndefined(Undefined):
    "a"

    __slots__ = ()

    def __str__(self):
        if self._undefined_hint is None:
            if self._undefined_obj is missing:
                return u"{{ %s }}" % self._undefined_name
            return "{{ no such element: %s[%r] }}" % (
                object_type_repr(self._undefined_obj),
                self._undefined_name,
            )
        return u"{{ undefined value printed: %s }}" % self._undefined_hint


@implements_to_string
class StrictUndefined(Undefined):
    "a"

    __slots__ = ()
    __iter__ = (
        __str__
    ) = (
        __len__
    ) = (
        __nonzero__
    ) = __eq__ = __ne__ = __bool__ = __hash__ = Undefined._fail_with_undefined_error

del (
    Undefined.__slots__,
    ChainableUndefined.__slots__,
    DebugUndefined.__slots__,
    StrictUndefined.__slots__,
)
