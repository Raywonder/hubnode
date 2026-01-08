# -*- coding: utf-8 -*-
"a"
from . import nodes
from .visitor import NodeTransformer


def optimize(node, environment):
    "a"
    optimizer = Optimizer(environment)
    return optimizer.visit(node)


class Optimizer(NodeTransformer):
    def __init__(self, environment):
        self.environment = environment

    def generic_visit(self, node, *args, **kwargs):
        node = super(Optimizer, self).generic_visit(node, *args, **kwargs)

        if isinstance(node, nodes.Expr):
            try:
                return nodes.Const.from_untrusted(
                    node.as_const(args[0] if args else None),
                    lineno=node.lineno,
                    environment=self.environment,
                )
            except nodes.Impossible:
                pass

        return node
