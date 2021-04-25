from __future__ import print_function

import pytest
from itertools import count, islice

import lena.flow
from lena.core import Source, LenaStopFill
from lena.flow import DropContext, CountFrom
from lena.flow.iterators import ISlice
from tests.examples.fill import StoreFilled

from hypothesis import strategies as s
from hypothesis import given
# don't think anything would change with other numbers
hypo_int_max = 200


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
    s = Source(CountFrom(),
         # lambda i: (i, {str(i): i}),
         # DropContext(
         #     ISlice(5),
         #     lambda i: i + 1,
         # ),
         ISlice(10),
    )
    results = s()
    assert [result for result in s()] == list(range(10))
    # [
    #     (1, {'0': 0}), (2, {'1': 1}), (3, {'2': 2}), (4, {'3': 3}), (5, {'4': 4})
    # ]

    # test start
    it = CountFrom(start=10)
    assert list(islice(it(), 5)) == list(range(10, 15))
    # test step
    it = CountFrom(step=2)
    assert list(islice(it(), 5)) == list(range(0, 10, 2))
    # test start and step 
    it = CountFrom(start=10, step=2)
    assert list(islice(it(), 5)) == list(range(10, 20, 2))


def test_islice():
    c = count()
    ### test __init__ and run ###
    # stop works
    isl = ISlice(10)
    list(isl.run(c)) == list(range(0, 10))
    # start, stop works
    isl = ISlice(10, 10)
    list(isl.run(c)) == []
    c = count()
    isl = ISlice(10, 15)
    list(isl.run(c)) == list(range(10, 15))
    # start, stop, step work
    isl = ISlice(0, 10, 2)
    list(isl.run(count())) == list(range(0, 10, 2))

    ### test fill ###
    store = StoreFilled()
    # start, stop work
    isl = ISlice(10, 15)
    for i in range(0, 15):
        isl.fill_into(store, i)
    assert store.list == list(range(10, 15))
    with pytest.raises(LenaStopFill):
        isl = ISlice(10, 15)
        for i in range(0, 16):
            isl.fill_into(store, i)
    # step works
    store.reset()
    isl = ISlice(10, 20, 2)
    # 18 will be filled last
    for i in range(0, 19):
        isl.fill_into(store, i)
    assert store.list == list(range(10, 20, 2))


def test_negative_islice():
    # negative stop
    isl1 = ISlice(-1)
    data = [0, 1, 2]
    assert list(isl1.run(iter(data))) == [0, 1]

    # positive start, negative stop
    isl2 = ISlice(1, -1)
    assert list(isl2.run(iter(data))) == [1]

    # negative start, negative stop
    isl3 = ISlice(-2, -1)
    assert list(isl3.run(iter(data))) == [1]

    # negative start, positive stop
    isl4 = ISlice(-2, 2)
    assert list(isl4.run(iter(data))) == [1]

    ## step works
    s = slice(None, None, 2)
    isl5 = ISlice(s.start, s.stop, s.step)
    assert list(isl5.run(iter(range(0, 6)))) == list(range(0, 6))[s.start:s.stop:s.step]

    # step with negative index works
    s = slice(-3, 3, 2)
    isl6 = ISlice(s.start, s.stop, s.step)
    assert list(isl6.run(iter(range(0, 6)))) == list(range(0, 6))[s.start:s.stop:s.step]

    # initialization works correctly (seems not always)
    isl7 = ISlice(-3, 5, None)
    assert (isl7._start, isl7._stop, isl7._step) == (-3, 5, 1)

    for s in [slice(-3, 3, 2), slice(-3, 4, 3), slice(-3, 5),
              # negative very large start should have no effect,
              # like getting all elements.
              slice(-100, 3)]:
        isl = ISlice(s.start, s.stop, s.step)
        for data in [range(0), range(4), range(10), range(20)]:
            assert list(isl.run(iter(data))) == list(data)[s.start:s.stop:s.step]

    # to check it myself.
    isl8 = ISlice(-100, 3)
    assert list(isl8.run(iter(range(5)))) == list(range(3))

    # step must be a natural number
    # negative step raises
    with pytest.raises(lena.core.LenaValueError):
        ISlice(None, None, -1)
    # zero step raises
    with pytest.raises(lena.core.LenaValueError):
        ISlice(None, None, 0)


start_stop_s = s.one_of(s.none(), s.integers(-hypo_int_max, hypo_int_max))
step_s = s.integers(1, hypo_int_max)

@given(start=start_stop_s, stop=start_stop_s, step=step_s,
       data_len=s.integers(0, hypo_int_max))
def test_islice_hypothesis(start, stop, step, data_len):
    data = list(range(data_len))
    isl = ISlice(start, stop, step)
    assert list(isl.run(iter(data))) == data[start:stop:step]
