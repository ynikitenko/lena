from __future__ import print_function

import os
import pytest
import sys

import lena.core
from lena.output import Writer


def test_writer_makefilename():
    w = Writer("", "x")
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
    w1 = Writer()
    assert w1._make_filename({}) == ("", "output", "txt", "output.txt")
    w2 = Writer("output")
    # in fact, directory path is not appended in this function
    path = os.path.join("output", "output.txt")
    assert w2._make_filename({}) == ("", "output", "txt", path)
    with pytest.raises(lena.core.LenaRuntimeError):
        w2._make_filename({"filename": ""})


def test_writer():
    # test init
    with pytest.raises(lena.core.LenaTypeError):
        Writer(1)
    with pytest.raises(lena.core.LenaTypeError):
        Writer(output_filename=1)
    w1 = Writer()
    # unwritten values pass unchanged
    indata = [1, 2, 
              (3, {}),
              (4, {"output": ("writer", True)}),
              (5, {"output": {"writer": False}}),
             ]
    assert list(w1.run(indata)) == indata
    with pytest.raises(lena.core.LenaRuntimeError):
        list(w1.run([("0", {"output": {"filename": ""}})]))


def test_writer_writes(mocker):
    m = mocker.mock_open()
    if sys.version[0] == "2":
        mocker.patch("__builtin__.open", m)
    else:
        mocker.patch("builtins.open", m)
    mocker.patch("os.path.exists", lambda val: val == "")
    w1 = Writer()
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
    w2 = Writer("output")
    res = list(w2.run(data))
    assert makedirs.mock_calls == [call("output")]
