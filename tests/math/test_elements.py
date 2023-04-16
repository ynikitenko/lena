import pytest

from lena.core import LenaZeroDivisionError
from lena.math import Mean, Sum


def test_mean():
    m0 = Mean()
    with pytest.raises(LenaZeroDivisionError):
        list(m0.compute())
    m1 = Mean(pass_on_empty=True)
    assert list(m1.compute()) == []
    # fill with context
    empty_context = {"context": "empty"}
    m1.fill((1, empty_context))
    assert list(m1.compute()) == [(1, empty_context)]
    # math is correct
    m1.fill(3)
    assert list(m1.compute()) == [2]


from decimal import getcontext, Decimal, Inexact
from math import frexp
getcontext().traps[Inexact] = True

def dsum(iterable):
    "Full precision summation using Decimal objects for intermediate values"
    # Transform (exactly) a float to m * 2 ** e where m and e are integers.
    # Convert (mant, exp) to a Decimal and add to the cumulative sum.
    # If the precision is too small for exact conversion and addition,
    # then retry with a larger precision.

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
    s0 = Sum()
    assert list(s0.compute()) == [0]
    # fill with context
    empty_context = {"context": "empty"}
    s0.fill((1, empty_context))
    assert list(s0.compute()) == [(1, empty_context)]
    # math is correct
    s0.fill(3)
    assert list(s0.compute()) == [4]
