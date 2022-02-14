import copy
import math
import random

import hypothesis
import pytest
import hypothesis.strategies as s
from hypothesis import given

import lena.flow
from lena.core import LenaValueError
from lena.structures import Histogram
from lena.math import refine_mesh, isclose
from lena.structures.graph import graph, Graph
# from histogram_strategy import generate_increasing_list, generate_data_in_range


def test_graph_structure():
    xs = [0, 1]
    ys = [2, 3]

    # simplest 2d initialization works
    gr0 = graph([xs, ys])
    assert gr0.field_names == ("x", "y")

    # iteration works
    assert list(gr0) == [(0, 2), (1, 3)]

    assert gr0.scale() is None

    # empty points raise
    with pytest.raises(LenaValueError):
        graph([], "")
    # duplicate names raise
    with pytest.raises(LenaValueError):
        graph([xs, ys], "x,x")
    # wrong sequence lengths raise
    with pytest.raises(LenaValueError):
        graph([[], [1]])
    # field names are same as the points length
    with pytest.raises(LenaValueError):
        graph([xs, ys], "x")
    # unset scale raises
    with pytest.raises(LenaValueError):
        gr0.scale(1)

    # rescaling when the scale is set works
    # 2d graph works
    gr1 = graph(copy.deepcopy([xs, ys]), scale=2)
    assert gr1.scale() == 2
    gr1.scale(1)
    assert gr1._points == [xs, [1, 1.5]]
    assert gr1.scale() == 1

    # 3d graph works
    gr2 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x,y,z", scale=2)
    gr2.scale(3)
    assert gr2._points == [xs, ys, [1.5, 3.]]
    assert gr2.scale() == 3

    # graph with errors works
    # x errors are unchanged, y coords change
    gr3 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x, y, x_err", scale=2)
    # spaces in field_names work
    assert gr3.field_names == ["x", "y", "x_err"]
    gr3.scale(1)
    assert gr3._points == [xs, [1, 1.5], [1, 2]]

    # y errors and coords change
    gr4 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x,y,y_err", scale=2)
    gr4.scale(1)
    assert gr4._points == [xs, [1, 1.5], [0.5, 1]]


def test_graph():
    # sorts well
    coords = range(0, 10)
    values = map(math.sin, coords)
    points = list(zip(coords, values))
    graph = Graph(points)
    print(graph)
    sorted_points = copy.deepcopy(points)
    random.shuffle(points)
    graph2 = Graph(points)
    gr_points, gr_context = next(graph2.request())
    assert gr_points.points == sorted_points

    # test repr
    coords = range(0, 3)
    values = map(lambda x: x+1, coords)
    points = list(zip(coords, values))
    random.shuffle(points)
    graph = Graph(points)
    # sort works
    assert repr(graph) == ("Graph(points=[(0, 1), (1, 2), (2, 3)], "
                           "scale=None, sort=True)")

    # doesn't sort when False
    points = [(2, 3), (0, 1), (1, 2)]
    unsorted_graph = Graph(points, sort=False)
    assert (repr(unsorted_graph) == 
            "Graph(points=[(2, 3), (0, 1), (1, 2)], scale=None, sort=False)")

    # fill with points works same as initialization
    new_unsorted_graph = Graph(sort=False)
    for pt in points:
        new_unsorted_graph.fill(pt)
    assert repr(new_unsorted_graph) == repr(unsorted_graph)

    # 2d graph
    coords = [(0, 1), (1, 0), (0, 0), (1, 1)]
    values = map(lambda crd: crd[0] + crd[1], coords)
    points = list(zip(coords, values))
    graph2d = Graph(points)
    graph2d.fill((((2, 0), 2), {"scale": 1, "dim": 2}))
    assert graph2d.scale() == 1
    rescaled = graph2d.scale(2)

    # sorting works fine, scale too
    assert repr(rescaled) == (
        "Graph(points=[((0, 0), 0.0), ((0, 1), 2.0), "
        "((1, 0), 2.0), ((1, 1), 4.0), ((2, 0), 4.0)], "
        "scale=2, sort=True)"
    )

    # rescale of composite values works
    pt = ((2, 3), (10, {"5th element": "5"}))
    rescaled.fill((pt, {}))
    resc = rescaled.scale(1)
    assert resc.points[-1] == ((2, 3), 5.0)

    # can't rescale 0 or unknown scale
    r0 = resc.scale(0)
    with pytest.raises(lena.core.LenaValueError):
        r0.scale(1)
    r1 = Graph()
    with pytest.raises(lena.core.LenaAttributeError):
        r1.scale()

    # can't set points
    with pytest.raises(AttributeError):
        r1.points = 1

    # context kwarg works
    context = {"data": "d1"}
    gr1 = Graph([(0, 1)], context=copy.deepcopy(context))
    gr2 = Graph()
    gr2.fill(((0, 1), copy.deepcopy(context)))
    res1 = list(gr1.request())
    res2 = list(gr2.request())
    assert res1 == res2

    # context must be a context, if set
    with pytest.raises(lena.core.LenaTypeError):
        Graph([(0, 1)], context=0)

    # reset works
    gr1.reset()
    assert gr1 == Graph()


def test_graph_equal():
    # test equality
    gr1 = Graph([(0, 1)])

    # non-Graphs are not equal to graphs
    # this line is not checked when using !=
    assert not gr1 == 1

    ## equality with scale works ##
    # set and unset scales are not equal
    gr2 = Graph([(0, 1)], scale=1)
    assert not gr1 == gr2

    # sometimes they are really equal
    gr3 = Graph(scale=1)
    gr3.fill((0, 1))
    assert gr2 == gr3

    # different points compare different
    gr3.fill((0, 1))
    assert not gr2 == gr3


def test_graph_to_csv():
    # to_csv works
    gr2 = Graph([(0, 1)])
    csv2 = gr2.to_csv()
    assert csv2 == "0,1"

    # fill with a point with another dimension is prohibited
    # should be moved to another method though...
    gr2.fill((((0, 1, 2), (3, 4)), {}))
    # in python3 it raises TypeError
    with pytest.raises((lena.core.LenaValueError, TypeError)):
        gr2.to_csv()

    # multidimensional to_csv works
    gr2 = Graph([(((0, 1, 2), (3, 4)))])
    assert gr2.to_csv() == "0,1,2,3,4"

    # header works
    header = "x,y,z,f,g"
    assert gr2.to_csv(header=header) == header + '\n' + "0,1,2,3,4"
