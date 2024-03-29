import pytest

from lena.core import Sequence, Source, FillCompute, FillComputeSeq, Run
from lena.core import LenaNotImplementedError, LenaTypeError
from lena.core import is_fill_compute_seq
from lena.flow import Print
from lena.flow import Slice
from lena.math import Mean


mul2 = lambda val: 2 * val


def cnt1(): 
    i = 1
    while True:
        yield i
        i = i + 1


def test_fill_compute_seq():
    # wrong initialization
    # no FillCompute element
    with pytest.raises(LenaTypeError):
        FillComputeSeq(lambda x: x)
    # Run can't be cast to a FillInto element
    with pytest.raises(LenaTypeError):
        FillComputeSeq(Run(Mean()), Mean())

    s1 = Source(cnt1, mul2, Slice(10), FillCompute(Mean()))
    assert next(s1()) == 11.

    s2 = Source(cnt1, Slice(10), FillComputeSeq(Mean(), mul2))
    assert list(s2()) == [11.]

    s3 = Source(cnt1, Slice(10), FillComputeSeq(mul2, FillCompute(Mean())))
    assert next(s3()) == 11.0

    s4 = Source(cnt1, Slice(10), FillComputeSeq(mul2, FillCompute(Mean()), Print()))
    assert next(s4()) == 11.0

    s5 = FillComputeSeq(mul2, FillCompute(Mean()), Print())

    assert is_fill_compute_seq(Mean())
    # Source is not fill_compute_seq. It's also non-iterable.
    assert not is_fill_compute_seq(s4)

    # Test Source containing FillComputeSeq
    # test LenaSequence
    # can take len
    assert len(s1) == 4
    assert len(s2) == 3
    assert len(s3) == 3
    assert len(s4) == 3
    # can get item
    assert isinstance(s2[1], Slice)

    # Test FillComputeSeq
    assert len(s5) == 3
    # can get item
    assert isinstance(s5[1], FillCompute)
    # deletion is prohibited
    with pytest.raises(TypeError):
        del s5[0]
    # setting elements is prohibited
    with pytest.raises(TypeError):
        s5[0] = 0

    # wrong subclass
    class MyFC(FillComputeSeq):
        def __init__(self):
            pass
    myfc = MyFC()
    with pytest.raises(LenaNotImplementedError):
        myfc.fill(0)
