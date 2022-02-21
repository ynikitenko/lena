import itertools
import pytest

from lena.core import Sequence, Source
from lena.core import LenaTypeError, LenaValueError, LenaNotImplementedError
from lena.core import (
    Call, FillInto, FillCompute, FillRequest, SourceEl, Run
)
from lena.flow import Slice, CountFrom, Print
from lena.math import Sum
from tests.examples.fill import StoreFilled
from tests.examples.numeric import Add


def test_fill_request_run():
    from itertools import islice, count

    size = 10
    data = list(islice(count(1), size))
    bufsize = 5
    sf = StoreFilled()
    run_store = Run(sf)

    fri = FillRequest(run_store, buffer_input=True,  bufsize=bufsize)
    fro = FillRequest(run_store, buffer_output=True, bufsize=bufsize)
    results = [list(range(1, 6)), list(range(1, 11))]
    assert list(fri.run(iter(data))) == results
    sf.reset()
    ## we can't reset that, because it is a run element.
    # fri = FillRequest(run_store, buffer_input=True,  bufsize=bufsize)
    assert list(fri.run(iter(data))) == results
    # OMG, they use same sf!
    sf.reset()
    assert list(fro.run(iter(data))) == results

    sf.reset()
    fry = FillRequest(run_store, buffer_output=True, bufsize=bufsize,
                      yield_on_remainder=True)
    assert list(fry.run(iter(data))) == results


def test_fill_request():
    # todo: modify Source to use iterables (incl. those from itertools)
    # from itertools import repeat
    def ones():
        while True:
            yield 1

    ## reset works
    # reset=False works
    s0 = Source(ones, Slice(10), FillRequest(Sum(), reset=False, bufsize=1))
    assert list(s0()) == list(range(1, 11))

    # reset=True works
    s10 = Source(ones, Slice(10), FillRequest(Sum(), reset=True, bufsize=1))
    assert list(s10()) == [1 for _ in range(10)]
    # Slice can be moved after FR if bufsize=1
    s11 = Source(ones, FillRequest(Sum(), reset=True, bufsize=1), Slice(10))
    assert list(s11()) == [1 for _ in range(10)]

    # bufsize 10
    s1 = Source(CountFrom(), Slice(100),
                FillRequest(Sum(), reset=False, bufsize=10))
    results = list(s1())
    assert results == [45, 190, 435, 780, 1225, 1770, 2415, 3160, 4005, 4950]

    # bufsize 1
    s2 = Source(CountFrom(), Slice(10), FillRequest(Sum(), reset=False, bufsize=1))
    results = list(s2())
    assert results == [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]

    # derive from FillCompute
    s3 = Source(CountFrom(), Slice(10),
                FillRequest(Sum(), bufsize=1., reset=True))
    results = list(s3())
    assert results == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # run works correctly
    class MyRun():

        def fill(self, val):
            pass

        def request(self):
            pass

        def reset(self):
            pass

        def run(self, flow):
            for val in flow:
                yield True

    fr = FillRequest(MyRun(), buffer_input=True, reset=True)
    results = list(fr.run(iter([1])))
    assert results == [True]

    results = list(fr.run(iter([])))
    assert results == []

    ## run for empty flow should yield nothing
    fr = FillRequest(Sum(), reset=True)

    # nothing if yield_on_remainder is false
    assert list(fr.run([])) == []

    # nothing for yield_on_remainder=True
    # - because no remainder is not a remainder.
    fr = FillRequest(Sum(), yield_on_remainder=True, reset=True)
    assert list(fr.run([])) == []


