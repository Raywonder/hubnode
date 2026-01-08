# -*- coding: utf-8 -*-
"""
markupsafe._native
~~~~~~~~~~~~~~~~~~

Native Python implementation used when the C module is not compiled.

:copyright: 2010 Pallets
:license: BSD-3-Clause
"""
from . import Markup
from ._compat import text_type


def escape(s):
    "a"
    if hasattr(s, "__html__"):
        return Markup(s.__html__())
    return Markup(
        text_type(s)
        .replace("&", "&amp;")
        .replace(">", "&gt;")
        .replace("<", "&lt;")
        .replace("'", "&#39;")
        .replace('"', "&#34;")
    )


def escape_silent(s):
    "a"
    if s is None:
        return Markup()
    return escape(s)


def soft_unicode(s):
    "a"
    if not isinstance(s, text_type):
        s = text_type(s)
    return s
