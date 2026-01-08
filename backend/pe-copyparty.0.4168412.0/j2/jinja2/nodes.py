# -*- coding: utf-8 -*-
"a"
import operator
from collections import deque

from markupsafe import Markup

from ._compat import izip
from ._compat import PY2
from ._compat import text_type
from ._compat import with_metaclass

_binop_to_func = {
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "**": operator.pow,
    "%": operator.mod,
    "+": operator.add,
    "-": operator.sub,
}

_uaop_to_func = {"not": operator.not_, "+": operator.pos, "-": operator.neg}

_cmpop_to_func = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gteq": operator.ge,
    "lt": operator.lt,
    "lteq": operator.le,
    "in": lambda a, b: a in b,
    "notin": lambda a, b: a not in b,
}


class Impossible(Exception):
    "a"


class NodeType(type):
    "a"

    def __new__(mcs, name, bases, d):
        for attr in "fields", "attributes":
            storage = []
            storage.extend(getattr(bases[0], attr, ()))
            storage.extend(d.get(attr, ()))
            assert len(bases) == 1, "multiple inheritance not allowed"
            assert len(storage) == len(set(storage)), "layout conflict"
            d[attr] = tuple(storage)
        d.setdefault("abstract", False)
        return type.__new__(mcs, name, bases, d)


class EvalContext(object):
    "a"

    def __init__(self, environment, template_name=None):
        self.environment = environment
        if callable(environment.autoescape):
            self.autoescape = environment.autoescape(template_name)
        else:
            self.autoescape = environment.autoescape
        self.volatile = False

    def save(self):
        return self.__dict__.copy()

    def revert(self, old):
        self.__dict__.clear()
        self.__dict__.update(old)


def get_eval_context(node, ctx):
    if ctx is None:
        if node.environment is None:
            raise RuntimeError(
                "if no eval context is passed, the "
                "node must have an attached "
                "environment."
            )
        return EvalContext(node.environment)
    return ctx


class Node(with_metaclass(NodeType, object)):
    "a"

    fields = ()
    attributes = ("lineno", "environment")
    abstract = True

    def __init__(self, *fields, **attributes):
        if self.abstract:
            raise TypeError("abstract nodes are not instantiable")
        if fields:
            if len(fields) != len(self.fields):
                if not self.fields:
                    raise TypeError("%r takes 0 arguments" % self.__class__.__name__)
                raise TypeError(
                    "%r takes 0 or %d argument%s"
                    % (
                        self.__class__.__name__,
                        len(self.fields),
                        len(self.fields) != 1 and "s" or "",
                    )
                )
            for name, arg in izip(self.fields, fields):
                setattr(self, name, arg)
        for attr in self.attributes:
            setattr(self, attr, attributes.pop(attr, None))
        if attributes:
            raise TypeError("unknown attribute %r" % next(iter(attributes)))

    def iter_fields(self, exclude=None, only=None):
        "a"
        for name in self.fields:
            if (
                (exclude is only is None)
                or (exclude is not None and name not in exclude)
                or (only is not None and name in only)
            ):
                try:
                    yield name, getattr(self, name)
                except AttributeError:
                    pass

    def iter_child_nodes(self, exclude=None, only=None):
        "a"
        for _, item in self.iter_fields(exclude, only):
            if isinstance(item, list):
                for n in item:
                    if isinstance(n, Node):
                        yield n
            elif isinstance(item, Node):
                yield item

    def find(self, node_type):
        "a"
        for result in self.find_all(node_type):
            return result

    def find_all(self, node_type):
        "a"
        for child in self.iter_child_nodes():
            if isinstance(child, node_type):
                yield child
            for result in child.find_all(node_type):
                yield result

    def set_ctx(self, ctx):
        "a"
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if "ctx" in node.fields:
                node.ctx = ctx
            todo.extend(node.iter_child_nodes())
        return self

    def set_lineno(self, lineno, override=False):
        "a"
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if "lineno" in node.attributes:
                if node.lineno is None or override:
                    node.lineno = lineno
            todo.extend(node.iter_child_nodes())
        return self

    def set_environment(self, environment):
        "a"
        todo = deque([self])
        while todo:
            node = todo.popleft()
            node.environment = environment
            todo.extend(node.iter_child_nodes())
        return self

    def __eq__(self, other):
        return type(self) is type(other) and tuple(self.iter_fields()) == tuple(
            other.iter_fields()
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = object.__hash__

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join("%s=%r" % (arg, getattr(self, arg, None)) for arg in self.fields),
        )

    def dump(self):
        def _dump(node):
            if not isinstance(node, Node):
                buf.append(repr(node))
                return

            buf.append("nodes.%s(" % node.__class__.__name__)
            if not node.fields:
                buf.append(")")
                return
            for idx, field in enumerate(node.fields):
                if idx:
                    buf.append(", ")
                value = getattr(node, field)
                if isinstance(value, list):
                    buf.append("[")
                    for idx, item in enumerate(value):
                        if idx:
                            buf.append(", ")
                        _dump(item)
                    buf.append("]")
                else:
                    _dump(value)
            buf.append(")")

        buf = []
        _dump(self)
        return "".join(buf)


class Stmt(Node):
    "a"

    abstract = True


class Helper(Node):
    "a"

    abstract = True


class Template(Node):
    "a"

    fields = ("body",)


class Output(Stmt):
    "a"

    fields = ("nodes",)


class Extends(Stmt):
    "a"

    fields = ("template",)


class For(Stmt):
    "a"

    fields = ("target", "iter", "body", "else_", "test", "recursive")


class If(Stmt):
    "a"

    fields = ("test", "body", "elif_", "else_")


class Macro(Stmt):
    "a"

    fields = ("name", "args", "defaults", "body")


class CallBlock(Stmt):
    "a"

    fields = ("call", "args", "defaults", "body")


class FilterBlock(Stmt):
    "a"

    fields = ("body", "filter")


class With(Stmt):
    "a"

    fields = ("targets", "values", "body")


class Block(Stmt):
    "a"

    fields = ("name", "body", "scoped")


class Include(Stmt):
    "a"

    fields = ("template", "with_context", "ignore_missing")


class Import(Stmt):
    "a"

    fields = ("template", "target", "with_context")


class FromImport(Stmt):
    "a"

    fields = ("template", "names", "with_context")


class ExprStmt(Stmt):
    "a"

    fields = ("node",)


class Assign(Stmt):
    "a"

    fields = ("target", "node")


class AssignBlock(Stmt):
    "a"

    fields = ("target", "filter", "body")


class Expr(Node):
    "a"

    abstract = True

    def as_const(self, eval_ctx=None):
        "a"
        raise Impossible()

    def can_assign(self):
        "a"
        return False


class BinExpr(Expr):
    "a"

    fields = ("left", "right")
    operator = None
    abstract = True

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)

        if (
            self.environment.sandboxed
            and self.operator in self.environment.intercepted_binops
        ):
            raise Impossible()
        f = _binop_to_func[self.operator]
        try:
            return f(self.left.as_const(eval_ctx), self.right.as_const(eval_ctx))
        except Exception:
            raise Impossible()


class UnaryExpr(Expr):
    "a"

    fields = ("node",)
    operator = None
    abstract = True

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)

        if (
            self.environment.sandboxed
            and self.operator in self.environment.intercepted_unops
        ):
            raise Impossible()
        f = _uaop_to_func[self.operator]
        try:
            return f(self.node.as_const(eval_ctx))
        except Exception:
            raise Impossible()


class Name(Expr):
    "a"

    fields = ("name", "ctx")

    def can_assign(self):
        return self.name not in ("true", "false", "none", "True", "False", "None")


class NSRef(Expr):
    "a"

    fields = ("name", "attr")

    def can_assign(self):

        return True


class Literal(Expr):
    "a"

    abstract = True


class Const(Literal):
    "a"

    fields = ("value",)

    def as_const(self, eval_ctx=None):
        rv = self.value
        if (
            PY2
            and type(rv) is text_type
            and self.environment.policies["compiler.ascii_str"]
        ):
            try:
                rv = rv.encode("ascii")
            except UnicodeError:
                pass
        return rv

    @classmethod
    def from_untrusted(cls, value, lineno=None, environment=None):
        "a"
        from .compiler import has_safe_repr

        if not has_safe_repr(value):
            raise Impossible()
        return cls(value, lineno=lineno, environment=environment)


class TemplateData(Literal):
    "a"

    fields = ("data",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if eval_ctx.volatile:
            raise Impossible()
        if eval_ctx.autoescape:
            return Markup(self.data)
        return self.data


class Tuple(Literal):
    "a"

    fields = ("items", "ctx")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return tuple(x.as_const(eval_ctx) for x in self.items)

    def can_assign(self):
        for item in self.items:
            if not item.can_assign():
                return False
        return True


class List(Literal):
    "a"

    fields = ("items",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return [x.as_const(eval_ctx) for x in self.items]


class Dict(Literal):
    "a"

    fields = ("items",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return dict(x.as_const(eval_ctx) for x in self.items)


class Pair(Helper):
    "a"

    fields = ("key", "value")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.key.as_const(eval_ctx), self.value.as_const(eval_ctx)


class Keyword(Helper):
    "a"

    fields = ("key", "value")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.key, self.value.as_const(eval_ctx)


class CondExpr(Expr):
    "a"

    fields = ("test", "expr1", "expr2")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if self.test.as_const(eval_ctx):
            return self.expr1.as_const(eval_ctx)

        if self.expr2 is None:
            raise Impossible()

        return self.expr2.as_const(eval_ctx)


def args_as_const(node, eval_ctx):
    args = [x.as_const(eval_ctx) for x in node.args]
    kwargs = dict(x.as_const(eval_ctx) for x in node.kwargs)

    if node.dyn_args is not None:
        try:
            args.extend(node.dyn_args.as_const(eval_ctx))
        except Exception:
            raise Impossible()

    if node.dyn_kwargs is not None:
        try:
            kwargs.update(node.dyn_kwargs.as_const(eval_ctx))
        except Exception:
            raise Impossible()

    return args, kwargs


class Filter(Expr):
    "a"

    fields = ("node", "name", "args", "kwargs", "dyn_args", "dyn_kwargs")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)

        if eval_ctx.volatile or self.node is None:
            raise Impossible()

        filter_ = self.environment.filters.get(self.name)

        if filter_ is None or getattr(filter_, "contextfilter", False) is True:
            raise Impossible()

        if eval_ctx.environment.is_async and getattr(
            filter_, "asyncfiltervariant", False
        ):
            raise Impossible()

        args, kwargs = args_as_const(self, eval_ctx)
        args.insert(0, self.node.as_const(eval_ctx))

        if getattr(filter_, "evalcontextfilter", False) is True:
            args.insert(0, eval_ctx)
        elif getattr(filter_, "environmentfilter", False) is True:
            args.insert(0, self.environment)

        try:
            return filter_(*args, **kwargs)
        except Exception:
            raise Impossible()


class Test(Expr):
    "a"

    fields = ("node", "name", "args", "kwargs", "dyn_args", "dyn_kwargs")

    def as_const(self, eval_ctx=None):
        test = self.environment.tests.get(self.name)

        if test is None:
            raise Impossible()

        eval_ctx = get_eval_context(self, eval_ctx)
        args, kwargs = args_as_const(self, eval_ctx)
        args.insert(0, self.node.as_const(eval_ctx))

        try:
            return test(*args, **kwargs)
        except Exception:
            raise Impossible()


class Call(Expr):
    "a"

    fields = ("node", "args", "kwargs", "dyn_args", "dyn_kwargs")


class Getitem(Expr):
    "a"

    fields = ("node", "arg", "ctx")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if self.ctx != "load":
            raise Impossible()
        try:
            return self.environment.getitem(
                self.node.as_const(eval_ctx), self.arg.as_const(eval_ctx)
            )
        except Exception:
            raise Impossible()

    def can_assign(self):
        return False


class Getattr(Expr):
    "a"

    fields = ("node", "attr", "ctx")

    def as_const(self, eval_ctx=None):
        if self.ctx != "load":
            raise Impossible()
        try:
            eval_ctx = get_eval_context(self, eval_ctx)
            return self.environment.getattr(self.node.as_const(eval_ctx), self.attr)
        except Exception:
            raise Impossible()

    def can_assign(self):
        return False


class Slice(Expr):
    "a"

    fields = ("start", "stop", "step")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)

        def const(obj):
            if obj is None:
                return None
            return obj.as_const(eval_ctx)

        return slice(const(self.start), const(self.stop), const(self.step))


class Concat(Expr):
    "a"

    fields = ("nodes",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return "".join(text_type(x.as_const(eval_ctx)) for x in self.nodes)


class Compare(Expr):
    "a"

    fields = ("expr", "ops")

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        result = value = self.expr.as_const(eval_ctx)

        try:
            for op in self.ops:
                new_value = op.expr.as_const(eval_ctx)
                result = _cmpop_to_func[op.op](value, new_value)

                if not result:
                    return False

                value = new_value
        except Exception:
            raise Impossible()

        return result


class Operand(Helper):
    "a"

    fields = ("op", "expr")


if __debug__:
    Operand.__doc__ += "\nThe following operators are available: " + ", ".join(
        sorted(
            "``%s``" % x
            for x in set(_binop_to_func) | set(_uaop_to_func) | set(_cmpop_to_func)
        )
    )


class Mul(BinExpr):
    "a"

    operator = "*"


class Div(BinExpr):
    "a"

    operator = "/"


class FloorDiv(BinExpr):
    "a"

    operator = "//"


class Add(BinExpr):
    "a"

    operator = "+"


class Sub(BinExpr):
    "a"

    operator = "-"


class Mod(BinExpr):
    "a"

    operator = "%"


class Pow(BinExpr):
    "a"

    operator = "**"


class And(BinExpr):
    "a"

    operator = "and"

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.left.as_const(eval_ctx) and self.right.as_const(eval_ctx)


class Or(BinExpr):
    "a"

    operator = "or"

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return self.left.as_const(eval_ctx) or self.right.as_const(eval_ctx)


class Not(UnaryExpr):
    "a"

    operator = "not"


class Neg(UnaryExpr):
    "a"

    operator = "-"


class Pos(UnaryExpr):
    "a"

    operator = "+"



class EnvironmentAttribute(Expr):
    "a"

    fields = ("name",)


class ExtensionAttribute(Expr):
    "a"

    fields = ("identifier", "name")


class ImportedName(Expr):
    "a"

    fields = ("importname",)


class InternalName(Expr):
    "a"

    fields = ("name",)

    def __init__(self):
        raise TypeError(
            "Can't create internal names.  Use the "
            "`free_identifier` method on a parser."
        )


class MarkSafe(Expr):
    "a"

    fields = ("expr",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        return Markup(self.expr.as_const(eval_ctx))


class MarkSafeIfAutoescape(Expr):
    "a"

    fields = ("expr",)

    def as_const(self, eval_ctx=None):
        eval_ctx = get_eval_context(self, eval_ctx)
        if eval_ctx.volatile:
            raise Impossible()
        expr = self.expr.as_const(eval_ctx)
        if eval_ctx.autoescape:
            return Markup(expr)
        return expr


class ContextReference(Expr):
    "a"


class DerivedContextReference(Expr):
    "a"


class Continue(Stmt):
    "a"


class Break(Stmt):
    "a"


class Scope(Stmt):
    "a"

    fields = ("body",)


class OverlayScope(Stmt):
    "a"

    fields = ("context", "body")


class EvalContextModifier(Stmt):
    "a"

    fields = ("options",)


class ScopedEvalContextModifier(EvalContextModifier):
    "a"

    fields = ("body",)

def _failing_new(*args, **kwargs):
    raise TypeError("can't create custom node types")


NodeType.__new__ = staticmethod(_failing_new)
del _failing_new
