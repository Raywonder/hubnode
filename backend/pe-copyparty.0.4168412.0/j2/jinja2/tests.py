# -*- coding: utf-8 -*-
"a"
import decimal
import operator
import re

from ._compat import abc
from ._compat import integer_types
from ._compat import string_types
from ._compat import text_type
from .runtime import Undefined

number_re = re.compile(r"^-?\d+(\.\d+)?$")
regex_type = type(number_re)
test_callable = callable


def test_odd(value):
    "a"
    return value % 2 == 1


def test_even(value):
    "a"
    return value % 2 == 0


def test_divisibleby(value, num):
    "a"
    return value % num == 0


def test_defined(value):
    "a"
    return not isinstance(value, Undefined)


def test_undefined(value):
    "a"
    return isinstance(value, Undefined)


def test_none(value):
    "a"
    return value is None


def test_boolean(value):
    "a"
    return value is True or value is False


def test_false(value):
    "a"
    return value is False


def test_true(value):
    "a"
    return value is True

def test_integer(value):
    "a"
    return isinstance(value, integer_types) and value is not True and value is not False

def test_float(value):
    "a"
    return isinstance(value, float)


def test_lower(value):
    "a"
    return text_type(value).islower()


def test_upper(value):
    "a"
    return text_type(value).isupper()


def test_string(value):
    "a"
    return isinstance(value, string_types)


def test_mapping(value):
    "a"
    return isinstance(value, abc.Mapping)


def test_number(value):
    "a"
    return isinstance(value, integer_types + (float, complex, decimal.Decimal))


def test_sequence(value):
    "a"
    try:
        len(value)
        value.__getitem__
    except Exception:
        return False
    return True


def test_sameas(value, other):
    "a"
    return value is other


def test_iterable(value):
    "a"
    try:
        iter(value)
    except TypeError:
        return False
    return True


def test_escaped(value):
    "a"
    return hasattr(value, "__html__")


def test_in(value, seq):
    "a"
    return value in seq


TESTS = {
    "odd": test_odd,
    "even": test_even,
    "divisibleby": test_divisibleby,
    "defined": test_defined,
    "undefined": test_undefined,
    "none": test_none,
    "boolean": test_boolean,
    "false": test_false,
    "true": test_true,
    "integer": test_integer,
    "float": test_float,
    "lower": test_lower,
    "upper": test_upper,
    "string": test_string,
    "mapping": test_mapping,
    "number": test_number,
    "sequence": test_sequence,
    "iterable": test_iterable,
    "callable": test_callable,
    "sameas": test_sameas,
    "escaped": test_escaped,
    "in": test_in,
    "==": operator.eq,
    "eq": operator.eq,
    "equalto": operator.eq,
    "!=": operator.ne,
    "ne": operator.ne,
    ">": operator.gt,
    "gt": operator.gt,
    "greaterthan": operator.gt,
    "ge": operator.ge,
    ">=": operator.ge,
    "<": operator.lt,
    "lt": operator.lt,
    "lessthan": operator.lt,
    "<=": operator.le,
    "le": operator.le,
}
