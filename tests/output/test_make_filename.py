from __future__ import print_function

import copy
import pytest

import lena.core, lena.output
from lena.core import Sequence
from lena.flow import Print
from lena.output import MakeFilename
from lena.context import format_context


def test_make_filename_init():
    # all format arguments must be strings
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(0)

    # zero arguments are prohibited
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename()

    # wrong format_str
    with pytest.raises(lena.core.LenaValueError):
        MakeFilename(filename="{}}")

    # prefix and suffix must be provided separately with filename
    with pytest.raises(lena.core.LenaTypeError):
        MakeFilename(filename="filename", prefix="wrong_")


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


def test_make_filename_prefix_suffix():
    data = [(0, {"output": {"filename": "file_name"}})]
    mk1 = MakeFilename(suffix="_suff1", prefix="pref1_")
    mk2 = MakeFilename(suffix="_suff2", prefix="pref2_")

    # existing file names are unchanged
    seq12_1 = Sequence(mk1, Print(), mk2)
    assert list(seq12_1.run(copy.deepcopy(data))) == [(
        0, {'output':
            {'filename': 'file_name',
             'prefix': 'pref2_pref1_',
             'suffix': '_suff1_suff2'}}
    )]

    # prefix and suffix are properly added
    seq12_2 = Sequence(mk1, mk2, MakeFilename("filename"))
    assert list(seq12_2.run([0])) == [(
        0, {'output': {'filename': 'pref2_pref1_filename_suff1_suff2'}}
    )]

    ## Overwrite works
    # it doesn't harm when file name is produced
    mk3 = MakeFilename(suffix="_suff2", overwrite=True)
    seq13 = Sequence(mk1, mk3, MakeFilename("filename3"))
    assert list(seq13.run(copy.deepcopy(data))) == [
        (0, {'output':
             {'prefix': 'pref1_', 'suffix': '_suff2', 
              'filename': 'file_name'}})
    ]

    # it really works
    seq13_2 = Sequence(mk1, mk3, MakeFilename("filename132"))
    assert list(seq13_2.run([0])) == [
        (0, {'output': {'filename': 'pref1_filename132_suff2'}})
    ]

    # formatting arguments work
    mk4 = MakeFilename(prefix="{{a}}_")
    seq14 = Sequence(mk1, mk4, MakeFilename("filename14"))
    assert list(seq14.run([(0, {"a": "A"})])) == [
        (0, {'a': 'A', 'output': {'filename': 'A_pref1_filename14_suff1'}})
    ]
