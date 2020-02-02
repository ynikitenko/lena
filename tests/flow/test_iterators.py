from __future__ import print_function

import pytest
from itertools import count, islice

import lena.flow
from lena.core import Source, LenaStopFill
from lena.flow import DropContext, CountFrom
from lena.flow.iterators import ISlice
from tests.examples.fill import StoreFilled


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
