from decimal import getcontext, Decimal, Inexact
from math import frexp

import pytest
import hypothesis
from hypothesis import given
from hypothesis.strategies import integers
import hypothesis.strategies as st

import lena
from lena.core import LenaZeroDivisionError, LenaTypeError, LenaRuntimeError
from lena.flow import StoreFilled
from lena.math import vector3, Mean, Sum, DSum, VarMeanCount, Vectorize
from lena.math import var_mean_count


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


def test_var():
    var = VarMeanCount()
    var.fill(0)
    var.fill(1)
    var.fill(2)
    res = list(var.compute())
    assert len(res) == 1
    mean = 1
    mean_sq = 5/3.
    corr_fact = 3/2.  # Bessel's correction
    assert res[0] == var_mean_count(corr_fact*(mean_sq - mean**2), mean, 3)


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


@pytest.mark.parametrize("stype", [Sum, DSum])
@given(st.lists(integers()))
def test_sums_hypothesis(stype, data):
    # since Sum uses simple addition,
    # there is no need to check for floats etc.
    # Different numbers are treated uniformly in its code.
    # Need to initialize anew, otherwise same object will be used
    # between different test calls
    s = stype()
    for val in data:
        s.fill(val)
    assert list(s.compute()) == [sum(data)]


def test_vectorize_init():
    ## init works ##
    # not FillCompute sequence raises
    with pytest.raises(lena.core.LenaTypeError):
        Vectorize(lambda x: x, dim=1)

    # construct with dim work
    vi2 = Vectorize(Sum(), construct=vector3, dim=3)
    assert list(vi2.compute()) == [vector3(0, 0, 0)]
    vi2.fill(vector3(1, 2, 3))
    assert list(vi2.compute()) == [vector3(1, 2, 3)]

    vi3 = Vectorize(Sum(), construct=int, dim=1)
    assert list(vi3.compute()) == [0]

    data = [vector3(1, 1, 1), vector3(1, 2, 3)]

    v1 = Vectorize(Sum(), dim=3)
    # todo: use inspect.isclass to forbid this:
    # v1 = Vectorize(Sum)
    for val in data:
        v1.fill(val)
    assert list(v1.compute()) == [(2, 3, 4)]
    context = {"context": True}
    v1.fill((vector3(0, 0, 0), context))
    assert list(v1.compute()) == [((2, 3, 4), context)]


@given(
    st.lists(
        st.tuples(integers(), integers(), integers()),
        min_size=1,
    )
)
def test_vectorize_hypothesis(data):
    # Vectorize doesn't mess with its input data.
    # If we filled values, they will be properly handled
    # by the nested sequence.
    v = Vectorize(StoreFilled(), dim=3)

    for val in data:
        v.fill(val)
    result = list(v.compute())
    assert len(result) == 1
    # 3-tuple of lists
    res = result[0]
    for ind, tup in enumerate(data):
        for dim in range(3):
            assert res[dim][ind] == tup[dim]
