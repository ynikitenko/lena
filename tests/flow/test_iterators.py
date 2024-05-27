import sys
from itertools import count, islice

import pytest
from hypothesis import strategies as s
from hypothesis import given

import lena.flow
from lena.core import Source, LenaStopFill
from lena.flow import DropContext, CountFrom, Reverse, Slice, StoreFilled

# all bugs converged to at most 3.
hypo_int_max = 20


def test_chain():
    nums = [1, 2, 3]
    lets = ['a', 'b']
    # chain with two iterables works
    c = lena.flow.Chain(nums, lets)
    assert list(c()) == nums + lets
    # empty chain works
    c = lena.flow.Chain()
    assert list(c()) == []


def test_count_from():
    s = Source(
        CountFrom(),
        Slice(10),
    )
    results = s()
    assert [result for result in s()] == list(range(10))

    # test start
    itstart = CountFrom(start=10)
    assert list(islice(itstart(), 5)) == list(range(10, 15))
    # test step
    itstep = CountFrom(step=2)
    assert list(islice(itstep(), 5)) == list(range(0, 10, 2))
    # test start and step 
    itss = CountFrom(start=10, step=2)
    assert list(islice(itss(), 5)) == list(range(10, 20, 2))

    # equality testing works
    assert itss == CountFrom(start=10, step=2)


def test_slice_run():
    c = count()
    ## __init__ and run work
    # stop works
    sl1 = Slice(10)
    assert repr(sl1) == "Slice(10)"
    list(sl1.run(c)) == list(range(0, 10))

    ## start, stop work
    # empty slice works
    sl2 = Slice(10, 10)
    assert repr(sl2) == "Slice(10, 10)"
    list(sl2.run(c)) == []

    c = count()
    # non-empty slice works
    sl3 = Slice(10, 15)
    list(sl3.run(c)) == list(range(10, 15))

    # start, stop, step work
    sl4 = Slice(0, 10, 2)
    assert repr(sl4) == "Slice(0, 10, 2)"
    list(sl4.run(count())) == list(range(0, 10, 2))


def test_negative_islice():
    # negative stop
    isl1 = Slice(-1)
    data = [0, 1, 2]
    assert list(isl1.run(iter(data))) == [0, 1]

    # positive start, negative stop
    isl2 = Slice(1, -1)
    assert list(isl2.run(iter(data))) == [1]

    # negative start, negative stop
    isl3 = Slice(-2, -1)
    assert list(isl3.run(iter(data))) == [1]

    # negative start, positive stop
    isl4 = Slice(-2, 2)
    assert list(isl4.run(iter(data))) == [1]

    ## step works
    s = slice(None, None, 2)
    isl5 = Slice(s.start, s.stop, s.step)
    assert list(isl5.run(iter(range(0, 6)))) == list(range(0, 6))[s.start:s.stop:s.step]

    # step with negative index works
    s = slice(-3, 3, 2)
    isl6 = Slice(s.start, s.stop, s.step)
    assert list(isl6.run(iter(range(0, 6)))) == list(range(0, 6))[s.start:s.stop:s.step]

    # initialization works correctly (seems not always)
    isl7 = Slice(-3, 5, None)
    assert (isl7._start, isl7._stop, isl7._step) == (-3, 5, 1)

    for s in [slice(-3, 3, 2), slice(-3, 4, 3), slice(-3, 5),
              # negative very large start should have no effect,
              # like getting all elements.
              slice(-100, 3)]:
        isl = Slice(s.start, s.stop, s.step)
        for data in [range(0), range(4), range(10), range(20)]:
            assert list(isl.run(iter(data))) == list(data)[s.start:s.stop:s.step]

    # to check it myself.
    isl8 = Slice(-100, 3)
    assert list(isl8.run(iter(range(5)))) == list(range(3))

    # step must be a natural number
    # negative step raises
    with pytest.raises(lena.core.LenaValueError):
        Slice(None, None, -1)
    # zero step raises
    with pytest.raises(lena.core.LenaValueError):
        Slice(None, None, 0)
    # it but raises
    with pytest.raises(lena.core.LenaValueError):
        Slice(-1, -1, 0)
    # it should raise also for non-integer numbers.
    with pytest.raises(lena.core.LenaValueError):
        Slice(-1, -1, 1.5)

    # found by hypothesis, but yesterday it was not found...
    # Pytest for the whole package doesn't show any error!
    # Is hypothesis reliable?..
    isl = Slice(-3, -1, 1)
    data = list(range(3))
    assert list(isl.run(iter(data))) == [0, 1]


start_stop_s = s.one_of(s.none(),
                        s.integers(-hypo_int_max, hypo_int_max))
step_s       = s.integers(1, hypo_int_max)

@given(start=start_stop_s, stop=start_stop_s, step=step_s,
       data_len=s.integers(0, hypo_int_max))
def test_islice_hypothesis(start, stop, step, data_len):
    data = list(range(data_len))
    isl = Slice(start, stop, step)
    assert list(isl.run(iter(data))) == data[start:stop:step]


def test_islice_fill_into():
    store = StoreFilled()
    # start, stop work
    isl = Slice(10, 15)
    for i in range(0, 15):
        isl.fill_into(store, i)
    assert store.group == list(range(10, 15))
    with pytest.raises(LenaStopFill):
        isl = Slice(10, 15)
        for i in range(0, 16):
            isl.fill_into(store, i)
    # step works
    store.reset()
    isl = Slice(10, 20, 2)
    # 18 will be filled last
    for i in range(0, 19):
        isl.fill_into(store, i)
    assert store.group == list(range(10, 20, 2))

    # found by hypothesis
    store = StoreFilled()
    isl = Slice(None, None, 1)
    data = [0]
    for val in data:
        isl.fill_into(store, val)
    assert store.group == [0]

    store = StoreFilled()
    isl = Slice(None, 1, 2)
    data = [0, 1]
    with pytest.raises(LenaStopFill):
        for val in data:
            isl.fill_into(store, val)
    assert store.group == [0]

    store = StoreFilled()
    isl = Slice(None, 2, 2)
    data = [0, 1]
    with pytest.raises(LenaStopFill):
        for val in data:
            isl.fill_into(store, val)
    assert store.group == [0]


start_stop_non_neg = s.one_of(s.none(),
                              s.integers(0, hypo_int_max))
@given(start=start_stop_non_neg,
       # stop=s.integers(0, hypo_int_max),
       stop=start_stop_non_neg,
       step=step_s,
       data_len=s.integers(1, hypo_int_max))
def test_islice_hypothesis_fill_into(start, stop, step, data_len):
    # data_len >= 1, because if the flow is empty,
    # there is nothing to check.
    data = list(range(data_len))
    isl = Slice(start, stop, step)
    if start is None:
        start = 0
    if stop is None:
        stop = sys.maxsize
    store = StoreFilled()
    if True:
    # to check this condition is pretty hard. For earliest raise
    # we don't check about when and whether LenaStopFill is raised.
    # if stop == 0 or data_len > stop or (data_len == stop and step != 1):
    # if stop == 0 or stop < data_len:
        try:
            for val in data:
                isl.fill_into(store, val)
        except LenaStopFill:
            assert store.group == data[start:stop:step]
        else:
            assert store.group == data[start:stop:step]
            # assert "should had raised" and False
    else:
        for val in data:
            isl.fill_into(store, val)
        assert store.group == data[start:stop:step]


def test_reverse():
    r = Reverse()
    assert list(r.run(iter([]))) == []
    assert list(r.run(iter([1]))) == [1]
    # it really works!
    assert list(r.run(iter([1, 2]))) == [2, 1]
    # just in case
    assert list(r.run(iter([1, 2, 3]))) == [3, 2, 1]
