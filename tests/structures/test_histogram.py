"""Histogram properties:

- scale of a not filled histogram is 0.
- scale (if filled with a non-negative weight) is always non-negative.
- scale of a histogram filled with *weight* is *weight* times scale.
- if all data fills into the histogram with bins size 1,
its scale is number of data points.
- if histogram bins are divided by N, its scale will be divided by N.
- Histogram and NumpyHistogram should be almost same (except for the upper edge).
"""
from __future__ import print_function

import math

import hypothesis
import pytest
import hypothesis.strategies as s
from hypothesis import given

from lena.core import LenaValueError
from lena.structures import Histogram
from lena.math import refine_mesh, isclose
from lena.structures.hist_functions import iter_bins, integral
from .histogram_strategy import generate_increasing_list, generate_data_in_range


Edges1dStrategy = s.builds(generate_increasing_list)

@given(Edges1dStrategy)
def test_init_scale_zero(edges):
    hist = Histogram(edges)
    assert hist.scale() == 0


@given(edges=Edges1dStrategy, weight=s.floats(),
       refinement=s.integers(min_value=1, max_value=20),
       data_samples=s.integers(min_value=1, max_value=50)
)
def test_scale_linear_on_weight(edges, weight, refinement, data_samples):
    hist1 = Histogram(edges)
    histw = Histogram(edges)
    min_edge, max_edge = edges[0], edges[-1]
    # print(min_edge, max_edge)
    # data can be outside of range too.
    data = generate_data_in_range(min_edge - 1, max_edge + 1, data_samples)
    # print("data =", data)
    for val in data:
        hist1.fill(val)
        histw.fill(val, weight)
    weight_scale = histw.scale()
    h1_scale = hist1.scale()
    if weight == 0:
        assert not weight_scale
    elif weight_scale == 0:
        # otherwise if weight is float('inf'), we get NaN on the left
        tst = h1_scale * weight
        assert isclose(tst, weight_scale) or math.isnan(tst)
    else:
        if math.isinf(weight_scale):
            assert math.isinf(h1_scale * weight) 
        elif math.isnan(weight_scale):
            assert math.isnan(h1_scale * weight) 
        else:
            assert isclose(h1_scale * weight, weight_scale)

    # scale is always non-negative if weight was not set
    assert h1_scale >= 0
    # scale doesn't change if we didn't fill
    if not math.isnan(weight_scale):
        assert histw.scale() == weight_scale

    # wrong for float edges.
    # n_of_filled_data = sum([1 for val in data if min_edge <= val < max_edge])
    # assert h1_scale == n_of_filled_data
    # # print(h1_scale)

    # if we refine mesh into N submeshes, its scale will be N times lower
    refined = refine_mesh(edges, refinement)
    hr = Histogram(refined)
    for val in data:
        hr.fill(val)
    assert isclose(h1_scale, refinement * hr.scale())


def test_histogram_3d():
    # new 3-dimensional histogram
    hist = Histogram([[1, 2, 3], [1, 2, 3], [1, 2, 3]])

    # new bins are zeroes
    assert hist.bins == [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]

    # fill works well
    hist.fill([1, 1, 1])
    assert hist.bins == [[[1, 0], [0, 0]], [[0, 0], [0, 0]]]
    hist.fill([1, 1, 2])
    assert hist.bins == [[[1, 1], [0, 0]], [[0, 0], [0, 0]]]

    # get bin on index
    assert hist.bins[0][0][1] == 1

    # iterate on bins
    assert list(iter_bins(hist.bins)) == [
        ((0, 0, 0), 1),
        ((0, 0, 1), 1),
        ((0, 1, 0), 0),
        ((0, 1, 1), 0),
        ((1, 0, 0), 0),
        ((1, 0, 1), 0),
        ((1, 1, 0), 0),
        ((1, 1, 1), 0)
    ]

    # get scale
    assert integral(hist.bins, hist.edges) == 2
    assert hist._scale is None
    assert hist.scale() == 2
    h2 = hist.scale(2)
    # assert h2.scale == 2
    assert h2.scale() == 2

    # rescale
    h1 = hist.scale(1)
    assert h1.bins[0][0] == [0.5, 0.5]
    # hist didn't change
    assert hist.bins[0][0] == [1, 1]

    # scale 0 can't be rescaled
    h0 = hist.scale(0)
    assert h0.scale() == 0
    with pytest.raises(LenaValueError):
        h0.scale(0)


def test_histogram_1d():
    hist = Histogram([0, 1, 2])
    # abandoned this idea. No exception is raised.
    # with pytest.raises(StopIteration):
    #     next(hist.compute())
    hist.fill(-10)
    assert hist.bins == [0, 0]
    hist.fill(10)
    assert hist.bins == [0, 0]
    assert repr(hist) == 'Histogram([0, 1, 2], bins=[0, 0])'

    hist = Histogram([0, 0.5, 1])
    hist.fill(0.5)
    assert hist.scale() == 0.5


if __name__ == "__main__":
    test_histogram_3d()
    test_scale_linear_on_weight()
