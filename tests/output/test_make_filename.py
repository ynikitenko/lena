from __future__ import print_function

import pytest

import lena.core, lena.output
from lena.output import format_context, MakeFilename


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
    ## single format_str works
    f = format_context("{x}")
    assert f({"x": 10}) == "10"
    f = format_context("{x.y}")
    assert f({"x": {"y": 10}}) == "10"
    # special string doesn't work with keyword arguments
    f = format_context("{}_{x.y}", "x.y")
    with pytest.raises(lena.core.LenaKeyError):
        f({"x": {"y": 10}})
    ## special formatting works
    f = format_context("{x!r}")
    assert f({"x": 10}) == "10"
    f = format_context("{x:*^4}")
    assert f({"x": 10}) == "*10*"
    # fancy braces work
    f = format_context("{{{x}}}")
    assert f({"x": 10}) == "{10}"

    ## positional arguments work
    f = format_context("{}", "x")
    assert f({"x": 1}) == "1"
    f = format_context("{}_{}", "x", "y")
    with pytest.raises(lena.core.LenaKeyError):
        # "y" not found in context
        f({"x": 1})
    assert f({"x": 1, "y": 2}) == "1_2"
    # redundant arguments don't play a role
    assert f({"x": 1, "y": 2, "z": 3}) == "1_2"
    # missing key raises
    f = format_context("{}", "x")
    with pytest.raises(lena.core.LenaKeyError):
        f({"u": 1})
    f = format_context("{x}", "x")
    with pytest.raises(lena.core.LenaKeyError):
        f({"u": 1})

    ## keyword arguments
    f = format_context("{x}", x="u")
    assert f({"u": 1}) == "1"
    # nested keys in keyword arguments
    f = format_context("{y}", y="x.y")
    assert f({"x": {"y": 10}}) == "10"
    assert format_context("{y}_{x}", x="y", y="x")({"x": 1, "y": 2}) == "1_2"
    with pytest.raises(lena.core.LenaKeyError):
        # keyword arguments in format string must be keywords in arguments
        assert format_context("{y}_{x}", "x", "y")({"x": 2, "y": 2}) == "1_2"

    ## mix of keyword and positional arguments
    f = format_context("{}_{x}_{y}", "x", x="x", y="y")
    assert f({"x": 1, "y": 2}) == "1_1_2"

    # nested keys in positional arguments
    f = format_context("{}", "x.y")
    assert f({"x": {"y": 10}}) == "10"
    # error
    # f = format_context("{x.y}", {"x.y": "x.y"})
    # assert f({"x": {"y": 10}}) == "10"

    # simple string works!
    f = format_context("a_string")
    assert f({"x": 1}) == "a_string"


def test_make_filename():
    ## test initialization
    # string can't be used with other arguments
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename("a", lambda x: x)
    # positional arguments can't be mixed with keyword arguments
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(lambda x: x, make_filename=("str"))
    # unknown keyword arguments
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(Make_Filename=("str"))
    # bad keyword argument
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(make_filename="str")
    # empty arguments are prohibited
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename()
    # not a tuple
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(make_filename=0)
    # wrong format_str
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(make_filename=(0,))

    ## sometimes it actually works
    data = [(0, {"output": {"filename": "exists"}}),
            (1, {"output": {"fileext": "ext"}}),
           ]
    filename = lambda val: val[1]["output"].get("filename")
    fileext = lambda val: val[1]["output"].get("fileext")
    # single argument string works
    mk = MakeFilename("out")
    res = list(mk.run(data))
    assert list(map(filename, res))[1] == "out"
    assert list(map(fileext, res)) == [None, "ext"]
    # single make_filename works
    mk = MakeFilename(make_filename=("out",))
    res = list(mk.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == [None, "ext"]
    # make_filename and make_fileext work
    mk = MakeFilename(make_filename=("out",), make_fileext=("txt",))
    res = list(mk.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == ["txt", "ext"]
    # works without context or without context.output
    res = list(mk.run([0, (1, {})]))
    assert list(map(filename, res)) == ["out", "out"]
    assert list(map(fileext, res)) == ["txt", "txt"]
    # works with real formatting
    val = (0, {"datatype": "MC"})
    mk = MakeFilename(make_filename=("{}", "datatype"))
    good_res = [(0, {"datatype": "MC", "output": {"filename": "MC"}})]
    assert list(mk.run([val])) == good_res
    mk = MakeFilename(make_filename=("{datatype}", "datatype"))
    assert list(mk.run([val])) == good_res
    # ignores formatting errors
    assert list(mk.run([0])) == [0]
    # format_context works
    mk = MakeFilename(make_filename=format_context("{datatype}", datatype="datatype"))
    assert list(mk.run([val])) == good_res
    assert list(mk.run([0])) == [0]

    # Sequence works
    # MakeFilename inside MakeFilename must give same results
    mks = MakeFilename(mk)
    assert list(mks.run([val])) == good_res
    assert list(mks.run([0])) == [0]
    mks = MakeFilename(mk, MakeFilename(make_filename=("out",)))
    # context in old data was already changed.
    data = [(0, {"output": {"filename": "exists"}}),
            (1, {"output": {"fileext": "ext"}}),
           ]
    res = list(mks.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == [None, "ext"]
    # several values in Sequence work
    assert list(map(filename, mks.run(data + [val]))) == ["exists", "out", "MC"]
