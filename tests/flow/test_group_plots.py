import pytest

import lena.core
from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy, GroupScale, Selector, GroupPlots
from lena.structures import histogram, Graph


def test_group_plots():
    h0 = histogram([0, 1], [0])
    h1 = histogram([0, 1], [1])
    h2 = histogram([0, 2], [2])
    g1 = Graph(((0, 1), (1, 2)))
    data = [h0, h1, h2, g1, 1]
    gp = GroupPlots(type, lambda _: True, transform=(), yield_selected=False)
    # groups are yielded in arbitrary order (because they are in a dict)
    results = list(gp.run(data))
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
            [Graph(points=[(0, 1), (1, 2)], sort=True)],
            {'group': [{}], 'output': {'changed': False}}
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

    gp2 = GroupPlots(GroupBy(type), Selector(lambda _: True),
                     transform=lena.core.Sequence(), yield_selected=False)
    results2 = list(gp2.run(data))
    assert_list_contents_equal(results, results2)

    data = [h1, h2]
    gp_scaled = GroupPlots(type, lambda _: True, scale=4, yield_selected=False)
    results = list(gp_scaled.run(data))

    context_unchanged = {'group': [{}, {}], 'output': {'changed': False}}
    assert results == [(
        [
            histogram([0, 1], bins=[4.0]),
            histogram([0, 2], bins=[2.0])
        ],
        context_unchanged
    )]

    ## other values are yielded fine
    gp = GroupPlots(type, Graph)
    assert list(gp.run(data)) == data

    ## yield_selected works
    gp = GroupPlots(type, lambda _: True, yield_selected=True)
    results = list(gp.run(data))
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
    gps = GroupPlots(type, lambda _: True, scale=8, yield_selected=True)
    results = list(gps.run(data))
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
    group_plots = GroupPlots(type, lambda _: True, yield_selected=False)
    assert list(group_plots.run(data_c))[0] == (
        [0, 1],
        {'group': [{'output': {'changed': False}}, {'output': {'changed': True}}],
         'output': {'changed': True}}
    )
