# -*- coding: utf-8 -*-
"a"
from markupsafe import escape
from markupsafe import Markup

from .environment import Environment
from .environment import Template
from .exceptions import TemplateAssertionError
from .exceptions import TemplateError
from .exceptions import TemplateNotFound
from .exceptions import TemplateRuntimeError
from .exceptions import TemplatesNotFound
from .exceptions import TemplateSyntaxError
from .exceptions import UndefinedError
from .filters import contextfilter
from .filters import environmentfilter
from .filters import evalcontextfilter
from .loaders import BaseLoader
from .loaders import FileSystemLoader
from .loaders import FunctionLoader
from .runtime import ChainableUndefined
from .runtime import DebugUndefined
from .runtime import make_logging_undefined
from .runtime import StrictUndefined
from .runtime import Undefined
from .utils import clear_caches
from .utils import contextfunction
from .utils import environmentfunction
from .utils import evalcontextfunction
from .utils import is_undefined
from .utils import select_autoescape

__version__ = "2.11.3"
