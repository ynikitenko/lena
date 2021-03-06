import pytest

import lena.core
from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy, GroupScale, Selector, GroupPlots
from lena.structures import Histogram, Graph


def test_group_plots():
    h0 = Histogram([0, 1], [0])
    h1 = Histogram([0, 1], [1])
    h2 = Histogram([0, 2], [2])
    g1 = Graph(((0, 1), (1, 2)))
    data = [h0, h1, h2, g1, 1]
    gp = GroupPlots(type, lambda _: True, transform=())
    # groups are yielded in arbitrary order (because they are in dict)
    results = list(gp.run(data))
    expected_results = [
        (
            [
                Histogram([0, 1], bins=[0]),
                Histogram([0, 1], bins=[1]),
                Histogram([0, 2], bins=[2])
            ],
            {'group': [{}, {}, {}]}
        ),
        (
            [1], {'group': [{}]}
        ),
        (
            [Graph(points=[(0, 1), (1, 2)], sort=True)],
            {'group': [{}]}
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
                     transform=lena.core.Sequence())
    results2 = list(gp2.run(data))
    assert_list_contents_equal(results, results2)

    data = [h1, h2]
    gp_scaled = GroupPlots(type, lambda _: True, scale=4)
    results = list(gp_scaled.run(data))
    assert results == [(
        [
            Histogram([0, 1], bins=[4.0]),
            Histogram([0, 2], bins=[2.0])
        ],
        {'group': [{}, {}]}
    )]

    ## other values are yielded fine
    gp = GroupPlots(type, Graph)
    assert list(gp.run(data)) == data

    ## yield_selected works
    gp = GroupPlots(type, lambda _: True, yield_selected=True)
    results = list(gp.run(data))
    # grouped data
    assert results[-1] == (
        [Histogram([0, 1], bins=[1]), Histogram([0, 2], bins=[2])],
        {'group': [{}, {}]}
    )
    # selected values are yielded
    assert results[:-1] == [
        Histogram([0, 1], bins=[1]),
        Histogram([0, 2], bins=[2])
    ]

    # yield_selected works with scale
    gps = GroupPlots(type, lambda _: True, scale=8, yield_selected=True)
    results = list(gps.run(data))
    # grouped histograms are rescaled
    assert results[-1] == (
        [Histogram([0, 1], bins=[8]), Histogram([0, 2], bins=[4])],
        {'group': [{}, {}]}
    )
    # scale and context of initial histograms remain the same
    assert results[:-1] == [
        Histogram([0, 1], bins=[1]),
        Histogram([0, 2], bins=[2])
    ]
