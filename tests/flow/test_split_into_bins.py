from __future__ import print_function

import pytest
import copy

import lena.core
import lena.flow.split_into_bins as sib
from lena.core import Split, FillCompute, Sequence
from lena.variables import Variable
from lena.structures import Histogram
from lena.flow import SplitIntoBins, TransformBins, ReduceBinContent
from lena.flow.split_into_bins import _iter_bins_with_edges

from tests.examples.fill_compute import Count, Sum


def test__iter_bins_with_edges():
    bins = [0]
    edges = [0, 1]
    assert list(_iter_bins_with_edges(bins, edges)) == [(0, ((0, 1),))]
    assert list(_iter_bins_with_edges([0, 1], [0, 1, 2])) ==  [(0, ((0, 1),)), (1, ((1, 2),))]
    # assert list(_iter_bins_with_edges(bins, edges)) == [(0, ([0], [1]))]
    # assert list(_iter_bins_with_edges([0, 1], [0, 1, 2])) == [(0, ([0], [1])), (1, ([1], [2]))]
    edges = [[0, 1], [0, 1]]
    bins = [[1]]
    # this (bins, edges) pair is legitimate
    h = Histogram(edges, bins)
    assert list(_iter_bins_with_edges(bins, edges)) == [(1, ((0, 1), (0, 1)))]


def test__md_seq_map():
    _MdSeqMap = sib._MdSeqMap
    arr = [Count(), Count()]
    arr[1].fill(1)
    seq_map = _MdSeqMap(lambda cell: cell.compute(), arr)
    assert list(seq_map) == [[0, 1]]
    with pytest.raises(StopIteration):
        seq_map.__next__()


def test_cell_to_str():
    cell_to_string = sib.cell_to_string
    assert cell_to_string(((0, 1),)) == "0_lte_coord0_lt_1"
    with pytest.raises(lena.core.LenaValueError):
        cell_to_string(((0, 1),), coord_names=["x", "y"])
    ## coord_names=["x", "y"]
    # reversed order
    assert cell_to_string(((0, 1),(2, 3)), coord_join="__", 
                          coord_names=["x", "y"], reverse=True) == \
        "2_lte_y_lt_3__0_lte_x_lt_1"
    # normal order
    xy_res = "0_lte_x_lt_1__2_lte_y_lt_3"
    assert cell_to_string(((0, 1),(2, 3)), coord_join="__", 
                          coord_names=["x", "y"]) == xy_res
    var_context = {"combine": ({"name": "x"}, {"name": "y"})}
    assert cell_to_string(((0, 1),(2, 3)), coord_join="__", 
                          var_context=var_context) == xy_res


def test_get_example_bin():
    get_example_bin = sib.get_example_bin
    bins = [[0, 1], [1, 1]]
    assert get_example_bin(bins) == 0
    hist = Histogram([[0, 1, 2], [0, 1, 2]], bins)
    assert get_example_bin(hist) == 0


def test_transform_bins():
    ## test init
    with pytest.raises(lena.core.LenaTypeError):
        TransformBins(create_edges_str=1)

    ## test run
    # not histograms pass unchanged
    # histogram bins must be histograms
    hist = Histogram([1, 2], [1])
    data = [1, (2, {}), lena.structures.Graph(), hist]
    t = TransformBins()
    assert list(t.run(data)) == data

    data_unchanged = [(Histogram([0, 1], [hist]), {
        "split_into_bins": {
            "variable": {"name": "x"},
            "histogram": {"dim": 1}
        }
    })]
    data = copy.deepcopy(data_unchanged)
    results = list(t.run(data))
    assert len(results) == 1
    assert results[0][0] == hist
    assert results[0][1] == {
        'bin': {
            'edges': ((0, 1),), 'edges_str': '0_lte_x_lt_1'
        },
        'split_into_bins': {
            'context': {},
            'histogram': {'dim': 1},
            'variable': {'name': 'x'}
        }
    }
    # create_edges_str works
    t1 = TransformBins(create_edges_str=sib.cell_to_string)
    data = copy.deepcopy(data_unchanged)
    results1 = list(t1.run(data))
    assert results1 == results


def test_reduce_bin_content():
    ## test init
    with pytest.raises(lena.core.LenaTypeError):
        ReduceBinContent(1, ())
    # this works
    ReduceBinContent(lambda _: True, ())
    with pytest.raises(lena.core.LenaTypeError):
        ReduceBinContent(lambda _: True, 1)

    # not selected flow passes unchanged
    data = [1, (2, {}), (Histogram([0, 1], [1]), {})]
    r = ReduceBinContent(lena.math.vector3, lambda v: v.x)
    assert list(r.run(data)) == data
    # empty context
    data = [(Histogram([0, 1], [lena.math.vector3([0.5, 0, 1])]), {})]
    results = list(r.run(data))[0]
    assert results[0] == Histogram([0, 1], bins=[0.5])
    assert results[1] == {'bin_content': {'example_bin': {}}}
    data_template = [(Histogram([0, 1], [lena.math.vector3([0.5, 0, 1])]), {
        "split_into_bins": {
            "variable": {"name": "x"},
            "histogram": {"dim": 1}
        }
    })]
    data = copy.deepcopy(data_template)
    results = list(r.run(data))
    assert len(results) == 1
    results = results[0]
    assert results[0] == Histogram([0, 1], bins=[0.5])
    assert results[1] == {
        'bin_content': {'example_bin': {}},
        'histogram': {'dim': 1},
        'split_into_bins': {
            'histogram': {'dim': 1},
            'variable': {'name': 'x'}
        },
        'variable': {'name': 'x'}
    }
    X = Variable("x", lambda v: v.x)
    r = ReduceBinContent(lena.math.vector3, X, drop_bins_context=False)
    data = copy.deepcopy(data_template)
    results = list(r.run(data))[0]
    assert results[0] == Histogram([0, 1], bins=[0.5])
    assert results[1] == {
        'bin_content': {
            'all_bins': [{'variable': {'name': 'x'}}],
            'example_bin': {'variable': {'name': 'x'}}
        },
        'histogram': {'dim': 1},
        'split_into_bins': {
            'histogram': {'dim': 1},
            'variable': {'name': 'x'}
        },
        'variable': {'name': 'x'}
    }


def test_split_into_bins():
    ## test initialization
    # seq must be FillComputeSeq
    with pytest.raises(lena.core.LenaTypeError):
        sb = SplitIntoBins(seq=lena.core.Sequence(),
                           arg_func=Variable("no", lambda val: val[0]),
                           edges=[0, 1, 2])
    # arg_func must be a Variable
    with pytest.raises(lena.core.LenaTypeError):
        SplitIntoBins(Count(), lambda _: 1, [0, 1, 2])
    # 4 bins
    edges = [0, 1, 2, 3, 4]
    arg_func = Variable("x", lambda x: x)
    seq = Count()
    # this example sequence works
    s = SplitIntoBins(seq, arg_func, edges)
    # edges must be increasing
    with pytest.raises(lena.core.LenaValueError):
        SplitIntoBins(seq, arg_func, [0, 1, 0])
    # transform, if set, must be convertible to Sequence
    with pytest.raises(lena.core.LenaTypeError):
        SplitIntoBins(seq, arg_func, edges, transform=True)

    ## run works
    flow = [0, 1, 2, 3, 4, 0, -1]
    s = lena.core.Sequence(s)
    res = [r for r in s.run(flow)]
    # res = list(s.run(flow))
    assert len(res) == 1
    hist, context = res[0]
    assert context == {
        'split_into_bins': {
            'histogram': {
                'dim': 1, 'nbins': [4], 'ranges': [(0, 4)]
            },
            'variable': {'name': 'x'}
        }
    }
    assert hist.edges == edges
    assert hist.bins == [2, 1, 1, 1]

    # usual Split works.
    seq = Sequence(Split([Sum(), Count()]))
    flowc = [(val, context) for val in flow]
    res = seq.run(flowc)
    assert list(res) == [9, 7]

    # need to create a new seq, otherwise old one will be used further.
    seq = Split([Sum(), Count()])
    arg_func = Variable("x", lambda x: x)
    s = Sequence(SplitIntoBins(seq, arg_func, edges, transform=()))
    res = s.run(flowc)
    res_bins = map(lambda r: r[0].bins, res)
    # first element is Sum, second is Count
    assert list(res_bins) == [[0, 1, 2, 3], [2, 1, 1, 1]]

    # transform works
    t = ReduceBinContent(int, lambda x: x+1)
    edges = [0, 1, 2, 3, 4]
    arg_func = Variable("x", lambda x: x)
    s = Sequence(SplitIntoBins(seq, arg_func, edges, transform=t))
    res = list(s.run(flow))
    assert [r[0] for r in res] == [
        Histogram([0, 1, 2, 3, 4], bins=[1, 2, 3, 4]),
        Histogram([0, 1, 2, 3, 4], bins=[3, 2, 2, 2])
    ]

    # 2d histogram
    # edges = lena.math.mesh(ranges=((0, 1), (0, 1)), nbins=(10, 10))
    # s = SplitIntoBins(seq, arg_func, edges)
