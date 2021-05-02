from __future__ import print_function

import pytest
from itertools import islice

from lena.core import Sequence, Source
from lena.core import LenaTypeError, LenaValueError, LenaNotImplementedError
from lena.core import (
    Call, FillInto, FillCompute, FillRequest, SourceEl, Run
)
from lena.flow import Slice, CountFrom
from lena.math import Sum
from tests.examples.fill import StoreFilled
from tests.examples.numeric import Add


# class Sum():
#     """Sum elements which *fill* this.
#     """
#     def __init__(self):
#         self.sum = 0
# 
#     def fill(self, val):
#         self.sum += val
# 
#     def reset(self):
#         self.sum = 0
# 
#     def compute(self):
#         yield self.sum


class StrangeCallable():
    def strange_call(self, val):
        return val


class StrangeSource():
    def strange_call(self):
        for i in [1, 2, 3, 4, 5]:
            yield i


class StrangeFillInto():
    def strange_fill_into(self, el, val):
        el.fill(val)


def my_run(flow):
    for val in flow:
        yield val


class MyRunEl():
    def run(self, flow):
        for val in flow:
            yield val
    def other_run(self, flow):
        for val in flow:
            yield val + 1


class MyFillCompute(FillCompute):
    def __init__(self):
        pass


def test_call():
    sc = StrangeCallable()
    s = Call(sc, call='strange_call')
    assert s(1) == 1
    c = Call(lambda x: x+1)
    assert c(1) == 2
    with pytest.raises(LenaTypeError):
        s = Call(sc, call='other')
    with pytest.raises(LenaTypeError):
        s = Call("not a callable")


def test_source_el():
    ss = StrangeSource()
    s = SourceEl(ss, call='strange_call')
    assert list(s()) == list(ss.strange_call())


def test_fill_compute():
    s = Sum()
    fc = FillCompute(s)
    assert list(fc.compute()) == [0]
    s.fill(1)
    assert list(fc.compute()) == [1]
    # reset is called
    s.reset()
    assert list(fc.compute()) == [0]

    # wrong compute method
    with pytest.raises(LenaTypeError):
        fc = FillCompute(s, compute="wrong")
    class MyFill():
        def fill():
            pass
    with pytest.raises(LenaTypeError):
        FillCompute(MyFill())
    with pytest.raises(LenaTypeError):
        FillCompute(s, fill="wrong")
    with pytest.raises(LenaNotImplementedError):
        MyFillCompute().fill(1)
    with pytest.raises(LenaNotImplementedError):
        MyFillCompute().compute()


def test_fill_into():
    store = StoreFilled()
    ## test initialization
    # with a class with a strangely named fill_into method 
    fi = FillInto(StrangeFillInto(), fill_into='strange_fill_into')
    fi.fill_into(store, 1)
    assert store == [1]
    # with a callable class
    fi = FillInto(Add(0))
    fi.fill_into(store, 1)
    assert store == [1, 1]
    # with a lambda
    fi = FillInto(lambda val: val + 3)
    fi.fill_into(store, 1)
    assert store == [1, 1, 4]


def test_fill_request():
    # no fill method raises
    with pytest.raises(LenaTypeError):
        FillRequest(lambda _: 0)

    # bufsize 10
    s1 = Source(CountFrom(), Slice(100), FillRequest(Sum(), reset=False, bufsize=10))
    results = list(s1())
    assert results == [45, 190, 435, 780, 1225, 1770, 2415, 3160, 4005, 4950]

    # bufsize 1
    s2 = Source(CountFrom(), Slice(10), FillRequest(Sum(), reset=False, bufsize=1))
    results = list(s2())
    assert results == [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]

    # derive from FillCompute
    s3 = Source(CountFrom(), Slice(10), FillRequest(Sum(), bufsize=1.))
    results = list(s3())
    assert results == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    sum = Sum()
    sum.reset = None
    with pytest.raises(LenaTypeError):
        FillRequest(sum)
    with pytest.raises(LenaValueError):
        FillRequest(Sum(), bufsize=0)
    class MyFillRequest(FillRequest):
        # otherwise base __init__ will be called
        def __init__(self):
            pass
    with pytest.raises(LenaNotImplementedError):
        MyFillRequest().fill(1)
    # with pytest.raises(LenaNotImplementedError):
    #     MyFillRequest().request()

    # test if run is initialized correctly
    class MyRun():
        def fill(self, val):
            pass

        def request(self):
            pass

        def reset(self):
            pass

        def run(self, flow):
            return self.my_run(flow)

        def my_run(self, flow):
            yield True

    fr = FillRequest(MyRun())
    results = list(fr.run([]))
    assert results == [True]
    # run empty flow should yield something.
    fr = FillRequest(Sum())
    assert list(fr.run([])) == [0]


def test_run():
    # Run without element
    simple_run = Run(None, my_run)
    data = [1, 2, 3]
    assert list(simple_run.run(data)) == data
    # Run with a Call
    call_run = Run(lambda x: x+1)
    assert list(call_run.run(data)) == [2, 3, 4]
    # Run with FillCompute
    sum_run = Run(Sum())
    assert list(sum_run.run(data)) == [6]
    # Run with element with run method
    facade_run = Run(MyRunEl())
    assert list(facade_run.run(data)) == data
    other_run = Run(MyRunEl(), run="other_run")
    assert list(other_run.run(data)) == [2, 3, 4]
    # wrong initialization fails
    with pytest.raises(LenaTypeError):
        facade_run = Run(MyRunEl(), run="other")
    with pytest.raises(LenaTypeError):
        Run(StrangeCallable())
