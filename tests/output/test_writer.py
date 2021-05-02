from __future__ import print_function

import copy
import os
import pytest
import sys
import warnings

import lena.core
from lena.output import Write


def test_write_makefilename():
    w = Write("", "x")
    # default name for empty context
    assert w._make_filename({}) == ("", "x", "txt", "x.txt")
    # name from context
    context = {"output": {"filename": "y", "filetype": "csv"}}
    val = ("text", context)
    outputc = context["output"]
    assert w._make_filename(outputc) == ("", "y", "csv", "y.csv")
    outputc = {"filename": "y", "fileext": "csv"}
    assert w._make_filename(outputc) == ("", "y", "csv", "y.csv")
    # default filename
    w1 = Write()
    assert w1._make_filename({}) == ("", "output", "txt", "output.txt")
    w2 = Write("output")
    # in fact, directory path is not appended in this function
    path = os.path.join("output", "output.txt")
    assert w2._make_filename({}) == ("", "output", "txt", path)
    with pytest.raises(lena.core.LenaRuntimeError):
        w2._make_filename({"filename": ""})


def test_write():
    # test init
    with pytest.raises(lena.core.LenaTypeError):
        Write(1)
    with pytest.raises(lena.core.LenaTypeError):
        Write(output_filename=1)
    with pytest.raises(lena.core.LenaValueError):
        Write(existing_unchanged=True, overwrite=True)
    w1 = Write()
    # unwritten values pass unchanged
    indata = [1, 2, 
              (3, {}),
              # note that context.output is not a dict!
              (4, {"output": ("write", True)}),
              ("5", {"output": {"write": False}}),
              # only here data part is checked
              (6, {"output": {"write": True}}),
             ]
    assert list(w1.run(indata)) == indata
    # empty filename is prohibited
    with pytest.raises(lena.core.LenaRuntimeError):
        list(w1.run([("0", {"output": {"filename": ""}})]))


def test_write_writes(mocker):
    m = mocker.mock_open()
    if sys.version[0] == "2":
        mocker.patch("__builtin__.open", m)
    else:
        mocker.patch("builtins.open", m)
    # otherwise the current directory "" would be absent
    mocker.patch("os.path.exists", lambda val: val == "")

    w1 = Write()
    data = [("0", {"output": {"filename": "y", "filetype": "csv"}})]
    res = list(w1.run(data))
    call = mocker.call
    assert m.mock_calls == [
        call("y.csv", "w"), call().__enter__(),
        call().write("0"), call().__exit__(None, None, None)
    ]
    assert res == [("y.csv", {"output": {"filename": "y",
                                         "fileext": "csv",
                                         "filetype": "csv",
                                         "filepath": "y.csv"}
                             })]

    makedirs = mocker.patch("os.makedirs")
    w2 = Write("output")
    res = list(w2.run(data))
    assert makedirs.mock_calls == [call("output")]

    # test one line where file name is not joined with file extension
    data_empty_ext = [("0", {"output": {"filename": "y", "fileext": ""}})]
    assert list(w2.run(data_empty_ext)) == [
        ('output/y',
         {'output': {'fileext': '', 'filename': 'y', 'filepath': 'output/y'}})
    ]

    # absolute paths raise warnings
    data_absolute_path = [("0", {"output": {"filename": "y", "dirname": "/tmp"}})]
    with pytest.warns(RuntimeWarning):
        assert list(w2.run(data_absolute_path)) == [
            ('output/tmp/y.txt',
             {'output': {'dirname': '/tmp',
                         'fileext': 'txt',
                         'filename': 'y',
                         'filepath': 'output/tmp/y.txt'}})
        ]


def test_write_changed(mocker):
    m = mocker.mock_open()
    if sys.version[0] == "2":
        mocker.patch("__builtin__.open", m)
    else:
        mocker.patch("builtins.open", m)
    mocker.patch("os.path.exists", lambda _: True)

    # overwrite set to True always overwrites
    data = [("1", {"output": {"filename": "x"}})]
    w_overwrite = Write(overwrite=True)
    assert list(w_overwrite.run(data)) == [
        ('x.txt',
         {'output': {'changed': True,
                     'fileext': 'txt',
                     'filename': 'x',
                     'filepath': 'x.txt'}}),
    ]
    # data is actually "written"
    call = mocker.call
    assert m.mock_calls == [
        call("x.txt", "w"), call().__enter__(),
        call().write("1"), call().__exit__(None, None, None)
    ]
    # context is updated in place
    assert data[0][1]["output"]["changed"] is True

    # existing_unchanged skips all existing files
    data_2 = [("2", {"output": {"filename": "x"}})]
    w_unchanged = Write(existing_unchanged=True)
    # clear the list of calls
    m.reset_mock()
    assert list(w_unchanged.run(copy.deepcopy(data_2))) == [
        ('x.txt',
         {'output': {'changed': False,
                     'fileext': 'txt',
                     'filename': 'x',
                     'filepath': 'x.txt'}}),
    ]
    # nothing was actually written
    assert m.mock_calls == []


def test_write_cached(mocker):
    m = mocker.mock_open(read_data="1")
    if sys.version[0] == "2":
        mocker.patch("__builtin__.open", m)
    else:
        mocker.patch("builtins.open", m)
    mocker.patch("os.path.exists", lambda _: True)
    data_1 = [("1", {"output": {"filename": "x"}})]

    # unchanged data is not written
    assert list(Write().run(copy.deepcopy(data_1))) == [
        ('x.txt',
         {'output': {'changed': False,
                     'fileext': 'txt',
                     'filename': 'x',
                     'filepath': 'x.txt'}})
    ]
    call = mocker.call
    assert m.mock_calls == [
        call("x.txt"), call().__enter__(),
        call().read(-1), call().__exit__(None, None, None)
    ]
    m.reset_mock()

    # even if file is unchanged, context.output.changed remains the same
    data_changed = [("1", {"output": {"filename": "x", "changed": True}})]
    assert list(Write().run(copy.deepcopy(data_changed))) == [
        ('x.txt',
         {'output': {'changed': True,
                     'fileext': 'txt',
                     'filename': 'x',
                     'filepath': 'x.txt'}})
    ]
    # no writes were done, as before
    assert m.mock_calls == [
        call("x.txt"), call().__enter__(),
        call().read(-1), call().__exit__(None, None, None)
    ]


def test_write_changed_data(mocker):
    m = mocker.mock_open(read_data="pi")
    if sys.version[0] == "2":
        mocker.patch("__builtin__.open", m)
    else:
        mocker.patch("builtins.open", m)
    mocker.patch("os.path.exists", lambda _: True)

    # changed data is written
    data_changed = [("1", {"output": {"filename": "x_changed"}})]
    # changed is True
    assert list(Write().run(copy.deepcopy(data_changed))) == [
        ('x_changed.txt',
         {'output': {'changed': True,
                     'fileext': 'txt',
                     'filename': 'x_changed',
                     'filepath': 'x_changed.txt'}})
    ]
    call = mocker.call
    # file is read and then written with 1
    assert m.mock_calls == [
        call("x_changed.txt"), call().__enter__(),
        call().read(-1),
        call().__exit__(None, None, None),
        call('x_changed.txt', 'w'),
        call().__enter__(),
        call().write('1'),
        call().__exit__(None, None, None)
    ]
