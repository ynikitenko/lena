import collections
import copy
import pytest

import lena.structures
from lena.core import LenaIndexError, LenaTypeError, LenaValueError
from lena.math import mesh
from lena.structures import histogram, graph
from lena.structures import (
    check_edges_increasing,
    get_bin_edges,
    get_bin_on_value_1d, get_bin_on_value,
    get_bin_on_index,
    HistCell,
    HistToGraph,
    hist_to_graph,
    integral,
    iter_bins,
    iter_bins_with_edges,
    iter_cells,
    unify_1_md,
)
from lena.variables import Variable


def test_check_edges_increasing():
    with pytest.raises(LenaValueError):
        check_edges_increasing([1, 0])
    with pytest.raises(LenaValueError):
        check_edges_increasing([1])
    with pytest.raises(LenaValueError):
        check_edges_increasing([])
    with pytest.raises(LenaValueError):
        check_edges_increasing([[1]])
    check_edges_increasing([1, 2, 3])


def test_get_bin_edges():
    hist = histogram(mesh((0, 5), 5))
    assert get_bin_edges(0, hist.edges) == (0, 1)
    hist = histogram(mesh(((0, 5), (0, 1)), (5, 2)))
    assert get_bin_edges((0, 1), hist.edges) == [(0, 1), (0.5, 1)]


def test_get_bin_on_value_1d():
    # attempts to cover the branch ind_guess == ind_max
    # it seems that it is impossible, because of the formula for shift.
    arr = [0, 1, 2, 3, 4, 4.1, 4.9, 7, 8, 9, 9.01]
    assert get_bin_on_value_1d(5, arr) == 6
    assert get_bin_on_value_1d(9.009, arr) == 9

    arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9.01]
    assert get_bin_on_value_1d(9.01, arr) == 10

    arr = [0, 1, 4, 5, 7, 10]
    assert get_bin_on_value_1d(0, arr) == 0
    assert get_bin_on_value_1d(2, arr) == 1
    assert get_bin_on_value_1d(4, arr) == 2
    assert get_bin_on_value_1d(10, arr) == 5

    arr = [0, 1]
    assert get_bin_on_value_1d(-0.5, arr) == -1
    assert get_bin_on_value_1d(0, arr) == 0
    assert get_bin_on_value_1d(0.5, arr) == 0
    assert get_bin_on_value_1d(1, arr) == 1
    assert get_bin_on_value_1d(1.5, arr) == 1

    arr = [0, 0.5, 1.1, 1.5]
    assert get_bin_on_value_1d(0.7, arr) == 1
    assert get_bin_on_value_1d(1.4, arr) == 2

    arr = [-100, 0.1, 0.2, 0.3, 0.4, 0.5, 1]
    assert get_bin_on_value_1d(0.05, arr) == 0
    assert get_bin_on_value_1d(0.11, arr) == 1
    assert get_bin_on_value_1d(0.49, arr) == 4
    assert get_bin_on_value_1d(0.51, arr) == 5
    assert get_bin_on_value_1d(0.99, arr) == 5

    arr = [-10] + list(range(1, 11))
    assert get_bin_on_value_1d(9.9, arr) == 9


def test_get_bin_on_value():
    edges = [[1, 2, 3], [1, 3.5]]
    assert get_bin_on_value((1.5, 2), edges) == [0, 0]
    assert get_bin_on_value((1.5, 0), edges) == [0, -1]
    assert get_bin_on_value((3, 2), edges) == [2, 0]

    edges = [1, 2, 3]
    assert get_bin_on_value(2, edges) == [1]
    with pytest.raises(LenaValueError):
    # I think that is Value error
    # with pytest.raises(LenaTypeError):
        get_bin_on_value((2, ), edges)


def test_get_bin_on_index():
    assert get_bin_on_index((0, 1), [[0, 1], [0, 0]]) == 1
    assert get_bin_on_index(0, [[0, 1], [0, 0]]) == [0, 1]
    with pytest.raises(LenaIndexError):
        get_bin_on_index(2, [[0, 1], [0, 0]])


def test_hist_to_graph():
    hist = histogram(mesh((0, 1), 1))
    hist.fill(0)
    context_no_transform = {"histogram": {"to_graph": False}}
    data = [
        0,
        copy.deepcopy(hist),
        (copy.deepcopy(hist), {}),
        (copy.deepcopy(hist), context_no_transform),
    ]
    nevents = Variable("nevents", lambda nevents: nevents)
    htg = HistToGraph(nevents)
    nev_context = {'value': {'variable': {'name': 'nevents'}}}
    gr = graph([[0], [1]])

    # run works correctly
    assert list(htg.run(data)) == [
        0,
        (gr, nev_context),
        (gr, nev_context),
        # values with the specified context are skipped
        (histogram([0, 1], bins=[1]),
         {'histogram': {'to_graph': False}}
        ),
    ]

    # different coordinates work
    assert list(HistToGraph(nevents, get_coordinate="right").run([hist])) == \
        [(graph([[1], [1]], scale=None), nev_context)]
    assert list(HistToGraph(nevents, get_coordinate="middle").run([hist])) == \
        [(graph([[0.5], [1]], scale=None), nev_context)]

    val_with_error = collections.namedtuple("val_with_error",
                                            ["value", "error"])
    hist1 = histogram(mesh((0, 1), 1))
    val = val_with_error(1, 2)
    hist1.bins = lena.structures.init_bins(hist1.edges, val)
    transform_value = Variable("value_error",
                               lambda val: (val.value, val.error))
    assert list(
        HistToGraph(
            make_value=transform_value, field_names=("x", "y", "z")
        ).run([hist1])
    ) == \
        [(graph([[0], [1], [2]], field_names="x,y,z"),
          {'value': {'variable': {'name': 'value_error'}}})]

    # wrong make_value raises
    with pytest.raises(lena.core.LenaTypeError):
        HistToGraph(lambda x: x, get_coordinate="left")

    # wrong coordinate raises LenaValueError in HistToGraph
    with pytest.raises(lena.core.LenaValueError):
        HistToGraph(nevents, get_coordinate="left_right")

    # same raises in hist_to_graph
    with pytest.raises(lena.core.LenaValueError):
        hist_to_graph(hist1, get_coordinate="left_right")

    # hist_to_graph works for 1-dimensional histograms
    assert hist_to_graph(histogram([0, 1], bins=[1])) == graph([[0], [1]])

    # scale works
    # True == 1 in Python, so better to test scale 2.
    assert hist_to_graph(histogram([0, 1], bins=[2]), scale=True) \
            == graph([[0], [2]], scale=2)

    # 2-dimensional histograms work
    hist2 = histogram(mesh(((0, 1), (0, 1)), (1, 1)), bins=[[2]])
    assert hist_to_graph(hist2, scale=True, field_names="x,y,z") \
            == graph([[0], [0], [2]], scale=2, field_names="x,y,z")


def test_iter_bins_with_edges():
    ibe = lambda hist: iter_bins_with_edges(hist.bins, hist.edges)

    # one-dimensional histogram works
    hist1 = histogram(mesh((0, 3), 3), bins=[0, 1, 2])
    assert list(ibe(hist1)) == [
        (0, ((0, 1.0),)), (1, ((1.0, 2.0),)), (2, ((2.0, 3.0),))
    ]

    # two-dimensional histogram works
    hist2 = histogram(mesh(((0, 1), (0, 1)), (1, 1)), bins=[[2]])
    assert list(ibe(hist2)) == [(2, ((0, 1), (0, 1)))]


def test_iter_cells():
    ## full range iteration works.
    # 1d histogram
    hist = histogram(mesh((0, 2), 2))
    assert list(iter_cells(hist)) == [HistCell([(0, 1.)], 0, (0,)),
                                      HistCell([(1., 2.)], 0, (1,))]
    # multidimensional histogram
    hist = histogram(mesh(((0, 5), (0, 1)), (5, 2)))
    assert list(iter_cells(hist))[:2] == [
        HistCell([(0, 1.), (0, 0.5)], 0, (0, 0)),
        HistCell([(0, 1.), (0.5, 1.)], 0, (0, 1))
    ]

    ## None works
    # 1-dimensional histogram works
    hist = histogram(mesh((0, 4), 4))

    assert list(iter_cells(hist, ranges=((None, 3),))) == [
        HistCell(edges=[(0, 1.0)], bin=0, index=(0,)),
        HistCell(edges=[(1.0, 2.0)], bin=0, index=(1,)),
        HistCell(edges=[(2.0, 3.0)], bin=0, index=(2,)),
        # HistCell(edges=(3.0, 4), bin=0, index=(3,)),
    ]

    # empty coord_range yields nothing
    assert list(iter_cells(hist, coord_ranges=((-10, -5)))) == []

    # nonexistent ranges are not allowed
    with pytest.raises(LenaValueError):
        list(iter_cells(hist, ranges=((None, 30),)))
    with pytest.raises(LenaValueError):
        list(iter_cells(hist, ranges=((-1, None),)))
    with pytest.raises(LenaTypeError):
        list(iter_cells(hist, ranges=((None, None),), coord_ranges=(None, None)))

    # multidimensional histogram works
    hist = histogram(mesh(((0, 4), (0, 2)), (4, 2)))

    assert list(iter_cells(hist, ranges=((1, None), (0, 2)))) == [
        # HistCell(edges=[(0, 1.0), (0, 1.0)], bin=0, index=(0, 0)),
        # HistCell(edges=[(0, 1.0), (1.0, 2)], bin=0, index=(0, 1)),
        HistCell(edges=[(1.0, 2.0), (0, 1.0)], bin=0, index=(1, 0)),
        HistCell(edges=[(1.0, 2.0), (1.0, 2)], bin=0, index=(1, 1)),
        HistCell(edges=[(2.0, 3.0), (0, 1.0)], bin=0, index=(2, 0)),
        HistCell(edges=[(2.0, 3.0), (1.0, 2)], bin=0, index=(2, 1)),
        HistCell(edges=[(3.0, 4), (0, 1.0)], bin=0, index=(3, 0)),
        HistCell(edges=[(3.0, 4), (1.0, 2)], bin=0, index=(3, 1)),
    ]

    # coord_ranges containing hist.edges produce same result as a full range
    # multidimensional
    assert list(iter_cells(hist, ranges=((None, None), (0, None)))) == \
        list(iter_cells(hist, coord_ranges=((0, 50), (-100, 100))))

    # empty range on first coordinate yields nothing
    assert list(iter_cells(hist, coord_ranges=((-10, -5), (-100, 100)))) == []
    # empty range on second coordinate yields nothing
    assert list(iter_cells(hist, coord_ranges=((0, 10), (-100, -10)))) == []


def test_unify_1_md():
    arr1 = [1, 2, 3]
    arr2 = [arr1]
    assert unify_1_md([], arr2)[1] == arr2
    assert unify_1_md([], arr1)[1] == arr2
