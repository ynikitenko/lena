import pytest

from decimal import getcontext, Decimal, Inexact
from math import frexp

from lena.core import LenaZeroDivisionError
from lena.math import vector3, Mean, Sum, DSum, Vectorize


def test_mean():
    # no filled entries raise
    m0 = Mean()
    with pytest.raises(LenaZeroDivisionError):
        list(m0.compute())

    # pass_on_empty works
    m1 = Mean(pass_on_empty=True)
    assert list(m1.compute()) == []

    # fill with context
    empty_context = {"context": "empty"}
    m1.fill((1, empty_context))
    assert list(m1.compute()) == [(1, empty_context)]
    # math is correct
    m1.fill(3)
    assert list(m1.compute()) == [2]

    # special sums work
    m2 = Mean(DSum())
    m2.fill(1)
    m2.fill(2)
    assert list(m2.compute()) == [1.5]

    m2.reset()
    with pytest.raises(LenaZeroDivisionError):
        assert list(m2.compute()) == [1.5]

    class SumWOReset():
        pass

    m3 = Mean(SumWOReset())
    # no reset in the sum element leads to no reset in Mean
    with pytest.raises(AttributeError):
        m3.reset()

    # sum_element is actually reset
    ds = DSum(3)
    assert ds.total == 3.
    m4 = Mean(ds)
    m4.reset()
    assert ds.total == 0.


def dsum(iterable):
    "Full precision summation using Decimal objects for intermediate values"
    # Transform (exactly) a float to m * 2 ** e where m and e are integers.
    # Convert (mant, exp) to a Decimal and add to the cumulative sum.
    # If the precision is too small for exact conversion and addition,
    # then retry with a larger precision.
    getcontext().traps[Inexact] = True

    total = Decimal(0)
    for x in iterable:
        mant, exp = frexp(x)
        mant, exp = int(mant * 2.0 ** 53), exp-53
        while True:
            try:
                # total += mant * Decimal(2) ** exp
                total = Decimal(x)
                break
            except Inexact:
                getcontext().prec += 1
    return float(total)


def _test_dsum():
    assert dsum([1,2]) == 3.
    from math import fsum
    from random import random, gauss, shuffle
    vals = [7, 1e100, -7, -1e100, -9e-20, 8e-20] * 10
    s = 0
    for i in range(200):
        v = gauss(0, random()) ** 7 - s
        s += v
        vals.append(v)
    shuffle(vals)
    assert dsum(vals) == fsum(vals)


def test_sum():
    # empty Sum is zero
    s0 = Sum()
    assert list(s0.compute()) == [0]

    # fill with context works
    empty_context = {"context": "empty"}
    s0.fill((1, empty_context))
    assert list(s0.compute()) == [(1, empty_context)]

    # math is correct
    s0.fill(3)
    assert list(s0.compute()) == [4]
    # total property works
    assert s0.total == 4

    # reset works
    s0.reset()
    assert s0.total == 0

    # empty context is not yielded
    # todo: maybe we would need to store the context for reset...
    assert list(s0.compute()) == [0]

    # starting value is counted
    s1 = Sum(1)
    s1.fill(2)
    assert s1.total == 3


def test_vectorize():
    data = [vector3(1, 1, 1), vector3(1, 2, 3)]

    v1 = Vectorize(Sum())
    # todo: use inspect.isclass to forbid this:
    # v1 = Vectorize(Sum)
    for val in data:
        v1.fill(val)
    assert list(v1.compute()) == [vector3(2, 3, 4)]
    context = {"context": True}
    v1.fill((vector3(0, 0, 0), context))
    assert list(v1.compute()) == [(vector3(2, 3, 4), context)]
