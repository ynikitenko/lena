import pytest

from lena.core import Sequence, Source, FillRequest, FillRequestSeq, Run
from lena.core import LenaNotImplementedError, LenaTypeError
from lena.flow import Print
from lena.flow import Slice, CountFrom
from lena.math import Mean, Sum


# it seems I can't replace cnt1 with CountFrom,
# because that is not iterable. todo: reconsider Source.
def cnt1():
    i = 1
    while True:
        yield i
        i = i + 1


def ones():
    while True:
        yield 1


def test_fill_request_seq():
    s1 = Source(
        ones,
        FillRequestSeq(
            FillRequest(Sum(start=0), reset=False),
            # this line is necessary, which is wrong!
            reset=False,
            bufsize=1
        ),
        Slice(10)
    )
    assert list(s1()) == list(range(1, 11))


def test_fill_request_seq_old():
    # FR with preprocess
    # todo: understand next todo.
    # todo: really 3 reset=False?

    # how not to write tests. Unclear what the result should be.
    # But I remember that I carefully checked that when written.
    s1 = Source(
        cnt1,
        # this FillRequest is optional
        FillRequest(
            FillRequestSeq(
                lambda x: x-1,
                FillRequest(Sum(start=0), reset=False),
                # lambda x: x
                reset=False,
            ),
            reset=False,
        ),
        Slice(10)
    )
    assert list(s1()) == [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]

    # FR with postprocess works
    s2 = Source(
        cnt1,
        FillRequestSeq(
            FillRequest(Sum(start=0), reset=False),
            lambda x: x-1,
            reset=False,
        ),
        Slice(10)
    )
    assert list(s2()) == [0, 2, 5, 9, 14, 20, 27, 35, 44, 54]

    # bufsize initialization works
    frs = FillRequestSeq(FillRequest(Sum()))
    assert frs._bufsize == 1
    frs2 = FillRequestSeq(FillRequest(Sum()), bufsize=2)
    assert frs2._bufsize == 2

    # wrong keyword raises
    with pytest.raises(LenaTypeError):
        FillRequestSeq(FillRequest(Sum()), unknown=True)

    # wrong subclassing raises (need to implement fill)
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
