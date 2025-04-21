from copy import deepcopy

import pytest

import lena
from lena.core import LenaTypeError, LenaKeyError, LenaValueError
from lena.context import (
    contains, difference, format_context, format_update_with,
    get_recursively,
    intersection,
    str_to_dict, str_to_list, to_string,
    update_recursively, update_nested,
)


def test_contains():
    d = {'a': {'b': 'c d'}, 'e': 1}
    assert contains(d, "a") is True
    assert contains(d, "a.b.c d") is True
    assert contains(d, "b.c") is False
    assert contains(d, "a.b") is True
    # not string contents are cast to strings
    assert contains(d, "e.1") is True
    ## test values with exception when cast to string
    class NoString():
        def __repr__(self):
            raise ValueError
    badd = {"key": NoString()}
    assert contains(badd, "key.1") is False


def test_difference():
    d1 = {'a': {'b': 'c d'}, 'e': 'f'}
    d2 = {'a': d1['a']}
    # difference with an empty dict works
    assert difference({}, d1) == {}
    assert difference(d1, {}) == d1

    # difference with self is empty
    assert difference(d1, d1) == {}

    # difference with not a dictionary works
    assert difference(d1, None) == d1
    assert difference(None, d1) == None
    # level 1 difference between similar dicts
    assert difference(d1, d2, level=1) == {'e': 'f'}
    # level 0 difference
    assert difference(d1, d2, level=0) == d1

    d3 = {'a': {'b': {"c d": 'e'}}}
    d4 = {'a': {'b': {"c d": 'e', "f": "g"}}}
    # Completely different. Complicated, but True
    assert difference(d1, d3, level=-1) == d1
    # One is contained in another.
    assert difference(d3, d4, level=-1) == {}

    # Some actual difference exists
    d5 = {'a': {'b': {"c d": 'e', "h": "i"}}}
    assert difference(d5, d4, level=-1) == {'a': {'b': {'h': 'i'}}}

    # a more important property is that
    # d1.diff(d2) + d1.intersection(d2) = d1.


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
    # with pytest.raises(LenaKeyError):
    #     f({"x": {"y": 10}})

    ## special formatting works
    f = format_context("{{x!r}}")
    assert f({"x": 10}) == "10"
    f = format_context("{{x:*^4}}")
    assert f({"x": 10}) == "*10*"

    # missing values raise LenaKeyError
    with pytest.raises(LenaKeyError):
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
    # with pytest.raises(LenaKeyError):
    #     # "y" not found in context
    #     f({"x": 1})
    # assert f({"x": 1, "y": 2}) == "1_2"
    # # redundant arguments don't play a role
    # assert f({"x": 1, "y": 2, "z": 3}) == "1_2"
    # # missing key raises
    # f = format_context("{}", "x")
    # with pytest.raises(LenaKeyError):
    #     f({"u": 1})
    # f = format_context("{x}", "x")
    # with pytest.raises(LenaKeyError):
    #     f({"u": 1})

    # ## keyword arguments
    # f = format_context("{x}", x="u")
    # assert f({"u": 1}) == "1"
    # # nested keys in keyword arguments
    # f = format_context("{y}", y="x.y")
    # assert f({"x": {"y": 10}}) == "10"
    # assert format_context("{y}_{x}", x="y", y="x")({"x": 1, "y": 2}) == "1_2"
    # with pytest.raises(LenaKeyError):
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
    # with pytest.raises(LenaValueError):
    #     format_context("{a_string")


def test_format_update_with():
    fuw = format_update_with

    # key formatting and update works
    d = {"detector": "FDI", "data_type": "data"}
    d1 = deepcopy(d)
    key, val = ("name", "{{detector}}_{{data_type}}")
    fuw(key, val, d1)
    assert d1 == {'data_type': 'data', 'detector': 'FDI',
                  'name': 'FDI_data',}

    # missing key raises
    with pytest.raises(LenaKeyError):
        fuw(key, val, {})

    # a trivial value updates context properly
    key2, val2 = ("key", 1)
    d2 = {}
    fuw(key2, val2, d2)
    assert d2 == {"key": 1}

    # a string without formatting updates context properly
    key3, val3 = ("key", "value")
    d3 = {}
    fuw(key3, val3, d3)
    assert d3 == {"key": "value"}


def test_get_recursively():
    # test wrong input parameters
    with pytest.raises(LenaTypeError):
        get_recursively("must be a dict", "output.latex.name")

    context = {"output": {"latex": {"name": "x"}}}
    with pytest.raises(LenaTypeError):
        get_recursively(context, ["output", True])
    with pytest.raises(LenaTypeError):
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
    with pytest.raises(LenaKeyError):
        get_recursively(context, "output.lalalatex")
    with pytest.raises(LenaKeyError):
        get_recursively(context, "out")
    with pytest.raises(LenaKeyError):
        get_recursively(context, ["output", "latex", "name???"])
    with pytest.raises(LenaKeyError):
        get_recursively(context, ["output", "latex??", "name???"])

    ## test dict as input
    assert get_recursively(context, {"output": {"latex": "name"}}) == "x"
    # only one key at a level is allowed
    with pytest.raises(LenaValueError):
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
    with pytest.raises(LenaTypeError):
        intersection([])

    # test level
    assert intersection(d1, d1, level=0) == d1
    assert intersection(d1, d2, level=0) == {}
    assert intersection(d1, d2, level=1) == {}
    assert intersection(d1, d2, level=2) == d2

    # wrong keyword arguments
    with pytest.raises(LenaTypeError):
        intersection(d1, d2, wrong_kw=True)


def test_str_to_dict():
    ## test with only one argument
    # empty string produces an empty dict
    assert str_to_dict("") == {}
    # otherwise s must have at least two dot-separated parts
    with pytest.raises(LenaValueError):
        str_to_dict("s")
    # this functionality is removed.
    # # dictionary is returned unchanged
    # d = {"d": "d"}
    # assert str_to_dict(d) == d

    ## test with an explicit value
    # short strings are prohibited
    with pytest.raises(LenaValueError):
        str_to_dict("", 5)
    assert str_to_dict("s", 5) == {"s": 5}


def test_str_to_list():
    # empty string produces an empty list
    assert str_to_list("") == []
    assert str_to_list(".a..") == ["", "a", "", ""]


def test_to_string():
    # a dictionary with a nested subdictionary can be formatted
    d1 = {"a": 1, "b": {"c": 3}}
    assert to_string(d1) == '{"a":1,"b":{"c":3}}'

    # a dictionary with a list can be formatted
    d2 = {"a": [1, 2, 3]}
    assert to_string(d2) == '{"a":[1,2,3]}'

    # unserializable types raise
    with pytest.raises(LenaValueError) as err:
        to_string({"a": set()})
    assert str(err.value) in (
        """can not serialize. TypeError("Object of type \'set\' is not JSON serializable",)""",  # 3.6
        "can not serialize. TypeError('Object of type set is not JSON serializable')",
        "can not serialize. TypeError('set([]) is not JSON serializable',)"
    )


def test_update_nested():
    d1 = {"a": 1, "b": {"c": 3}}
    d2 = {"d": 4}
    update_nested("b", d1, d2)
    # d2 is updated with values from d1
    assert d2 == {'d': 4, 'b': {'c': 3}}
    # old key from d1 is inserted into d1["b"]["b"]
    assert d1 == {'a': 1, 'b': {'b': {'c': 3}, 'd': 4}}

    d1 = {"a": 1, "b": {"c": 3}}
    d2 = {"d": 4}
    update_nested("e", d1, d2)
    # if key is not present in d1, it is simply inserted there
    assert d1 == {'a': 1, 'b': {'c': 3}, 'e': {'d': 4}}

    # recursive d2 is forbidden
    d1 = {"d": {}}
    d2 = {}
    d2["d"] = d2
    with pytest.raises(LenaValueError):
        update_nested("d", d1, d2)


def test_update_recursively():
    d1 = {"a": 1, "b": {"c": 3}}
    d2 = {"b": {"d": 4}}
    update_recursively(d1, d2)
    assert d1 == {"a": 1, "b": {"c": 3, "d": 4}}
    update_recursively(d1, {"b": 2})
    assert d1 == {"a": 1, "b": 2}
    update_recursively(d1, {"e": {"f": 2}})
    assert d1 == {"a": 1, "b": 2, "e": {"f": 2}}
    with pytest.raises(LenaTypeError):
        update_recursively(1, {})
    update_recursively(d1, {"a": {"b": "c"}})
    assert d1 == {"a": {"b": "c"}, "b": 2, "e": {"f": 2}}

    ## test explicit value
    d_empty = {}
    update_recursively(d_empty, "output.changed", True)
    assert d_empty == {"output": {"changed": True}}
    with pytest.raises(LenaValueError):
        update_recursively(d_empty, {"a": "b"}, "fail")
