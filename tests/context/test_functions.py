from __future__ import print_function

import pytest

import lena
import lena.core
from lena.core import LenaTypeError, LenaValueError
import lena.context.functions as lf
from lena.context import (
    difference, format_context, get_recursively,
    iterate_update, update_recursively, update_nested,
    intersection,
)


def test_contains():
    d = {'a': {'b': 'c d'}, 'e': 1}
    assert lena.context.contains(d, "a") is True
    assert lena.context.contains(d, "a.b.c d") is True
    assert lena.context.contains(d, "b.c") is False
    assert lena.context.contains(d, "a.b") is True
    # not string contents are cast to strings
    assert lena.context.contains(d, "e.1") is True


def test_difference():
    d0 = {}
    d1 = {'a': {'b': 'c d'}, 'e': 'f'}
    d2 = {'a': d1['a']}
    assert difference(d0, d1) == d0
    assert difference(d1, d0) == d1
    assert difference(d1, d2) == {'e': 'f'}


def test_format_context():
    """Note that formatting errors may be very tricky to understand.

    >>> "{}".format(x=1) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    IndexError: tuple index out of range
    >>> "{}{}".format(1) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    IndexError: tuple index out of range
    >>> "{y}_{x}".format(1, 2)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    KeyError: 'y'
    """
    # format_str must be a string
    with pytest.raises(LenaTypeError):
        format_context(0)
    ## old single braces are prohibited
    with pytest.raises(LenaValueError):
        format_context("{x}")
    # unbalanced braces are prohibited
    with pytest.raises(LenaValueError):
        format_context("{{x}}}}")

    # new double braces work
    f = format_context("{{x}}")
    assert f({"x": 10}) == "10"
    f = format_context("{{x.y}}")
    assert f({"x": {"y": 10}}) == "10"
    # # special string doesn't work with keyword arguments
    # f = format_context("{}_{x.y}", "x.y")
    # with pytest.raises(lena.core.LenaKeyError):
    #     f({"x": {"y": 10}})

    ## special formatting works
    f = format_context("{{x!r}}")
    assert f({"x": 10}) == "10"
    f = format_context("{{x:*^4}}")
    assert f({"x": 10}) == "*10*"

    # missing values raise LenaKeyError
    with pytest.raises(lena.core.LenaKeyError):
        f({})
    f = format_context("{{x} }")
    with pytest.raises(ValueError):
        f({"x": 10})

    # several braces work
    f = format_context("{{x}}_{{y}}")
    assert f({"x": 1, "y":1}) == "1_1"
    f = format_context("{{x}}{{y}}")
    assert f({"x": 1, "y":1}) == "11"

    # simple string works!
    f = format_context("a_string")
    assert f({"x": 1}) == "a_string"

    # ## positional arguments work
    # f = format_context("{}", "x")
    # assert f({"x": 1}) == "1"
    # f = format_context("{}_{}", "x", "y")
    # with pytest.raises(lena.core.LenaKeyError):
    #     # "y" not found in context
    #     f({"x": 1})
    # assert f({"x": 1, "y": 2}) == "1_2"
    # # redundant arguments don't play a role
    # assert f({"x": 1, "y": 2, "z": 3}) == "1_2"
    # # missing key raises
    # f = format_context("{}", "x")
    # with pytest.raises(lena.core.LenaKeyError):
    #     f({"u": 1})
    # f = format_context("{x}", "x")
    # with pytest.raises(lena.core.LenaKeyError):
    #     f({"u": 1})

    # ## keyword arguments
    # f = format_context("{x}", x="u")
    # assert f({"u": 1}) == "1"
    # # nested keys in keyword arguments
    # f = format_context("{y}", y="x.y")
    # assert f({"x": {"y": 10}}) == "10"
    # assert format_context("{y}_{x}", x="y", y="x")({"x": 1, "y": 2}) == "1_2"
    # with pytest.raises(lena.core.LenaKeyError):
    #     # keyword arguments in format string must be keywords in arguments
    #     assert format_context("{y}_{x}", "x", "y")({"x": 2, "y": 2}) == "1_2"

    # ## mix of keyword and positional arguments
    # f = format_context("{}_{x}_{y}", "x", x="x", y="y")
    # assert f({"x": 1, "y": 2}) == "1_1_2"

    # # nested keys in positional arguments
    # f = format_context("{}", "x.y")
    # assert f({"x": {"y": 10}}) == "10"
    # # error
    # # f = format_context("{x.y}", {"x.y": "x.y"})
    # # assert f({"x": {"y": 10}}) == "10"

    # not implemented
    # with pytest.raises(lena.core.LenaValueError):
    #     format_context("{a_string")


def test_get_recursively():
    # test wrong input parameters
    with pytest.raises(lena.core.LenaTypeError):
        get_recursively("must be a dict", "output.latex.name")

    context = {"output": {"latex": {"name": "x"}}}
    with pytest.raises(lena.core.LenaTypeError):
        get_recursively(context, ["output", True])
    with pytest.raises(lena.core.LenaTypeError):
        get_recursively(context, True)

    # empty keys return context
    assert get_recursively(context, {}) is context
    assert get_recursively(context, "") is context
    assert get_recursively(context, []) is context
    # test str as input
    assert get_recursively(context, "output.latex.name") == "x"
    assert get_recursively(context, "output.latex.name.x", default="default") == "default"
    # test default keyword
    assert get_recursively(context, "out", default=None) is None
    assert get_recursively(context, "out", default="default") == "default"
    # list as input
    assert get_recursively(context, ["output", "latex", "name"], default="") == "x"
    assert get_recursively(context, ["output", "latex"], default="") == {"name": "x"}
    # missing values raise
    with pytest.raises(lena.core.LenaKeyError):
        get_recursively(context, "output.lalalatex")
    with pytest.raises(lena.core.LenaKeyError):
        get_recursively(context, "out")
    with pytest.raises(lena.core.LenaKeyError):
        get_recursively(context, ["output", "latex", "name???"])
    with pytest.raises(lena.core.LenaKeyError):
        get_recursively(context, ["output", "latex??", "name???"])

    ## test dict as input
    assert get_recursively(context, {"output": {"latex": "name"}}) == "x"
    # only one key at a level is allowed
    with pytest.raises(lena.core.LenaValueError):
        get_recursively(context, {"output": {"latex": "name"}, "a": 1})


def test_intersection():
    # intersection with self is self
    d1 = {1: "1", 2: "2"}
    d2 = dict(d1)
    assert intersection(d1, d2) == d1

    # intersection with empty dictionary is empty
    assert intersection(d1, {}) == {}
    assert intersection({}, d1) == {}

    d3 = {3: "3"}
    assert intersection(d1, d3) == {}
    d4 = {1: "3"}
    assert intersection(d1, d4) == {}
    d5 = {1: "3", 2: "2"}
    assert intersection(d1, d5) == {2: "2"}
    assert intersection() == {}

    # nested intersection works
    d1 = {1: "1", 2: {3: "3", 4: "4"}}
    d2 = {2: {4: "4"}}
    assert intersection(d1, d2) == d2

    # dicts must contain only dictionaries
    with pytest.raises(lena.core.LenaTypeError):
        lena.context.intersection([])

    # test level
    assert intersection(d1, d1, level=0) == d1
    assert intersection(d1, d2, level=0) == {}
    assert intersection(d1, d2, level=1) == {}
    assert intersection(d1, d2, level=2) == d2

    # wrong keyword arguments
    with pytest.raises(lena.core.LenaTypeError):
        intersection(d1, d2, wrong_kw=True)


def test_iterate_update():
    context = {"output": {"latex": {"name": "x"}}}
    updates = [{"scale": "log"}, {"scale": "normal"}]
    assert list(iterate_update(context, updates)) == [
        {'output': {'latex': {'name': 'x'}}, 'scale': 'log'}, 
        {'output': {'latex': {'name': 'x'}}, 'scale': 'normal'}
        ]
    updates = [{"output": {"latex": {"name": "y"}}}]
    assert list(iterate_update(context, updates)) == [
        {'output': {'latex': {'name': 'y'}}}
        ]
    updates = [{"output": "latex"}]
    assert list(iterate_update(context, updates)) == [
        {'output': 'latex'}
        ]
    updates = [{}]
    assert list(iterate_update(context, updates)) == [context]
    assert context == {"output": {"latex": {"name": "x"}}}
    updates = []
    assert list(iterate_update(context, updates)) == []


def test_make_context():
    class Obj():
        scale = 2
        _dim = 1
        foo = None
        name = "obj"
    assert (lf.make_context(Obj(), "scale", "_dim", "foo") ==
            {'dim': 1, 'scale': 2})


def test_str_to_dict():
    # empty string produces an empty dict
    assert lena.context.str_to_dict("") == {}
    # otherwise s must have at least two dot-separated parts
    with pytest.raises(lena.core.LenaValueError):
        lena.context.str_to_dict("s")
    # dictionary is returned unchanged
    d = {"d": "d"}
    assert lena.context.str_to_dict(d) == d


def test_str_to_list():
    # empty string produces an empty list
    assert lena.context.str_to_list("") == []
    assert lena.context.str_to_list(".a..") == ["", "a", "", ""]


def test_update_nested():
    d1 = {"a": 1, "b": {"c": 3}}
    d2 = {"b": {"d": 4}}
    # dict must contain only one element
    with pytest.raises(lena.core.LenaValueError):
        update_nested(d2, d1)
    update_nested(d1, d2)
    assert d2 == {'b': {'c': 3, 'd': 4}}
    assert d1 == {'a': 1, 'b': {'c': 3, 'd': 4}}
    d1 = {"a": 1, "b": "c"}
    d2 = {"b": {"d": 4}}
    # d[key] must be a dictionary
    with pytest.raises(lena.core.LenaValueError):
        update_nested(d1, d2)
    # simple update works
    d1 = {"a": 1, "b": 2}
    d2 = {"c": 3}
    update_nested(d1, d2)
    assert d1 == {"a": 1, "b": 2, "c": 3}
    assert d2 == {"c": 3}


def test_update_recursively():
    d1 = {"a": 1, "b": {"c": 3}}
    d2 = {"b": {"d": 4}}
    update_recursively(d1, d2)
    assert d1 == {"a": 1, "b": {"c": 3, "d": 4}}
    update_recursively(d1, {"b": 2})
    assert d1 == {"a": 1, "b": 2}
    update_recursively(d1, {"e": {"f": 2}})
    assert d1 == {"a": 1, "b": 2, "e": {"f": 2}}
    with pytest.raises(lena.core.LenaTypeError):
        update_recursively(1, {})
    update_recursively(d1, {"a": {"b": "c"}})
    assert d1 == {"a": {"b": "c"}, "b": 2, "e": {"f": 2}}
