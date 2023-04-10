import pytest

import lena.core
from lena.flow import Count, RunIf, End, Selector
from tests.examples.fill import StoreFilled


def test_count():
    # test run
    flow = [1, 2, 3, "foo"]
    c = Count(name="counter")
    assert list(c.run(iter(flow))) == [
        1, 2, 3, ('foo', {'counter': 4})
    ]
    assert list(c.run(iter([]))) == []

    # test FillCompute
    c = Count(name="counter")
    for val in flow:
        c.fill(val)
    result = [(4, {'type': 'count', 'name': 'counter'})]
    # # don't change during request
    # assert list(c.request()) == result
    # assert list(c.request()) == result
    # assert list(c.compute()) == [(4, {'type': 'count', 'name': 'counter'})]
    assert list(c.compute()) == [(4, {'counter': 4})]
    # reset after compute
    assert list(c.compute()) == [(0, {'counter': 0})]
    # context is updated correctly
    # c.fill(("foo", {"bar": "baz"}))
    # assert list(c.request()) == [
    #     (1, {'type': 'count', 'bar': 'baz', 'name': 'counter'})
    # ]

    ## test fill_into
    store = StoreFilled()
    for val in flow:
        c.fill_into(store, val)
    results = store.list
    assert len(results) == 4
    assert results[3] == ("foo", {'counter': 4})


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
