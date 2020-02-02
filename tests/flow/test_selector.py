import pytest

from lena.core import LenaTypeError
from lena.flow import Selector


def test_selector():
    ## wrong selector raises
    with pytest.raises(LenaTypeError):
        s = Selector(1)
    # wrong type inside 'or'
    with pytest.raises(LenaTypeError):
        s = Selector([1])
    # wrong type inside 'and'
    with pytest.raises(LenaTypeError):
        s = Selector((1,))

    data = [1, "s", []]
    # class works
    s0 = Selector(int)
    assert list(map(bool, map(s0, data))) == [True, False, False]
    # *And* works
    sand = Selector((int, str))
    assert list(map(bool, map(sand, data))) == [False, False, False]
    # *Or* works
    sor = Selector([int, str])
    assert list(map(bool, map(sor, data))) == [True, True, False]
    # callable And works
    scal = Selector((int, lambda val: val < 2))
    assert list(map(bool, map(scal, data))) == [True, False, False]
    # callable Or works
    scal = Selector([str, lambda val: val < 2])
    assert [bool(scal(val)) for val in data] == [True, True, False]
    # first check lamda (which may raise), then str
    scal = Selector([lambda val: val < 2, str])
    assert [bool(scal(val)) for val in data] == [True, True, False]
    # nested and, or works
    sccal = Selector([str, (int, lambda val: val < 2)])
    assert list(map(bool, [sccal(dt) for dt in data])) == [True, True, False]
    assert list(map(bool, map(sccal, data))) == [True, True, False]

    # string initializer works
    data = [(1, {"name": "x"}), (2, {"name": "y"})]
    dsel = Selector("name.x")
    assert [dsel(val) for val in data] == [True, False]
