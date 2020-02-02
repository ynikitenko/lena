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

