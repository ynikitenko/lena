import pytest

import lena.core
from lena.math import vector3
from lena.core.exceptions import LenaTypeError


def test_eq():
    v1 = vector3(1, 2, 3)
    v2 = vector3(1, 2, 3)
    assert v1 == v2
    assert (v1 != v2) == False
    v3 = vector3(1., 2, 3)
    assert v1 == v3
    v4 = vector3(1.5, 2, 3)
    assert v1 != v4

    assert (v1 == [1, 2, 3]) is False
    with pytest.raises(LenaTypeError):
        v1 < 0
    with pytest.raises(LenaTypeError):
        v1 <= 0
    with pytest.raises(LenaTypeError):
        v1 >= v2
    with pytest.raises(LenaTypeError):
        v1 > 0


def test_operations():
    v1 = vector3(3, 4, 5)
    v1 *= 2
    assert v1 == vector3(6, 8, 10)
    v1 /= 2
    assert v1 == vector3(3, 4, 5)

    # after division vector representation will be with floats
    assert str(v1) == "vector3(3.0, 4.0, 5.0)"

    # test all assignments / getters
    v2 = vector3(0, 0, 0)
    v2.x = 1
    v2.y = 2
    v2.z = 3
    assert v2 == vector3(1, 2, 3)

    # r2 getter works
    assert v2.getr2() == 14

    # != works
    assert v1 != v2
    # != for different types is True
    assert (v1 != 0) is True

    # comparison with a wrong type raises
    with pytest.raises(lena.core.LenaTypeError):
        v1 < 0

    # iter works
    assert list(coord for coord in v2) == [1, 2, 3]

    # container length is 3
    assert len(v1) == 3

    # we also have this method!
    v2[2] = 4
    assert v2 == vector3(1, 2, 4)

    # we can add a list to vector3! From the right side.
    assert [1.1, 2.2, 3.3] + v2 == vector3(2.1, 4.2, 7.3)

    # non-zero works
    assert bool(v2)


def test_cylindrical():
    v1 = vector3(3, 4, 5)
    # rho computed
    assert v1.rho == 5
    # rho can be set (increasing)
    v1.rho = 10
    assert v1 == vector3(6, 8, 5)
    # rho can be set (decreasing)
    v1.rho = 5
    assert v1 == vector3(3, 4, 5)

    # can't change rho2 if it is 0.
    v2 = vector3(0, 0, 3)
    assert v2.rho == 0
    with pytest.raises(ZeroDivisionError):
        v2.rho = 1

    v1 = vector3(3, 4, 5)
    # rho2 computed
    assert v1.rho2 == 25
    # rho2 can be set (increasing)
    v1.rho2 = 100
    assert v1 == vector3(6, 8, 5)
    # rho2 can be set (decreasing)
    v1.rho2 = 25
    assert v1 == vector3(3, 4, 5)

    # can't change rho2 if it is 0.
    v2 = vector3(0, 0, 3)
    assert v2.rho2 == 0
    with pytest.raises(ZeroDivisionError):
        v2.rho2 = 1
