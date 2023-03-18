import copy
import pytest

import lena.core
from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy, GroupScale, Selector, MapGroup
from lena.flow.group_plots import group_plots, GroupPlots
from lena.structures import histogram, graph


def test_map_group():
    el = lambda i: i+1

    # map scalars works
    mgt = MapGroup(el, map_scalars=True)
    assert list(mgt.run([1])) == [2]
    # don't map scalars works
    mgf = MapGroup(el, map_scalars=False)
    assert list(mgf.run([1])) == [1]

    # for now need to make lambdas use context.
    mg1 = MapGroup(lambda val: (val[0]+1, val[1]))
    grp1 = ([1, 3], {"group": [{}, {}]})
    # empty context unchanged
    assert list(mg1.run([grp1])) == [([2, 4], grp1[1])]

    # intersection actually updates the resulting context
    grp2 = ([1, 3], {"group": [{"a": 1}, {"a": 1}]})
    # but only if that was not present before the map!
    assert list(mg1.run([grp2])) == [([2, 4], grp2[1])]
                                      # {"a": 1, "group": grp2[1]["group"]})]

    # new common transform updates context.
    mg2 = MapGroup(lambda val: (val[0]+1, {"b": 2}))
    assert list(mg2.run([grp2])) == [([2, 4],
                                      {"b": 2, "group": grp2[1]["group"]})]

    # explicit changes work
    # if we change to [True, False], it fails!
    # Probably because of grp1 mutation.
    for changed in [False, True]:
        uc = lambda val: (val[0]+1, {"output": {"changed": changed}})
        mg3 = MapGroup(uc)
        assert list(mg3.run([grp1])) == [
            ([2, 4],
             {"output": {"changed": changed}, "group": grp1[1]["group"]})
        ]

    # wrong value raises
    with pytest.raises(lena.core.LenaRuntimeError):
        # empty context group
        list(mg2.run([([1], {"group": []})]))

    ## test initialization
    # Several elements work
    mg4 = MapGroup(el, el, map_scalars=True)
    assert list(mg4.run([1])) == [3]

    # same without explicit map_scalars
    mg4 = MapGroup(el, el)
    assert list(mg4.run([1])) == [3]

    # map_scalars must be explicit
    with pytest.raises(lena.core.LenaTypeError):
        MapGroup(el, True)

    # wrong keyword arguments raise
    with pytest.raises(lena.core.LenaTypeError):
        MapGroup(el, wrong_kwarg=True)

    # unconvertible element raises
    with pytest.raises(lena.core.LenaTypeError):
        MapGroup(1)

    ## different number of resulting values raises
    class RunN():

        def run(self, flow):
            for val in flow:
                data, context = lena.flow.get_data_context(val)
                while data:
                    if context:
                        yield (data, context)
                    else:
                        yield data
                    data -= 1

    mg4 = MapGroup(RunN(), map_scalars=True)
    # for scalars it works
    assert list(mg4.run([1, 2])) == [1, 2, 1]
    # for a group of one it works
    grpc = {"group": [{}]}
    assert list(mg4.run([([2], grpc)])) == [([2], grpc), ([1], grpc)]
    # for a group of several it raises
    with pytest.raises(lena.core.LenaRuntimeError):
        assert list(mg4.run([([1, 2], {"group": [{}, {}]})]))


def test_group_plots():
    data = [1, 2]
    contexts = ({"a": "a", "b": {}}, {"a": "a"})
    vals = list(zip(data, contexts))
    res = (
        [1, 2],
        {'a': 'a',
         'group': [{'a': 'a',
                    'b': {}},
                   {'a': 'a'}],
         'output': {'changed': False}},
    )
    assert group_plots(vals) == res

    vals = data
    assert group_plots(vals) == (
        [1, 2],
        # there is a group context, even if it was empty.
        # It is better for generality.
        {'group': [{}, {}], 'output': {'changed': False}}
    )


def test_GroupPlots():
    h0 = histogram([0, 1], [0])
    h1 = histogram([0, 1], [1])
    h2 = histogram([0, 2], [2])
    gr1 = graph([[0, 1], [1, 2]])
    # copy not to modify original histograms
    data = copy.deepcopy([h0, h1, h2, gr1, 1])

    # in Python 2 type of histogram and graph is the same
    def tp(data):
        if isinstance(data, histogram):
            return "hist"
        if isinstance(data, graph):
            return "graph"
        return type(data)

    gp = GroupPlots(tp, lambda _: True, transform=(), yield_selected=False)
    # groups are yielded in arbitrary order (because they are in a dict)
    results = list(gp.run(data))
    print(results)
    expected_results = [
        (
            [
                histogram([0, 1], bins=[0]),
                histogram([0, 1], bins=[1]),
                histogram([0, 2], bins=[2])
            ],
            {'group': [{}, {}, {}], 'output': {'changed': False}}
        ),
        (
            [1], {'group': [{}], 'output': {'changed': False}}
        ),
        (
            [gr1], {'group': [{}], 'output': {'changed': False}}
        ),
    ]
    def assert_list_contents_equal(results, expected_results):
        assert len(results) == len(expected_results)
        for res in results:
            assert res in expected_results
        # and no duplicate results in results
        for res in expected_results:
            assert res in results
    assert_list_contents_equal(results, expected_results)
    # set can't be used, TypeError: unhashable type: 'list'
    # moreover, if there are duplicates, we won't check that with set.
    # assert set(results) == set(expected_results)

    gp2 = GroupPlots(GroupBy(tp), Selector(lambda _: True),
                     transform=lena.core.Sequence(), yield_selected=False)
    results2 = list(gp2.run(data))
    assert_list_contents_equal(results, results2)

    data1 = copy.deepcopy([h1, h2])
    gp_scaled = GroupPlots(tp, lambda _: True, scale=4, yield_selected=False)
    results = list(gp_scaled.run(data1))

    context_unchanged = {'group': [{}, {}], 'output': {'changed': False}}
    assert results == [(
        [
            histogram([0, 1], bins=[4.0]),
            histogram([0, 2], bins=[2.0])
        ],
        context_unchanged
    )]

    ## other values are yielded fine
    gp = GroupPlots(tp, graph)
    assert list(gp.run(data1)) == data1

    ## yield_selected works
    data2 = copy.deepcopy([h1, h2])
    # selector is None (all is selected)
    gp = GroupPlots(tp, yield_selected=True)
    results = list(gp.run(data2))
    # grouped data
    assert results[-1] == (
        [histogram([0, 1], bins=[1]), histogram([0, 2], bins=[2])],
        context_unchanged
    )
    # selected values are yielded
    assert results[:-1] == [
        histogram([0, 1], bins=[1]),
        histogram([0, 2], bins=[2])
    ]

    # yield_selected works with scale
    data3 = copy.deepcopy([h1, h2])
    gps = GroupPlots(tp, lambda _: True, scale=8, yield_selected=True)
    results = list(gps.run(data3))
    # grouped histograms are rescaled
    assert results[-1] == (
        [histogram([0, 1], bins=[8]), histogram([0, 2], bins=[4])],
        context_unchanged
    )
    # scale and context of initial histograms remain the same
    assert results[:-1] == [
        histogram([0, 1], bins=[1]),
        histogram([0, 2], bins=[2])
    ]

    # test that changed values create changed context
    data_c = [(0, {"output": {"changed": False}}),
              (1, {"output": {"changed": True}})]
    group_plots = GroupPlots(tp, lambda _: True, yield_selected=False)
    assert list(group_plots.run(data_c))[0] == (
        [0, 1],
        {'group': [{'output': {'changed': False}}, {'output': {'changed': True}}],
         'output': {'changed': True}}
    )
