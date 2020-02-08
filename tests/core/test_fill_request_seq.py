from __future__ import print_function

import pytest

from lena.core import Sequence, Source, FillRequest, FillRequestSeq, Run
from lena.core import LenaNotImplementedError, LenaTypeError
from lena.flow import Print
from lena.flow import ISlice
from lena.math import Mean, Sum


mul2 = lambda val: 2 * val


def cnt1(): 
    i = 1
    while True:
        yield i
        i = i + 1


def test_fill_request_seq():
    # FR with preprocess
    s1 = Source(
        cnt1,
        # this FillRequest is optional
        FillRequest(FillRequestSeq(
            lambda x: x-1,
            FillRequest(Sum(start=0), request="compute"),
            # lambda x: x
            )
        ),
        ISlice(10)
    )
    assert list(s1()) == [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]
    # FR with postprocess
    s2 = Source(
        cnt1,
        FillRequestSeq(
            FillRequest(Sum(start=0), request="compute"),
            lambda x: x-1,
        ),
        ISlice(10)
    )
    assert list(s2()) == [0, 2, 5, 9, 14, 20, 27, 35, 44, 54]
    # this works
    frs = FillRequestSeq(FillRequest(Sum()))
    assert frs.bufsize == 1
    frs2 = FillRequestSeq(FillRequest(Sum()), bufsize=2)
    assert frs2.bufsize == 2
    # wrong keyword
    with pytest.raises(LenaTypeError):
        FillRequestSeq(FillRequest(Sum()), unknown=True)

    # wrong subclass
    class MyFR(FillRequestSeq):
        def __init__(self):
            pass
    myfr = MyFR()
    with pytest.raises(LenaNotImplementedError):
        myfr.fill(0)

    # fill with preprocess works
    s3 = FillRequestSeq(
        lambda x: x-1,
        FillRequest(Sum()),
    )
    flow = list(range(0, 4))
    for val in flow:
        s3.fill(val)
    assert list(s3.request()) == [2]

    # direct fill works
    s4 = FillRequestSeq(
        FillRequest(Sum()),
    )
    for val in flow:
        s4.fill(val)
    assert list(s4.request()) == [6]
