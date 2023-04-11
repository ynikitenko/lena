import pytest

from lena.core import LenaTypeError
from lena.flow import Selector, Not


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

    ## Class works ##
    s0 = Selector(int)
    assert list(map(bool, map(s0, data))) == [True, False, False]
    # *And* works
    sand = Selector((int, str))
    assert list(map(bool, map(sand, data))) == [False, False, False]
    # *Or* works
    sor = Selector([int, str])
    assert list(map(bool, map(sor, data))) == [True, True, False]

    # equality tests work
    assert s0 == Selector(int)
    assert s0 != sand
    # representation works
    # or int.__name__ for better cross-platformity
    assert repr(s0) == "Selector(int)"
    assert repr(sand) == "Selector((Selector(int), Selector(str)))"
    assert repr(sor) == "Selector([Selector(int), Selector(str)])"

    ## callable And works
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

    ## string initializer works
    data = [(1, {"name": "x"}), (2, {"name": "y"})]
    dsel = Selector("name.x")
    assert [dsel(val) for val in data] == [True, False]
    assert repr(dsel) == """Selector("name.x")"""
    assert dsel == Selector("name.x")
    assert dsel != Selector("other")

    ## And and Or with initialized selectors work.
    sel_and = Selector([Selector(len)])
    assert [sel_and(dt[0]) for dt in data] == [False]*2
    sel_or = Selector((Selector(len),))
    assert [sel_or(dt[0]) for dt in data] == [False]*2

    # eq works
    assert sel_and == Selector([Selector(len)])
    assert sel_and != sel_or
    assert sel_and != 0


def test_raise_on_error():
    data = [1, "s", []]
    sel1 = Selector(lambda x: len(x))
    # no errors is raised
    assert list(map(sel1, data)) == [False, True, False]

    sel2 = Selector(lambda x: len(x), raise_on_error=True)
    assert sel2("s") == 1
    # error is raised
    with pytest.raises(TypeError):
        sel2(1)

    ## Not works
    # raise on error has no effect here
    sel3 = Not(sel2, raise_on_error=False)
    with pytest.raises(TypeError):
        sel3(1)
    # raise on error has no effect here
    sel4 = Not(sel1, raise_on_error=True)
    assert sel4(1) == True

    # raise on error works
    sel5 = Not(lambda x: len(x), raise_on_error=True)
    assert sel5("s") == False
    with pytest.raises(TypeError):
        sel5(1)

    ## And and Or raise properly.
    # Or works
    sel_or = Selector([len], raise_on_error=True)
    with pytest.raises(TypeError):
        sel_or(1)
    # And works
    sel_and = Selector((len,), raise_on_error=True)
    with pytest.raises(TypeError):
        sel_and(1)


def test_not():
    # simple type
    ns1 = Not(int)
    # equality works
    assert ns1 == Not(int)
    assert ns1 != Selector(int)
    assert ns1 != int

    # representation works
    assert repr(ns1) == """Not(int)"""

    data = [1, "s", []]
    assert list(map(ns1, data)) == [False, True, True]

    # missing value, raises an exception
    ns2 = Not("context")
    assert repr(ns2) == """Not("context")"""
    assert list(map(ns2, data)) == [True, True, True]

    # pure exception
    f = lambda x: x/0.
    ns3 = Not(f)
    assert list(map(ns3, data)) == [True, True, True]
