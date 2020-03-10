"""Test graph."""
from __future__ import print_function

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
from lena.structures.graph import Graph
# from histogram_strategy import generate_increasing_list, generate_data_in_range


def test_graph():
    # test that sort is performed
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

    # fill works same as initialization
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

    r0 = resc.scale(0)
    with pytest.raises(lena.core.LenaValueError):
        r0.scale(1)
    r1 = Graph()
    with pytest.raises(lena.core.LenaAttributeError):
        r1.scale()

    with pytest.raises(AttributeError):
        # can't set points
        r1.points = 1


if __name__ == "__main__":
    test_graph()
