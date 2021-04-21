from __future__ import print_function

import pytest

from lena.math import vector3
from lena.core.exceptions import LenaTypeError


def test_eq():
    v1 = vector3([1, 2, 3])
    v2 = vector3([1, 2, 3])
    assert v1 == v2
    assert (v1 != v2) == False
    v3 = vector3([1., 2, 3])
    assert v1 == v3
    v4 = vector3([1.5, 2, 3])
    assert v1 != v4

    with pytest.raises(LenaTypeError):
        v1 == [1, 2, 3]
    with pytest.raises(TypeError):
        # LenaTypeError, to be precise
        v1 == [1, 2, 3]
    with pytest.raises(LenaTypeError):
        v1 < 0
    with pytest.raises(LenaTypeError):
        v1 <= 0
    with pytest.raises(LenaTypeError):
        v1 >= v2
    with pytest.raises(LenaTypeError):
        v1 > 0


def test_cylindrical():
    v1 = vector3([3, 4, 5])
    # rho computed
    assert v1.rho == 5
    # rho can be set (increasing)
    v1.rho = 10
    assert v1 == vector3([6, 8, 5])
    # rho can be set (decreasing)
    v1.rho = 5
    assert v1 == vector3([3, 4, 5])

    # can't change rho2 if it is 0.
    v2 = vector3([0, 0, 3])
    assert v2.rho == 0
    with pytest.raises(ZeroDivisionError):
        v2.rho = 1

    v1 = vector3([3, 4, 5])
    # rho2 computed
    assert v1.rho2 == 25
    # rho2 can be set (increasing)
    v1.rho2 = 100
    assert v1 == vector3([6, 8, 5])
    # rho2 can be set (decreasing)
    v1.rho2 = 25
    assert v1 == vector3([3, 4, 5])

    # can't change rho2 if it is 0.
    v2 = vector3([0, 0, 3])
    assert v2.rho2 == 0
    with pytest.raises(ZeroDivisionError):
        v2.rho2 = 1
