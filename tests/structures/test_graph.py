import copy
import math
import random

import pytest

import lena.flow
from lena.core import LenaValueError
from lena.structures import Histogram
from lena.math import refine_mesh, isclose
from lena.structures.graph import graph, Graph


def test_graph():
    xs = [0, 1]
    ys = [2, 3]

    # simplest 2d initialization works
    gr0 = graph([xs, ys])
    assert gr0.field_names == ("x", "y")
    # dim works
    assert gr0.dim == 2

    # iteration works
    assert list(gr0) == [(0, 2), (1, 3)]

    assert gr0.scale() is None

    ## points work correctly
    # empty points raise
    with pytest.raises(LenaValueError):
        graph([], "")
    # wrong sequence lengths raise
    with pytest.raises(LenaValueError):
        graph([[], [1]])

    ## field_names work correctly
    # duplicate names raise
    with pytest.raises(LenaValueError):
        graph([xs, ys], "x,x")
    # non-tuple field names raise
    with pytest.raises(lena.core.LenaTypeError):
        graph([xs, ys], ["x", "y"])

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
    assert gr1.dim == 2
    gr1.scale(1)
    assert gr1.coords == [xs, [1, 1.5]]
    assert gr1.scale() == 1

    # 3d graph works
    gr2 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x,y,z", scale=2)
    gr2.scale(3)
    assert gr2.coords == [xs, ys, [1.5, 3.]]
    assert gr2.scale() == 3
    assert gr2.dim == 3

    # graph with errors works
    # x errors are unchanged, y coords change
    gr3 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x, y, error_x", scale=2)
    # spaces in field_names work
    assert gr3.field_names == ("x", "y", "error_x")
    gr3.scale(1)
    assert gr3.coords == [xs, [1, 1.5], [1, 2]]

    # y errors and coords change
    gr4 = graph(copy.deepcopy([xs, ys, [1, 2]]), field_names="x,y,error_y", scale=2)
    gr4.scale(1)
    assert gr4.dim == 2
    assert gr4.coords == [xs, [1, 1.5], [0.5, 1]]


def test_graph_add():
    xs = [0, 1]
    ys = [2, 3]

    # sum of 1-dimensional graphs work
    gr0 = graph([xs, ys])
    gr1 = graph([xs, ys])
    gradd1 = gr0 + gr1
    assert gradd1 == graph([[0, 1], [4, 6]],
                           field_names=('x', 'y'), scale=None)


def test_graph_error_fields():
    xs = [0, 1]
    ys = [2, 3]
    zs = [1, 2]

    # no error fields works
    gr0 = graph(copy.deepcopy([xs, ys]), field_names="x, y", scale=2)
    assert gr0._parsed_error_names == []

    # one error field works
    gr1 = graph(copy.deepcopy([xs, ys, [1, 2]]),
                field_names="x, y, error_x", scale=2)
    assert gr1._parsed_error_names == [('error', 'x', '', 2)]

    # wrong order of fields raises
    with pytest.raises(lena.core.LenaValueError) as exc:
        graph([xs, ys, [1, 2], xs], field_names="x,y,error_x,z")
    assert str(exc.value) == "errors must go after coordinate fields"

    # ambiguous error fields raise
    with pytest.raises(lena.core.LenaValueError) as exc:
        graph([xs, ys, [1, 2]], field_names="x,x_low,error_x_low")
    assert str(exc.value).startswith("ambiguous")

    # errors with unknown field names raise
    with pytest.raises(lena.core.LenaValueError) as exc:
        graph([xs, ys, zs], field_names="x,y,error_z")
    assert str(exc.value) == "no coordinate corresponding to error_z given"


def test_update_context():
    xs = [0, 1]
    ys = [2, 3]
    zs = [1, 2]

    # no error fields works
    gr0 = graph(copy.deepcopy([xs, ys]), field_names="x, y", scale=2)
    context = {}
    gr0._update_context(context)
    assert context == {}

    gr1 = graph([xs, ys, zs], field_names="E,t,error_E_low", scale=2)
    gr1._update_context(context)
    assert context == {'error': {'x_low': {'index': 2}}}

    # 4 coordinates, arbitrary error sequence work
    gr2 = graph([xs]*8,
                field_names="a,b,c,d,error_b,error_a_low,error_d,error_d_low")
    gr2._update_context(context)
    assert context == {
        'error': {
            'x_low': {'index': 5},
            'y': {'index': 4}
        }
    }


# Graph is deprecated, but we keep its tests at the moment.
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_Graph():
    # sorts well
    coords = range(0, 10)
    values = map(math.sin, coords)
    points = list(zip(coords, values))
    graph = Graph(points)
    print(graph)
    sorted_points = copy.deepcopy(points)
    random.shuffle(points)
    graph2 = Graph(points)
    gr_points, gr_context = next(graph2.compute())
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
    res1 = list(gr1.compute())
    res2 = list(gr2.compute())
    assert res1 == res2

    # context must be a context, if set
    with pytest.raises(lena.core.LenaTypeError):
        Graph([(0, 1)], context=0)

    # reset works
    gr1.reset()
    assert gr1 == Graph()


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
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


@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_graph_to_csv():
    # rows work
    gr1 = Graph([(0, 1)])
    rows1 = list(gr1.rows())
    assert rows1 == [(0, 1)]

    # # fill with a point with another dimension is prohibited
    # # should be moved to another method though...
    # gr2.fill((((0, 1, 2), (3, 4)), {}))
    # # in python3 it raises TypeError
    # with pytest.raises((lena.core.LenaValueError, TypeError)):
    #     gr2.to_csv()

    # multidimensional to_csv works
    gr2 = Graph([(((0, 1, 2), (3, 4)))])
    assert list(gr2.rows()) == [(0, 1, 2, 3, 4)]

    # # header works
    # header = "x,y,z,f,g"
    # assert gr2.to_csv(header=header) == header + '\n' + "0,1,2,3,4"
