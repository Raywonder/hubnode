# -*- coding: utf-8 -*-
"a"
import os
import sys
import weakref
from hashlib import sha1
from os import path
from types import ModuleType

from ._compat import abc
from ._compat import fspath
from ._compat import iteritems
from ._compat import string_types
from .exceptions import TemplateNotFound
from .utils import internalcode
from .utils import open_if_exists


def split_template_path(template):
    "a"
    pieces = []
    for piece in template.split("/"):
        if (
            path.sep in piece
            or (path.altsep and path.altsep in piece)
            or piece == path.pardir
        ):
            raise TemplateNotFound(template)
        elif piece and piece != ".":
            pieces.append(piece)
    return pieces


class BaseLoader(object):
    "a"

    has_source_access = True

    def get_source(self, environment, template):
        "a"
        if not self.has_source_access:
            raise RuntimeError(
                "%s cannot provide access to the source" % self.__class__.__name__
            )
        raise TemplateNotFound(template)

    def list_templates(self):
        "a"
        raise TypeError("this loader cannot iterate over all templates")

    @internalcode
    def load(self, environment, name, globals=None):
        "a"
        code = None
        if globals is None:
            globals = {}

        source, filename, uptodate = self.get_source(environment, name)

        bcc = environment.bytecode_cache
        if bcc is not None:
            bucket = bcc.get_bucket(environment, name, filename, source)
            code = bucket.code

        if code is None:
            code = environment.compile(source, name, filename)

        if bcc is not None and bucket.code is None:
            bucket.code = code
            bcc.set_bucket(bucket)

        return environment.template_class.from_code(
            environment, code, globals, uptodate
        )


class FileSystemLoader(BaseLoader):
    "a"

    def __init__(self, searchpath, encoding="utf-8", followlinks=False):
        if not isinstance(searchpath, abc.Iterable) or isinstance(
            searchpath, string_types
        ):
            searchpath = [searchpath]

        self.searchpath = [fspath(p) for p in searchpath]

        self.encoding = encoding
        self.followlinks = followlinks

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        for searchpath in self.searchpath:
            filename = path.join(searchpath, *pieces)
            f = open_if_exists(filename)
            if f is None:
                continue
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()

            mtime = path.getmtime(filename)

            def uptodate():
                try:
                    return path.getmtime(filename) == mtime
                except OSError:
                    return False

            return contents, filename, uptodate
        raise TemplateNotFound(template)

    def list_templates(self):
        found = set()
        for searchpath in self.searchpath:
            walk_dir = os.walk(searchpath, followlinks=self.followlinks)
            for dirpath, _, filenames in walk_dir:
                for filename in filenames:
                    template = (
                        os.path.join(dirpath, filename)[len(searchpath) :]
                        .strip(os.path.sep)
                        .replace(os.path.sep, "/")
                    )
                    if template[:2] == "./":
                        template = template[2:]
                    if template not in found:
                        found.add(template)
        return sorted(found)


class FunctionLoader(BaseLoader):
    "a"

    def __init__(self, load_func):
        self.load_func = load_func

    def get_source(self, environment, template):
        rv = self.load_func(template)
        if rv is None:
            raise TemplateNotFound(template)
        elif isinstance(rv, string_types):
            return rv, None, None
        return rv


class _TemplateModule(ModuleType):
    "a"


