from collections import namedtuple
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

    zn0 = Zip([
            Sum(),
            (
                lambda x: x + 1,
                Sum(),
            ),
        ],
        fields=["sum", "sum_plus_one"]
    )
    for val in flow:
        zn0.fill(val)
    zipnamed = namedtuple("zip", ["sum", "sum_plus_one"])
    assert list(zn0.compute()) == [zipnamed(3, 6)]
    zn1 = Zip([
            Sum(),
            (
                lambda x: (x + 1, {"new_context": 1}),
                Sum(),
            ),
        ],
        name="other_zip",
        fields=["sum", "sum_plus_one"]
    )
    for val in flow:
        zn1.fill(val)
    other_zip = namedtuple("other_zip", ["sum", "sum_plus_one"])
    assert list(zn1.compute()) == [
        (other_zip(sum=3, sum_plus_one=6),
        {'zip': other_zip(sum={}, sum_plus_one={'new_context': 1})})
    ]
