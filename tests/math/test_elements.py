from __future__ import print_function

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
