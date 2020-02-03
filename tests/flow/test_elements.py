from lena.flow import Count, TransformIf, End
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


def test_transform_if():
    data = [1, 2.5]
    # t0-t3 check work for empty types, int, lambda and a list.
    t0 = TransformIf(lambda _: True, lambda num: num + 1)
    assert list(t0.run(data)) == [2, 3.5]
    t1 = TransformIf(int, lambda num: num + 1)
    assert list(t1.run(data)) == [2, 2.5]
    t2 = TransformIf(float, lambda num: num + 1)
    assert list(t2.run(data)) == [1, 3.5]
    t3 = TransformIf([lambda val: isinstance(val, float), int], lambda num: num + 1)
    assert list(t3.run(data)) == [2, 3.5]


def test_end():
    flow = [1, 2, 3]
    flit = iter(flow)
    res = list(End().run(flit))
    assert res == []
    assert list(flit) == []
