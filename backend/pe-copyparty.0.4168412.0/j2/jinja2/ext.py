# -*- coding: utf-8 -*-
"a"
import pprint
import re
from sys import version_info

from markupsafe import Markup

from . import nodes
from ._compat import iteritems
from ._compat import string_types
from ._compat import with_metaclass
from .defaults import BLOCK_END_STRING
from .defaults import BLOCK_START_STRING
from .defaults import COMMENT_END_STRING
from .defaults import COMMENT_START_STRING
from .defaults import KEEP_TRAILING_NEWLINE
from .defaults import LINE_COMMENT_PREFIX
from .defaults import LINE_STATEMENT_PREFIX
from .defaults import LSTRIP_BLOCKS
from .defaults import NEWLINE_SEQUENCE
from .defaults import TRIM_BLOCKS
from .defaults import VARIABLE_END_STRING
from .defaults import VARIABLE_START_STRING
from .environment import Environment
from .exceptions import TemplateAssertionError
from .exceptions import TemplateSyntaxError
from .nodes import ContextReference
from .runtime import concat
from .utils import contextfunction
from .utils import import_string

GETTEXT_FUNCTIONS = ("_", "gettext", "ngettext")

_ws_re = re.compile(r"\s*\n\s*")


class ExtensionRegistry(type):
    "a"

    def __new__(mcs, name, bases, d):
        rv = type.__new__(mcs, name, bases, d)
        rv.identifier = rv.__module__ + "." + rv.__name__
        return rv


class Extension(with_metaclass(ExtensionRegistry, object)):
    "a"

    tags = set()

    priority = 100

    def __init__(self, environment):
        self.environment = environment

    def bind(self, environment):
        "a"
        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.environment = environment
        return rv

    def preprocess(self, source, name, filename=None):
        "a"
        return source

    def filter_stream(self, stream):
        "a"
        return stream

    def parse(self, parser):
        "a"
        raise NotImplementedError()

    def attr(self, name, lineno=None):
        "a"
        return nodes.ExtensionAttribute(self.identifier, name, lineno=lineno)

    def call_method(
        self, name, args=None, kwargs=None, dyn_args=None, dyn_kwargs=None, lineno=None
    ):
        "a"
        if args is None:
            args = []
        if kwargs is None:
            kwargs = []
        return nodes.Call(
            self.attr(name, lineno=lineno),
            args,
            kwargs,
            dyn_args,
            dyn_kwargs,
            lineno=lineno,
        )


@contextfunction
def _gettext_alias(__context, *args, **kwargs):
    return __context.call(__context.resolve("gettext"), *args, **kwargs)


class ExprStmtExtension(Extension):
    "a"

    tags = set(["do"])

    def parse(self, parser):
        node = nodes.ExprStmt(lineno=next(parser.stream).lineno)
        node.node = parser.parse_tuple()
        return node


class LoopControlExtension(Extension):
    "a"

    tags = set(["break", "continue"])

    def parse(self, parser):
        token = next(parser.stream)
        if token.value == "break":
            return nodes.Break(lineno=token.lineno)
        return nodes.Continue(lineno=token.lineno)


class WithExtension(Extension):
    pass


class AutoEscapeExtension(Extension):
    pass


class DebugExtension(Extension):
    "a"

    tags = {"debug"}

    def parse(self, parser):
        lineno = parser.stream.expect("name:debug").lineno
        context = ContextReference()
        result = self.call_method("_render", [context], lineno=lineno)
        return nodes.Output([result], lineno=lineno)

    def _render(self, context):
        result = {
            "context": context.get_all(),
            "filters": sorted(self.environment.filters.keys()),
            "tests": sorted(self.environment.tests.keys()),
        }

        if version_info[:2] >= (3, 4):
            return pprint.pformat(result, depth=3, compact=True)
        else:
            return pprint.pformat(result, depth=3)


def extract_from_ast(node, gettext_functions=GETTEXT_FUNCTIONS, babel_style=True):
    "a"
    for node in node.find_all(nodes.Call):
        if (
            not isinstance(node.node, nodes.Name)
            or node.node.name not in gettext_functions
        ):
            continue

        strings = []
        for arg in node.args:
            if isinstance(arg, nodes.Const) and isinstance(arg.value, string_types):
                strings.append(arg.value)
            else:
                strings.append(None)

        for _ in node.kwargs:
            strings.append(None)
        if node.dyn_args is not None:
            strings.append(None)
        if node.dyn_kwargs is not None:
            strings.append(None)

        if not babel_style:
            strings = tuple(x for x in strings if x is not None)
            if not strings:
                continue
        else:
            if len(strings) == 1:
                strings = strings[0]
            else:
                strings = tuple(strings)
        yield node.lineno, node.node.name, strings


class _CommentFinder(object):
    "a"

    def __init__(self, tokens, comment_tags):
        self.tokens = tokens
        self.comment_tags = comment_tags
        self.offset = 0
        self.last_lineno = 0

    def find_backwards(self, offset):
        try:
            for _, token_type, token_value in reversed(
                self.tokens[self.offset : offset]
            ):
                if token_type in ("comment", "linecomment"):
                    try:
                        prefix, comment = token_value.split(None, 1)
                    except ValueError:
                        continue
                    if prefix in self.comment_tags:
                        return [comment.rstrip()]
            return []
        finally:
            self.offset = offset

    def find_comments(self, lineno):
        if not self.comment_tags or self.last_lineno > lineno:
            return []
        for idx, (token_lineno, _, _) in enumerate(self.tokens[self.offset :]):
            if token_lineno > lineno:
                return self.find_backwards(self.offset + idx)
        return self.find_backwards(len(self.tokens))


do = ExprStmtExtension
loopcontrols = LoopControlExtension
with_ = WithExtension
autoescape = AutoEscapeExtension
debug = DebugExtension
