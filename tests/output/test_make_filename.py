from __future__ import print_function

import copy
import pytest

import lena.core, lena.output
from lena.output import MakeFilename
from lena.context import format_context


def test_make_filename_init():
    # all format arguments must be strings
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(0)
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(filename=0)
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(dirname=0)
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(fileext=0)

    # zero arguments are prohibited
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename()

    # wrong format_str
    with pytest.raises(lena.core.LenaValueError):
        MakeFilename(filename="{}}")

def test_make_filename():
    data = [(0, {"output": {"filename": "exists"}}),
            (1, {"output": {"fileext": "ext"}}),
           ]
    filename = lambda val: val[1]["output"].get("filename")
    dirname = lambda val: val[1]["output"].get("dirname")
    fileext = lambda val: val[1]["output"].get("fileext")

    # single argument string works
    mk = MakeFilename("out")
    res = list(map(mk, copy.deepcopy(data)))
    assert list(map(filename, res))[1] == "out"
    assert list(map(fileext, res)) == [None, "ext"]
    assert list(map(dirname, res)) == [None, None]

    # single make_filename works, overwrite works
    mk = MakeFilename(filename="out", overwrite=True)
    res = list(map(mk, copy.deepcopy(data)))
    assert list(map(filename, res)) == ["out", "out"]
    assert list(map(fileext, res)) == [None, "ext"]
    assert list(map(dirname, res)) == [None, None]

    # dirname works
    mk = MakeFilename(dirname="out")
    res = list(map(mk, copy.deepcopy(data)))
    assert list(map(dirname, res)) == ["out", "out"]

    # fileext works
    mk = MakeFilename(fileext="ext")
    res = list(map(mk, copy.deepcopy(data)))
    assert list(map(fileext, res)) == ["ext", "ext"]

    # filename and fileext work
    mk = MakeFilename(filename="out", fileext="txt")
    res = list(map(mk, copy.deepcopy(data)))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == ["txt", "ext"]

    # works without context or without context.output
    res = list(map(mk, ([0, (1, {})])))
    assert list(map(filename, res)) == ["out", "out"]
    assert list(map(fileext, res)) == ["txt", "txt"]
    # values are unchanged
    assert res[0][0] == 0 and res[1][0] == 1

    # works with real formatting
    val = (0, {"datatype": "MC"})
    mk = MakeFilename(filename="{{datatype}}")
    good_res = (0, {"datatype": "MC", "output": {"filename": "MC"}})
    assert mk(copy.deepcopy(val)) == good_res

    mk = MakeFilename(filename="{{datatype}}")
    # ignores formatting errors
    assert mk(0) == 0

    # context is unchanged
    d = {}
    assert mk((0, d))[1] is d
