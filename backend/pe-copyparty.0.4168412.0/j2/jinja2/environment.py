# -*- coding: utf-8 -*-
"a"
import os
import sys
import weakref
from functools import partial
from functools import reduce

from markupsafe import Markup

from . import nodes
from ._compat import encode_filename
from ._compat import implements_iterator
from ._compat import implements_to_string
from ._compat import iteritems
from ._compat import PY2
from ._compat import PYPY
from ._compat import reraise
from ._compat import string_types
from ._compat import text_type
from .compiler import CodeGenerator
from .compiler import generate
from .defaults import BLOCK_END_STRING
from .defaults import BLOCK_START_STRING
from .defaults import COMMENT_END_STRING
from .defaults import COMMENT_START_STRING
from .defaults import DEFAULT_FILTERS
from .defaults import DEFAULT_NAMESPACE
from .defaults import DEFAULT_POLICIES
from .defaults import DEFAULT_TESTS
from .defaults import KEEP_TRAILING_NEWLINE
from .defaults import LINE_COMMENT_PREFIX
from .defaults import LINE_STATEMENT_PREFIX
from .defaults import LSTRIP_BLOCKS
from .defaults import NEWLINE_SEQUENCE
from .defaults import TRIM_BLOCKS
from .defaults import VARIABLE_END_STRING
from .defaults import VARIABLE_START_STRING
from .exceptions import TemplateNotFound
from .exceptions import TemplateRuntimeError
from .exceptions import TemplatesNotFound
from .exceptions import TemplateSyntaxError
from .exceptions import UndefinedError
from .lexer import get_lexer
from .lexer import TokenStream
from .nodes import EvalContext
from .parser import Parser
from .runtime import Context
from .runtime import new_context
from .runtime import Undefined
from .utils import concat
from .utils import consume
from .utils import have_async_gen
from .utils import import_string
from .utils import internalcode
from .utils import LRUCache
from .utils import missing

_spontaneous_environments = LRUCache(10)


def get_spontaneous_environment(cls, *args):
    "a"
    key = (cls, args)

    try:
        return _spontaneous_environments[key]
    except KeyError:
        _spontaneous_environments[key] = env = cls(*args)
        env.shared = True
        return env


def create_cache(size):
    "a"
    if size == 0:
        return None
    if size < 0:
        return {}
    return LRUCache(size)


def copy_cache(cache):
    "a"
    if cache is None:
        return None
    elif type(cache) is dict:
        return {}
    return LRUCache(cache.capacity)


def load_extensions(environment, extensions):
    "a"
    result = {}
    for extension in extensions:
        if isinstance(extension, string_types):
            extension = import_string(extension)
        result[extension.identifier] = extension(environment)
    return result


def fail_for_missing_callable(string, name):
    msg = string % name
    if isinstance(name, Undefined):
        try:
            name._fail_with_undefined_error()
        except Exception as e:
            msg = "%s (%s; did you forget to quote the callable name?)" % (msg, e)
    raise TemplateRuntimeError(msg)


def _environment_sanity_check(environment):
    "a"
    assert issubclass(
        environment.undefined, Undefined
    ), "undefined must be a subclass of undefined because filters depend on it."
    assert (
        environment.block_start_string
        != environment.variable_start_string
        != environment.comment_start_string
    ), "block, variable and comment start strings must be different"
    assert environment.newline_sequence in (
        "\r",
        "\r\n",
        "\n",
    ), "newline_sequence set to unknown line ending string."
    return environment


class Environment(object):
    "a"

    sandboxed = False

    overlayed = False

    linked_to = None

    shared = False

    code_generator_class = CodeGenerator

    context_class = Context

    def __init__(
        self,
        block_start_string=BLOCK_START_STRING,
        block_end_string=BLOCK_END_STRING,
        variable_start_string=VARIABLE_START_STRING,
        variable_end_string=VARIABLE_END_STRING,
        comment_start_string=COMMENT_START_STRING,
        comment_end_string=COMMENT_END_STRING,
        line_statement_prefix=LINE_STATEMENT_PREFIX,
        line_comment_prefix=LINE_COMMENT_PREFIX,
        trim_blocks=TRIM_BLOCKS,
        lstrip_blocks=LSTRIP_BLOCKS,
        newline_sequence=NEWLINE_SEQUENCE,
        keep_trailing_newline=KEEP_TRAILING_NEWLINE,
        extensions=(),
        optimized=True,
        undefined=Undefined,
        finalize=None,
        autoescape=False,
        loader=None,
        cache_size=400,
        auto_reload=True,
        bytecode_cache=None,
        enable_async=False,
    ):

        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string
        self.line_statement_prefix = line_statement_prefix
        self.line_comment_prefix = line_comment_prefix
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.newline_sequence = newline_sequence
        self.keep_trailing_newline = keep_trailing_newline

        self.undefined = undefined
        self.optimized = optimized
        self.finalize = finalize
        self.autoescape = autoescape

        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()

        self.loader = loader
        self.cache = create_cache(cache_size)
        self.bytecode_cache = bytecode_cache
        self.auto_reload = auto_reload

        self.policies = DEFAULT_POLICIES.copy()

        self.extensions = load_extensions(self, extensions)

        self.enable_async = enable_async
        self.is_async = self.enable_async and have_async_gen
        if self.is_async:

            from . import asyncsupport

        _environment_sanity_check(self)

    def add_extension(self, extension):
        "a"
        self.extensions.update(load_extensions(self, [extension]))

    def extend(self, **attributes):
        "a"
        for key, value in iteritems(attributes):
            if not hasattr(self, key):
                setattr(self, key, value)

    def overlay(
        self,
        block_start_string=missing,
        block_end_string=missing,
        variable_start_string=missing,
        variable_end_string=missing,
        comment_start_string=missing,
        comment_end_string=missing,
        line_statement_prefix=missing,
        line_comment_prefix=missing,
        trim_blocks=missing,
        lstrip_blocks=missing,
        extensions=missing,
        optimized=missing,
        undefined=missing,
        finalize=missing,
        autoescape=missing,
        loader=missing,
        cache_size=missing,
        auto_reload=missing,
        bytecode_cache=missing,
    ):
        "a"
        args = dict(locals())
        del args["self"], args["cache_size"], args["extensions"]

        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.overlayed = True
        rv.linked_to = self

        for key, value in iteritems(args):
            if value is not missing:
                setattr(rv, key, value)

        if cache_size is not missing:
            rv.cache = create_cache(cache_size)
        else:
            rv.cache = copy_cache(self.cache)

        rv.extensions = {}
        for key, value in iteritems(self.extensions):
            rv.extensions[key] = value.bind(rv)
        if extensions is not missing:
            rv.extensions.update(load_extensions(rv, extensions))

        return _environment_sanity_check(rv)

    lexer = property(get_lexer, doc="The lexer for this environment.")

    def iter_extensions(self):
        "a"
        return iter(sorted(self.extensions.values(), key=lambda x: x.priority))

    def getitem(self, obj, argument):
        "a"
        try:
            return obj[argument]
        except (AttributeError, TypeError, LookupError):
            if isinstance(argument, string_types):
                try:
                    attr = str(argument)
                except Exception:
                    pass
                else:
                    try:
                        return getattr(obj, attr)
                    except AttributeError:
                        pass
            return self.undefined(obj=obj, name=argument)

    def getattr(self, obj, attribute):
        "a"
        try:
            return getattr(obj, attribute)
        except AttributeError:
            pass
        try:
            return obj[attribute]
        except (TypeError, LookupError, AttributeError):
            return self.undefined(obj=obj, name=attribute)

    def call_filter(
        self, name, value, args=None, kwargs=None, context=None, eval_ctx=None
    ):
        "a"
        func = self.filters.get(name)
        if func is None:
            fail_for_missing_callable("no filter named %r", name)
        args = [value] + list(args or ())
        if getattr(func, "contextfilter", False) is True:
            if context is None:
                raise TemplateRuntimeError(
                    "Attempted to invoke context filter without context"
                )
            args.insert(0, context)
        elif getattr(func, "evalcontextfilter", False) is True:
            if eval_ctx is None:
                if context is not None:
                    eval_ctx = context.eval_ctx
                else:
                    eval_ctx = EvalContext(self)
            args.insert(0, eval_ctx)
        elif getattr(func, "environmentfilter", False) is True:
            args.insert(0, self)
        return func(*args, **(kwargs or {}))

    def call_test(self, name, value, args=None, kwargs=None):
        "a"
        func = self.tests.get(name)
        if func is None:
            fail_for_missing_callable("no test named %r", name)
        return func(value, *(args or ()), **(kwargs or {}))

    @internalcode
    def parse(self, source, name=None, filename=None):
        "a"
        try:
            return self._parse(source, name, filename)
        except TemplateSyntaxError:
            self.handle_exception(source=source)

    def _parse(self, source, name, filename):
        "a"
        return Parser(self, source, name, encode_filename(filename)).parse()

    def lex(self, source, name=None, filename=None):
        "a"
        source = text_type(source)
        try:
            return self.lexer.tokeniter(source, name, filename)
        except TemplateSyntaxError:
            self.handle_exception(source=source)

    def preprocess(self, source, name=None, filename=None):
        "a"
        return reduce(
            lambda s, e: e.preprocess(s, name, filename),
            self.iter_extensions(),
            text_type(source),
        )

    def _tokenize(self, source, name, filename=None, state=None):
        "a"
        source = self.preprocess(source, name, filename)
        stream = self.lexer.tokenize(source, name, filename, state)
        for ext in self.iter_extensions():
            stream = ext.filter_stream(stream)
            if not isinstance(stream, TokenStream):
                stream = TokenStream(stream, name, filename)
        return stream

    def _generate(self, source, name, filename, defer_init=False):
        "a"
        return generate(
            source,
            self,
            name,
            filename,
            defer_init=defer_init,
            optimized=self.optimized,
        )

    def _compile(self, source, filename):
        "a"
        return compile(source, filename, "exec")

    @internalcode
    def compile(self, source, name=None, filename=None, raw=False, defer_init=False):
        "a"
        source_hint = None
        try:
            if isinstance(source, string_types):
                source_hint = source
                source = self._parse(source, name, filename)
            source = self._generate(source, name, filename, defer_init=defer_init)
            if raw:
                return source
            if filename is None:
                filename = "<template>"
            else:
                filename = encode_filename(filename)
            return self._compile(source, filename)
        except TemplateSyntaxError:
            self.handle_exception(source=source_hint)

    def compile_expression(self, source, undefined_to_none=True):
        "a"
        parser = Parser(self, source, state="variable")
        try:
            expr = parser.parse_expression()
            if not parser.stream.eos:
                raise TemplateSyntaxError(
                    "chunk after expression", parser.stream.current.lineno, None, None
                )
            expr.set_environment(self)
        except TemplateSyntaxError:
            if sys.exc_info() is not None:
                self.handle_exception(source=source)

        body = [nodes.Assign(nodes.Name("result", "store"), expr, lineno=1)]
        template = self.from_string(nodes.Template(body, lineno=1))
        return TemplateExpression(template, undefined_to_none)

    def list_templates(self, extensions=None, filter_func=None):
        "a"
        names = self.loader.list_templates()

        if extensions is not None:
            if filter_func is not None:
                raise TypeError(
                    "either extensions or filter_func can be passed, but not both"
                )

            def filter_func(x):
                return "." in x and x.rsplit(".", 1)[1] in extensions

        if filter_func is not None:
            names = [name for name in names if filter_func(name)]

        return names

    def handle_exception(self, source=None):
        "a"
        from .debug import rewrite_traceback_stack

        reraise(*rewrite_traceback_stack(source=source))

    def join_path(self, template, parent):
        "a"
        return template

    @internalcode
    def _load_template(self, name, globals):
        if self.loader is None:
            raise TypeError("no loader for this environment specified")
        cache_key = (weakref.ref(self.loader), name)
        if self.cache is not None:
            template = self.cache.get(cache_key)
            if template is not None and (
                not self.auto_reload or template.is_up_to_date
            ):
                return template
        template = self.loader.load(self, name, globals)
        if self.cache is not None:
            self.cache[cache_key] = template
        return template

    @internalcode
    def get_template(self, name, parent=None, globals=None):
        "a"
        if isinstance(name, Template):
            return name
        if parent is not None:
            name = self.join_path(name, parent)
        return self._load_template(name, self.make_globals(globals))

    @internalcode
    def select_template(self, names, parent=None, globals=None):
        "a"
        if isinstance(names, Undefined):
            names._fail_with_undefined_error()

        if not names:
            raise TemplatesNotFound(
                message=u"Tried to select from an empty list " u"of templates."
            )
        globals = self.make_globals(globals)
        for name in names:
            if isinstance(name, Template):
                return name
            if parent is not None:
                name = self.join_path(name, parent)
            try:
                return self._load_template(name, globals)
            except (TemplateNotFound, UndefinedError):
                pass
        raise TemplatesNotFound(names)

    @internalcode
    def get_or_select_template(self, template_name_or_list, parent=None, globals=None):
        "a"
        if isinstance(template_name_or_list, (string_types, Undefined)):
            return self.get_template(template_name_or_list, parent, globals)
        elif isinstance(template_name_or_list, Template):
            return template_name_or_list
        return self.select_template(template_name_or_list, parent, globals)

    def from_string(self, source, globals=None, template_class=None):
        "a"
        globals = self.make_globals(globals)
        cls = template_class or self.template_class
        return cls.from_code(self, self.compile(source), globals, None)

    def make_globals(self, d):
        "a"
        if not d:
            return self.globals
        return dict(self.globals, **d)


class Template(object):
    "a"

    environment_class = Environment

    def __new__(
        cls,
        source,
        block_start_string=BLOCK_START_STRING,
        block_end_string=BLOCK_END_STRING,
        variable_start_string=VARIABLE_START_STRING,
        variable_end_string=VARIABLE_END_STRING,
        comment_start_string=COMMENT_START_STRING,
        comment_end_string=COMMENT_END_STRING,
        line_statement_prefix=LINE_STATEMENT_PREFIX,
        line_comment_prefix=LINE_COMMENT_PREFIX,
        trim_blocks=TRIM_BLOCKS,
        lstrip_blocks=LSTRIP_BLOCKS,
        newline_sequence=NEWLINE_SEQUENCE,
        keep_trailing_newline=KEEP_TRAILING_NEWLINE,
        extensions=(),
        optimized=True,
        undefined=Undefined,
        finalize=None,
        autoescape=False,
        enable_async=False,
    ):
        env = get_spontaneous_environment(
            cls.environment_class,
            block_start_string,
            block_end_string,
            variable_start_string,
            variable_end_string,
            comment_start_string,
            comment_end_string,
            line_statement_prefix,
            line_comment_prefix,
            trim_blocks,
            lstrip_blocks,
            newline_sequence,
            keep_trailing_newline,
            frozenset(extensions),
            optimized,
            undefined,
            finalize,
            autoescape,
            None,
            0,
            False,
            None,
            enable_async,
        )
        return env.from_string(source, template_class=cls)

    @classmethod
    def from_code(cls, environment, code, globals, uptodate=None):
        "a"
        namespace = {"environment": environment, "__file__": code.co_filename}
        exec(code, namespace)
        rv = cls._from_namespace(environment, namespace, globals)
        rv._uptodate = uptodate
        return rv

    @classmethod
    def from_module_dict(cls, environment, module_dict, globals):
        "a"
        return cls._from_namespace(environment, module_dict, globals)

    @classmethod
    def _from_namespace(cls, environment, namespace, globals):
        t = object.__new__(cls)
        t.environment = environment
        t.globals = globals
        t.name = namespace["name"]
        t.filename = namespace["__file__"]
        t.blocks = namespace["blocks"]

        t.root_render_func = namespace["root"]
        t._module = None

        t._debug_info = namespace["debug_info"]
        t._uptodate = None

        namespace["environment"] = environment
        namespace["__jinja_template__"] = t

        return t

    def render(self, *args, **kwargs):
        "a"
        vars = dict(*args, **kwargs)
        try:
            return concat(self.root_render_func(self.new_context(vars)))
        except Exception:
            self.environment.handle_exception()

    def render_async(self, *args, **kwargs):
        "a"

        raise NotImplementedError(
            "This feature is not available for this version of Python"
        )

    def stream(self, *args, **kwargs):
        "a"
        return TemplateStream(self.generate(*args, **kwargs))

    def generate(self, *args, **kwargs):
        "a"
        vars = dict(*args, **kwargs)
        try:
            for event in self.root_render_func(self.new_context(vars)):
                yield event
        except Exception:
            yield self.environment.handle_exception()

    def generate_async(self, *args, **kwargs):
        "a"

        raise NotImplementedError(
            "This feature is not available for this version of Python"
        )

    def new_context(self, vars=None, shared=False, locals=None):
        "a"
        return new_context(
            self.environment, self.name, self.blocks, vars, shared, self.globals, locals
        )

    def make_module(self, vars=None, shared=False, locals=None):
        "a"
        return TemplateModule(self, self.new_context(vars, shared, locals))

    def make_module_async(self, vars=None, shared=False, locals=None):
        "a"

        raise NotImplementedError(
            "This feature is not available for this version of Python"
        )

    @internalcode
    def _get_default_module(self):
        if self._module is not None:
            return self._module
        self._module = rv = self.make_module()
        return rv

    @property
    def module(self):
        "a"
        return self._get_default_module()

    def get_corresponding_lineno(self, lineno):
        "a"
        for template_line, code_line in reversed(self.debug_info):
            if code_line <= lineno:
                return template_line
        return 1

    @property
    def is_up_to_date(self):
        "a"
        if self._uptodate is None:
            return True
        return self._uptodate()

    @property
    def debug_info(self):
        "a"
        if self._debug_info:
            return [tuple(map(int, x.split("="))) for x in self._debug_info.split("&")]
        return []

    def __repr__(self):
        if self.name is None:
            name = "memory:%x" % id(self)
        else:
            name = repr(self.name)
        return "<%s %s>" % (self.__class__.__name__, name)


@implements_to_string
class TemplateModule(object):
    "a"

    def __init__(self, template, context, body_stream=None):
        if body_stream is None:
            if context.environment.is_async:
                raise RuntimeError(
                    "Async mode requires a body stream "
                    "to be passed to a template module.  Use "
                    "the async methods of the API you are "
                    "using."
                )
            body_stream = list(template.root_render_func(context))
        self._body_stream = body_stream
        self.__dict__.update(context.get_exported())
        self.__name__ = template.name

    def __html__(self):
        return Markup(concat(self._body_stream))

    def __str__(self):
        return concat(self._body_stream)

    def __repr__(self):
        if self.__name__ is None:
            name = "memory:%x" % id(self)
        else:
            name = repr(self.__name__)
        return "<%s %s>" % (self.__class__.__name__, name)


class TemplateExpression(object):
    "a"

    def __init__(self, template, undefined_to_none):
        self._template = template
        self._undefined_to_none = undefined_to_none

    def __call__(self, *args, **kwargs):
        context = self._template.new_context(dict(*args, **kwargs))
        consume(self._template.root_render_func(context))
        rv = context.vars["result"]
        if self._undefined_to_none and isinstance(rv, Undefined):
            rv = None
        return rv


@implements_iterator
class TemplateStream(object):
    "a"

    def __init__(self, gen):
        self._gen = gen
        self.disable_buffering()

    def dump(self, fp, encoding=None, errors="strict"):
        "a"
        close = False
        if isinstance(fp, string_types):
            if encoding is None:
                encoding = "utf-8"
            fp = open(fp, "wb")
            close = True
        try:
            if encoding is not None:
                iterable = (x.encode(encoding, errors) for x in self)
            else:
                iterable = self
            if hasattr(fp, "writelines"):
                fp.writelines(iterable)
            else:
                for item in iterable:
                    fp.write(item)
        finally:
            if close:
                fp.close()

    def disable_buffering(self):
        "a"
        self._next = partial(next, self._gen)
        self.buffered = False

    def _buffered_generator(self, size):
        buf = []
        c_size = 0
        push = buf.append

        while 1:
            try:
                while c_size < size:
                    c = next(self._gen)
                    push(c)
                    if c:
                        c_size += 1
            except StopIteration:
                if not c_size:
                    return
            yield concat(buf)
            del buf[:]
            c_size = 0

    def enable_buffering(self, size=5):
        "a"
        if size <= 1:
            raise ValueError("buffer size too small")

        self.buffered = True
        self._next = partial(next, self._buffered_generator(size))

    def __iter__(self):
        return self

    def __next__(self):
        return self._next()

Environment.template_class = Template
