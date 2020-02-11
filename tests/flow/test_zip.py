from __future__ import print_function

import pytest

import lena.core
from lena.core import LenaTypeError
from lena.flow import Zip
from lena.math import Sum


def test_zip_init():
    # no sequences
    with pytest.raises(LenaTypeError):
        Zip([])
    # wrong sequence
    with pytest.raises(LenaTypeError):
        Zip([1])
    # several sequence types
    # these work
    Zip([Sum()])
    # not implemented yet
    # Zip([()])
    # different types prohibited
    with pytest.raises(LenaTypeError):
        Zip([(), Sum()])


def test_zip_with_fill_compute():
    flow = [0, 1, 2]
    z0 = Zip([
        Sum(),
        (
            lambda x: x + 1,
            Sum(),
        ),
    ])
    for val in flow:
        z0.fill(val)
    assert list(z0.compute()) == [(3, 6)]
    z1 = Zip([
        Sum(),
        (
            lambda x: (x + 1, {"new_context": 1}),
            Sum(),
        ),
    ])
    # flow = [0, 1, (2, {"empty": 2})]
    # assert list(z0.compute()) == [(3, 6)]
    for val in flow:
        z1.fill(val)
    # assert list(z1.compute()) == [((3, 6), {'new_context': 1})]
    assert list(z1.compute()) == [((3, 6), {"zip": ({}, {'new_context': 1})})]

