from __future__ import print_function

import pytest

import lena.core, lena.output
from lena.output import MakeFilename
from lena.context import format_context


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
        MakeFilename(make_filename={})
    # empty arguments are prohibited
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename()
    # not a tuple
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(make_filename=0)
    # wrong format_str
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(make_filename=0)

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
    mk = MakeFilename(make_filename="out")
    res = list(mk.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == [None, "ext"]
    # make_filename and make_fileext work
    mk = MakeFilename(make_filename="out", make_fileext="txt")
    res = list(mk.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == ["txt", "ext"]
    # works without context or without context.output
    res = list(mk.run([0, (1, {})]))
    assert list(map(filename, res)) == ["out", "out"]
    assert list(map(fileext, res)) == ["txt", "txt"]
    # works with real formatting
    val = (0, {"datatype": "MC"})
    mk = MakeFilename(make_filename="{datatype}")
    good_res = [(0, {"datatype": "MC", "output": {"filename": "MC"}})]
    assert list(mk.run([val])) == good_res
    mk = MakeFilename(make_filename="{datatype}")
    assert list(mk.run([val])) == good_res
    # ignores formatting errors
    assert list(mk.run([0])) == [0]

    # Sequence works
    # MakeFilename inside MakeFilename must give same results
    mks = MakeFilename(mk)
    assert list(mks.run([val])) == good_res
    assert list(mks.run([0])) == [0]
    mks = MakeFilename(mk, MakeFilename(make_filename="out"))
    # context in old data was already changed.
    data = [(0, {"output": {"filename": "exists"}}),
            (1, {"output": {"fileext": "ext"}}),
           ]
    res = list(mks.run(data))
    assert list(map(filename, res)) == ["exists", "out"]
    assert list(map(fileext, res)) == [None, "ext"]
    # several values in Sequence work
    assert list(map(filename, mks.run(data + [val]))) == ["exists", "out", "MC"]
