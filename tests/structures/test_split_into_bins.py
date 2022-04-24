import pytest
import copy

import lena.core
from lena.core import Split, FillCompute, Sequence
from lena.variables import Variable
from lena.structures import histogram
from lena.structures import cell_to_string, get_example_bin
from lena.structures import SplitIntoBins, IterateBins, MapBins
from lena.structures.split_into_bins import _MdSeqMap
from lena.structures import iter_bins_with_edges

from tests.examples.fill_compute import Count, Sum


def test_iter_bins_with_edges():
    ibe = iter_bins_with_edges

    # one-dimensional list works
    bins = [0]
    edges = [0, 1]
    assert list(ibe(bins, edges)) == [(0, ((0, 1),))]
    assert list(ibe([0, 1], [0, 1, 2])) ==  [(0, ((0, 1),)), (1, ((1, 2),))]
    ## old interface
    # assert list(iter_bins_with_edges(bins, edges)) == [(0, ([0], [1]))]
    # assert list(iter_bins_with_edges([0, 1], [0, 1, 2])) == [(0, ([0], [1])), (1, ([1], [2]))]

    ## two-dimensional list works
    # one bin
    edges = [[0, 1], [2, 3]]
    bins = [[1]]
    # this (bins, edges) pair is legitimate
    ## strange to test it here!
    h = histogram(edges, bins)
    assert list(iter_bins_with_edges(bins, edges)) == [(1, ((0, 1), (2, 3)))]

    edges = [[0, 1, 2], [3, 4, 5]]
    bins = [[10, 20], [30, 40]]
    # this (bins, edges) pair is legitimate
    h = histogram(edges, bins)
    assert list(iter_bins_with_edges(bins, edges)) == [
        (10, ((0, 1), (3, 4))),
        (20, ((0, 1), (4, 5))),
        (30, ((1, 2), (3, 4))),
        (40, ((1, 2), (4, 5))),
    ]


def test__md_seq_map():
    arr = [Count(), Count()]
    arr[1].fill(1)
    seq_map = _MdSeqMap(lambda cell: cell.compute(), arr)
    assert list(seq_map) == [[0, 1]]
    with pytest.raises(StopIteration):
        seq_map.__next__()


def test_cell_to_str():
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
    bins = [[0, 1], [1, 1]]
    assert get_example_bin(bins) == 0
    hist = histogram([[0, 1, 2], [0, 1, 2]], bins)
    assert get_example_bin(hist) == 0


def test_iterate_bins():
    ## test init
    with pytest.raises(lena.core.LenaTypeError):
        IterateBins(create_edges_str=1)
    with pytest.raises(lena.core.LenaTypeError):
        IterateBins(select_bins=1)

    ## test run
    # not histograms pass unchanged
    # histogram bins must be histograms
    hist = histogram([1, 2], [1])
    data = [1, (2, {}), lena.structures.graph([[], []]), hist]
    t = IterateBins()
    assert list(t.run(data)) == data

    data_unchanged = [
        (histogram([0, 1], [hist]),
         {
             "variable": {"name": "x"},
             "histogram": {"dim": 1}
         })
    ]
    data = copy.deepcopy(data_unchanged)
    results = list(t.run(data))
    assert len(results) == 1
    assert results[0][0] == hist
    assert results[0][1] == {
        'bin': {
            'edges': ((0, 1),), 'edges_str': '0_lte_x_lt_1'
        },
        'bins': {
            'variable': {'name': 'x'},
            'histogram': {'dim': 1},
        }
    }
    # create_edges_str works
    t1 = IterateBins(create_edges_str=cell_to_string)
    data = copy.deepcopy(data_unchanged)
    results1 = list(t1.run(data))
    assert results1 == results


def test_map_bins():
    ## test init
    # wrong sequence raises
    with pytest.raises(lena.core.LenaTypeError):
        MapBins(1)

    # wrong selector raises
    with pytest.raises(lena.core.LenaTypeError):
        MapBins((), select_bins=1)

    # not selected flow passes unchanged
    data = [1, (2, {}), (histogram([0, 1], [1]), {})]
    r = MapBins(lambda v: v.x, select_bins=lena.math.vector3)
    assert list(r.run(data)) == data

    # empty context
    data = [(histogram([0, 1], [lena.math.vector3(0.5, 0, 1)]), {})]
    results = list(r.run(data))[0]
    assert results[0] == histogram([0, 1], bins=[0.5])
    assert results[1] == {}

    data_template = [(histogram([0, 1], [lena.math.vector3(0.5, 0, 1)]), {
        "variable": {"name": "x"},
        "histogram": {"dim": 1}
    })]
    data = copy.deepcopy(data_template)
    results = list(r.run(data))
    assert len(results) == 1
    results = results[0]
    assert results[0] == histogram([0, 1], bins=[0.5])
    assert results[1] == {
        'histogram': {'dim': 1},
        'variable': {'name': 'x'}
    }

    # retain bins context works
    X = Variable("x", lambda v: v.x)
    r = MapBins(X, select_bins=lena.math.vector3, drop_bins_context=False)
    data = copy.deepcopy(data_template)
    results = list(r.run(data))[0]
    assert results[0] == histogram([0, 1], bins=[(0.5, {'variable': {'name': 'x'}})])
    assert results[1] == {
        'value': {'variable': {'name': 'x'}},
        'histogram': {'dim': 1},
        'variable': {'name': 'x'},
    }


def test_split_into_bins():
    ## test initialization
    # seq must be FillComputeSeq
    with pytest.raises(lena.core.LenaTypeError):
        sb = SplitIntoBins(seq=lena.core.Sequence(),
                           arg_var=Variable("no", lambda val: val[0]),
                           edges=[0, 1, 2])
    # arg_var must be a Variable
    with pytest.raises(lena.core.LenaTypeError):
        SplitIntoBins(Count(), lambda _: 1, [0, 1, 2])
    # 4 bins
    edges = [0, 1, 2, 3, 4]
    arg_var = Variable("x", lambda x: x)
    ### TODO: check for several output values!
    ### Could have bugs with update_nested(histogram.context)
    seq = Count()
    # this example sequence works
    s = SplitIntoBins(seq, arg_var, edges)
    # edges must be increasing
    with pytest.raises(lena.core.LenaValueError):
        SplitIntoBins(seq, arg_var, [0, 1, 0])

    ## run works
    flow = [0, 1, 2, 3, 4, 0, -1]
    s = lena.core.Sequence(s)
    res = [r for r in s.run(flow)]
    # res = list(s.run(flow))
    assert len(res) == 1
    hist, context = res[0]
    # we don't check whether variable composition
    # creates a correct context.
    # We only delegate that explicitly in code.
    assert context == {'variable': {'name': 'x'}}
    assert hist.edges == edges
    assert hist.bins == [2, 1, 1, 1]

    # usual Split works.
    seq = Sequence(Split([Sum(), Count()]))
    flowc = [(val, context) for val in flow]
    res = seq.run(flowc)
    assert list(res) == [9, 7]

    # need to create a new seq, otherwise old one will be reused
    seq = Split([Sum(), Count()])
    arg_var = Variable("x", lambda x: x)
    s = Sequence(SplitIntoBins(seq, arg_var, edges))
    res = s.run(flowc)
    res_bins = map(lambda r: r[0].bins, res)
    # first element is Sum, second is Count
    assert list(res_bins) == [[0, 1, 2, 3], [2, 1, 1, 1]]

    # MapBins works
    ## It was a transform kwarg, but it seems not needed.
    map_no_context = MapBins(lambda x: x+1, select_bins=int)
    edges = [0, 1, 2, 3, 4]
    arg_var = Variable("x", lambda x: x)
    sib = SplitIntoBins(seq, arg_var, edges)

    s_map_no_context = Sequence(copy.deepcopy(sib), map_no_context)
    res = list(s_map_no_context.run(flow))
    assert [r[0] for r in res] == [
        histogram([0, 1, 2, 3, 4], bins=[1, 2, 3, 4]),
        histogram([0, 1, 2, 3, 4], bins=[3, 2, 2, 2])
    ]
    # no interference between contexts occurred,
    # proper deep copies were made.
    # context.value is missing because it is empty.
    assert [r[1] for r in res] == [
        {'variable': {'name': 'x'}},
        {'variable': {'name': 'x'}},
    ]

    map_with_context = MapBins(Variable("add1", lambda x: x+1), select_bins=int)
    s_map_with_context = Sequence(copy.deepcopy(sib), map_with_context)
    res_c = list(s_map_with_context.run(flow))
    # data doesn't change
    assert [r[0] for r in res_c] == [r[0] for r in res]
    # context is updated correctly
    new_context = {
        'value': {
            'variable': {'name': 'add1'}
        },
        'variable': {'name': 'x'}
    }
    assert [r[1] for r in res_c] == [new_context, new_context]

    # 2d histogram
    # edges = lena.math.mesh(ranges=((0, 1), (0, 1)), nbins=(10, 10))
    # s = SplitIntoBins(seq, arg_var, edges)
