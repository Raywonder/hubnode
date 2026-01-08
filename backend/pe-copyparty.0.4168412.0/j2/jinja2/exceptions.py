# -*- coding: utf-8 -*-
from ._compat import imap
from ._compat import implements_to_string
from ._compat import PY2
from ._compat import text_type


class TemplateError(Exception):
    "a"

    if PY2:

        def __init__(self, message=None):
            if message is not None:
                message = text_type(message).encode("utf-8")
            Exception.__init__(self, message)

        @property
        def message(self):
            if self.args:
                message = self.args[0]
                if message is not None:
                    return message.decode("utf-8", "replace")

        def __unicode__(self):
            return self.message or u""

    else:

        def __init__(self, message=None):
            Exception.__init__(self, message)

        @property
        def message(self):
            if self.args:
                message = self.args[0]
                if message is not None:
                    return message


@implements_to_string
class TemplateNotFound(IOError, LookupError, TemplateError):
    "a"

    message = None

    def __init__(self, name, message=None):
        IOError.__init__(self, name)

        if message is None:
            from .runtime import Undefined

            if isinstance(name, Undefined):
                name._fail_with_undefined_error()

            message = name

        self.message = message
        self.name = name
        self.templates = [name]

    def __str__(self):
        return self.message


class TemplatesNotFound(TemplateNotFound):
    "a"

    def __init__(self, names=(), message=None):
        if message is None:
            from .runtime import Undefined

            parts = []

            for name in names:
                if isinstance(name, Undefined):
                    parts.append(name._undefined_message)
                else:
                    parts.append(name)

            message = u"none of the templates given were found: " + u", ".join(
                imap(text_type, parts)
            )
        TemplateNotFound.__init__(self, names and names[-1] or None, message)
        self.templates = list(names)


@implements_to_string
class TemplateSyntaxError(TemplateError):
    "a"

    def __init__(self, message, lineno, name=None, filename=None):
        TemplateError.__init__(self, message)
        self.lineno = lineno
        self.name = name
        self.filename = filename
        self.source = None

        self.translated = False

    def __str__(self):

        if self.translated:
            return self.message

        location = "line %d" % self.lineno
        name = self.filename or self.name
        if name:
            location = 'File "%s", %s' % (name, location)
        lines = [self.message, "  " + location]

        if self.source is not None:
            try:
                line = self.source.splitlines()[self.lineno - 1]
            except IndexError:
                line = None
            if line:
                lines.append("    " + line.strip())

        return u"\n".join(lines)

    def __reduce__(self):

        return self.__class__, (self.message, self.lineno, self.name, self.filename)


class TemplateAssertionError(TemplateSyntaxError):
    "a"


class TemplateRuntimeError(TemplateError):
    "a"


class UndefinedError(TemplateRuntimeError):
    "a"


class SecurityError(TemplateRuntimeError):
    "a"


class FilterArgumentError(TemplateRuntimeError):
    "a"
