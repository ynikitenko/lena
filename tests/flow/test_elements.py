from collections import namedtuple

import pytest

import lena.core
from lena.flow import Count, RunIf, End, Selector, RunningChunkBy, StoreFilled


@pytest.mark.parametrize("initial_count", [0, 3])
def test_count(initial_count):
    flow = [1, 2, 3, "foo"]
    c1 = Count(name="counter", count=initial_count)

    # run works
    assert list(c1.run(iter(flow))) == [
        1, 2, 3, ('foo', {'counter': 4 + initial_count})
    ]
    assert list(c1.run(iter([]))) == []

    # fill and compute work
    c2 = Count(name="counter", count=initial_count)
    for val in flow:
        c2.fill(val)
    # didn't change, though not sure why it is needed.
    assert list(c2.compute()) == [(4+initial_count, {'counter': 4+initial_count})]

    # reset works
    c2.reset()
    assert list(c2.compute()) == [(0, {'counter': 0})]

    # fill_into works
    store = StoreFilled()
    for val in flow:
        c2.fill_into(store, val)
    results = store.group
    assert len(results) == 4
    assert results[3] == ("foo", {'counter': 4})


def test_count_eq_repr():
    # empty counter
    c0 = Count("cnt")
    assert c0.count == 0
    assert repr(c0) == """Count(name="cnt", count=0)"""

    # non-trivial value
    c1 = Count("counter", count=4)
    assert repr(c1) == """Count(name="counter", count=4)"""

    c2 = Count(name=c1.name)
    c2.count = c1.count
    assert c2 == c1

    # different names and counts make counters not equal
    assert c1 != c0
    # different types return False
    assert c1 != 0


def test_run_if():
    data = [1, 2.5]
    add_1 = lambda num: num + 1
    add_2 = lambda num: num + 2
    select_all = Selector(lambda _: True)

    # select all works
    t0 = RunIf(select_all, add_1)
    assert list(t0.run(data)) == [2, 3.5]

    # several elements work
    t0 = RunIf(select_all, add_1, add_2)
    assert list(t0.run(data)) == [4, 5.5]

    # select none works
    # ready Sequence works
    t1 = RunIf(lambda _: False, lena.core.Sequence(add_1))
    assert list(t1.run(data)) == [1, 2.5]

    # partial selector works
    t2 = RunIf(float, add_1)
    assert list(t2.run(data)) == [1, 3.5]

    ## test initialization errors
    # not a selector raises
    with pytest.raises(lena.core.LenaTypeError):
        RunIf(0, add_1)
    # not a sequence raises
    with pytest.raises(lena.core.LenaTypeError):
        RunIf(select_all, 0)


def test_running_chunk_by():
    rcb = RunningChunkBy(2)
    flow = range(5)

    ## default container (tuple) works
    assert list(rcb.run(flow)) == [(0, 1), (1, 2), (2, 3), (3, 4)]
    # not large enough flow yields no elements
    assert list(rcb.run((1,))) == []

    nt = namedtuple("xy", "x,y")
    rcb2 = RunningChunkBy(2, nt)
    res2 = list(rcb.run(flow))
    assert res2 == [(0, 1), (1, 2), (2, 3), (3, 4)]
    assert res2[0] == nt(0, 1)

    # step 1 works
    rcb3 = RunningChunkBy(1)
    assert list(rcb3.run(range(3))) == [(0,), (1,), (2,)]


def test_end():
    # run works correctly
    flow = [1, 2, 3]
    flit = iter(flow)
    res = list(End().run(flit))
    assert res == []
    assert list(flit) == []

    # equality and representation work
    e1 = End()
    e2 = End()
    assert e1 == e2
    assert e1 != []
    assert repr(e1) == "End()"
