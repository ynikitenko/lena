import pytest

from lena.core import LenaTypeError
from lena.flow import Selector, Not, And, Or


def test_selector():
    ## wrong initialiser raises
    with pytest.raises(LenaTypeError):
        s = Selector(1)
    # wrong type inside of 'or' raises
    with pytest.raises(LenaTypeError):
        s = Selector([1])
    # wrong type inside of 'and' raises
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

    # equality works
    assert s0 == Selector(int)
    assert s0 != sand

    # representation works
    # or int.__name__ for better cross-platformity
    assert repr(s0) == "Selector(int)"
    assert repr(sand) == "Selector(And((Selector(int), Selector(str))))"
    sand1 = Selector((int, str), raise_on_error=False)
    sand2 = And((int, str), raise_on_error=False)
    assert sand2 == And((int, str), raise_on_error=False)
    assert sand != sand1
    assert repr(sand1) == "Selector(And((Selector(int, raise_on_error=False), " +\
        "Selector(str, raise_on_error=False)), raise_on_error=False), " +\
        "raise_on_error=False)"
    assert repr(sor) == "Selector(Or([Selector(int), Selector(str)]))"

    ## callable And works
    scal = Selector((int, lambda val: val < 2))
    assert list(map(scal, data)) == [True, False, False]
    # assert list(map(bool, map(scal, data))) == [True, False, False]
    # callable Or works
    scal = Selector([str, lambda val: val < 2], raise_on_error=False)
    assert [scal(val) for val in data] == [True, True, False]
    # first check lamda (which may raise), then str
    scal = Selector([lambda val: val < 2, str], raise_on_error=False)
    assert [bool(scal(val)) for val in data] == [True, True, False]

    # nested and, or work
    sccal = Selector([str, (int, lambda val: val < 2)])
    assert [sccal(dt) for dt in data] == [True, True, False]
    assert list(map(sccal, data)) == [True, True, False]

    ## string initializer works
    data = [(1, {"name": "x"}), ((2, 3), {"name": "y"})]
    dsel = Selector("name.x")
    assert [dsel(val) for val in data] == [True, False]
    assert repr(dsel) == """Selector("name.x")"""
    # equality with strings works
    assert dsel == Selector("name.x")
    assert dsel != Selector("other")

    ## And and Or with initialized selectors work.
    sel_and = Selector([Selector(len, raise_on_error=False)])
    assert [sel_and(dt[0]) for dt in data] == [False, True]
    sel_or = Selector((Selector(len, raise_on_error=False),))
    assert [sel_or(dt[0]) for dt in data] == [False, True]


def test_eq():
    sel_and = Selector([Selector(len, raise_on_error=False)])
    sel_or = Selector((Selector(len, raise_on_error=False),))
    assert sel_and == Selector([Selector(len, raise_on_error=False)])
    assert sel_and != Selector([Selector(len)])
    assert sel_and != sel_or
    assert sel_and != 0
    assert Selector(len) != Selector("len")
    assert Selector(len, raise_on_error=True) != \
        Selector(len, raise_on_error=False)

    f = lambda val: len(val)
    g = lambda val: len(val)
    sf = Selector(f)
    # same function address gives equal results
    assert sf == Selector(f)
    # different addresses give unequal results
    assert f != g
    assert sf != Selector(g)


def test_raise_on_error():
    data = [1, "s", []]
    sel1 = Selector(lambda x: len(x), raise_on_error=False)
    # no errors is raised
    assert list(map(sel1, data)) == [False, True, False]

    sel2 = Selector(lambda x: len(x), raise_on_error=True)
    assert sel2("s") == 1
    # error is raised
    with pytest.raises(TypeError):
        sel2(1)

    ## Not works
    # raise on error has no effect here
    sel3 = Not(sel2, raise_on_error=True)
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
    assert Selector(int) != ns1
    assert ns1 != int

    # representation works
    assert repr(ns1) == """Not(int)"""
    ns11 = Not(int, raise_on_error=False)
    assert repr(ns11) == """Not(int, raise_on_error=False)"""

    data = [1, "s", []]
    assert list(map(ns1, data)) == [False, True, True]

    # missing value in context.contains does not raise an exception
    ns2 = Not("context")
    assert repr(ns2) == """Not("context")"""
    assert list(map(ns2, data)) == [True, True, True]

    # pure exception
    f = lambda x: x/0.
    ns3 = Not(f)
    with pytest.raises(ZeroDivisionError):
        list(map(ns3, data))

    ns4 = Not(f, raise_on_error=False)
    assert list(map(ns4, data)) == [True, True, True]
