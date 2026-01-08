# -*- coding: utf-8 -*-
"a"
from . import nodes
from ._compat import iteritems
from ._compat import string_types
from .compiler import CodeGenerator


class TrackingCodeGenerator(CodeGenerator):
    "a"

    def __init__(self, environment):
        CodeGenerator.__init__(self, environment, "<introspection>", "<introspection>")
        self.undeclared_identifiers = set()

    def write(self, x):
        "a"

    def enter_frame(self, frame):
        "a"
        CodeGenerator.enter_frame(self, frame)
        for _, (action, param) in iteritems(frame.symbols.loads):
            if action == "resolve" and param not in self.environment.globals:
                self.undeclared_identifiers.add(param)


def find_undeclared_variables(ast):
    "a"
    codegen = TrackingCodeGenerator(ast.environment)
    codegen.visit(ast)
    return codegen.undeclared_identifiers


def find_referenced_templates(ast):
    "a"
    for node in ast.find_all(
        (nodes.Extends, nodes.FromImport, nodes.Import, nodes.Include)
    ):
        if not isinstance(node.template, nodes.Const):

            if isinstance(node.template, (nodes.Tuple, nodes.List)):
                for template_name in node.template.items:

                    if isinstance(template_name, nodes.Const):
                        if isinstance(template_name.value, string_types):
                            yield template_name.value

                    else:
                        yield None

            else:
                yield None
            continue

        if isinstance(node.template.value, string_types):
            yield node.template.value

        elif isinstance(node, nodes.Include) and isinstance(
            node.template.value, (tuple, list)
        ):
            for template_name in node.template.value:
                if isinstance(template_name, string_types):
                    yield template_name

        else:
            yield None
