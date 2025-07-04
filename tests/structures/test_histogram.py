"""Histogram properties:

- scale of a not filled histogram is 0.
- scale (if filled with a non-negative weight) is always non-negative.
- scale of a histogram filled with *weight* is *weight* times scale.
- if all data fills into the histogram with bins size 1,
  its scale is the number of data points.
- if histogram bins are divided by N, its scale is divided by N.
- Histogram and NumpyHistogram should be almost same (except for the upper edge).
"""
import math
import sys
from copy import deepcopy

import pytest
import hypothesis.strategies as st
from hypothesis import given

from lena.core import LenaValueError, LenaTypeError
from lena.structures import histogram, Histogram
from lena.math import refine_mesh, isclose
from lena.structures.hist_functions import iter_bins, integral
from .histogram_strategy import generate_increasing_list

## builds(target, /, *args, **kwargs)[source]
## Generates values by drawing from args and kwargs and passing them to the callable
## (provided as the first positional argument) in the appropriate argument position.
## https://hypothesis.readthedocs.io/en/latest/reference/strategies.html#hypothesis.strategies.builds
Edges1dStrategy = generate_increasing_list
# Edges1dStrategy = st.builds(generate_increasing_list)

@given(Edges1dStrategy())
def test_init_scale_zero(edges):
    hist = histogram(edges)
    assert hist.get_scale() == 0

# we disable subnormals, because in Python 3.10 sometimes (!)
# the test failed with an error,
#     where False = isclose((2.2216311086621543 * 5e-324), 1.5e-323)
# https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.floats
if sys.version_info.major > 2:
    floats_ = st.floats(allow_subnormal=False)
else:
    # in Python 2 allow_subnormal is not recognised
    floats_ = st.floats()


def hypo_isclose(a, b):
    if math.isinf(a):
        return math.isinf(b) 
    elif math.isnan(a):
        return math.isnan(b) 
    else:
        return isclose(a, b)


@given(edges=Edges1dStrategy(),
       weight=floats_,
       refinement=st.integers(min_value=1, max_value=20),
       # data_samples=st.integers(min_value=1, max_value=50),
       # we set these 1 and 20 by hand
       data=st.lists(st.floats(min_value=0, max_value=21, exclude_max=True))
)
def test_scale_linear_on_weight(edges, weight, refinement, data):
    hist1 = histogram(edges)
    histw = histogram(edges)
    min_edge, max_edge = edges[0], edges[-1]
    # print(min_edge, max_edge)
    # data can be outside of range too.
    # data = generate_data_in_range(min_edge - 1, max_edge + 1, data_samples)
    data_in_range = [val for val in data if min_edge <= val and val < max_edge]
    # print("data =", data)
    for val in data:
        hist1.fill(val)
        histw.fill(val, weight)
    weight_scale = histw.get_scale()
    h1_scale = hist1.get_scale()
    if weight == 0:
        assert not weight_scale
    elif weight_scale == 0:
        # otherwise if weight is float('inf'), we get NaN on the left
        tst = h1_scale * weight
        assert isclose(tst, weight_scale) or math.isnan(tst)
    else:
        assert hypo_isclose(weight_scale, h1_scale * weight)

    # scale is always non-negative if weight was not set
    assert h1_scale >= 0
    # scale doesn't change if we didn't fill
    if not math.isnan(weight_scale):
        assert histw.get_scale() == weight_scale

    ## nevents is correct ##

    # nevents without weight is correct
    assert hist1.get_n_events() == len(data_in_range)
    assert hist1.get_n_events() + hist1.n_out_of_range == len(data)

    ## nevents with weight is correct
    # unfortunately, we don't check it for different weights
    # to avoid 0*inf
    if len(data_in_range) == 0:
        assert histw.get_n_events() == 0
    else:
        assert hypo_isclose(histw.get_n_events(), len(data_in_range) * weight)

    # wrong for float edges.
    # n_of_filled_data = sum([1 for val in data if min_edge <= val < max_edge])
    # assert h1_scale == n_of_filled_data
    # # print(h1_scale)

    # if we refine mesh into N submeshes, its scale will be N times lower
    refined = refine_mesh(edges, refinement)
    hr = histogram(refined)
    for val in data:
        hr.fill(val)
    assert isclose(h1_scale, refinement * hr.get_scale())


def test_add():
    # one-dimensional histograms work
    hist1 = histogram([0., 1, 2.])
    hist2 = histogram([0., 1, 2.])
    hist1.fill(0)
    hist2.fill(1)
    hadd = hist1 + hist2
    assert hadd.edges == hist1.edges
    assert hadd.bins == [1, 1]

    # addition is commutative
    assert hist1 + hist2 == hist2 + hist1

    # subtraction works
    hsub = hist1 - hist2
    assert hsub.bins == [1, -1]

    # different edges raise
    hist2f = histogram([-1, 1, 2.])
    with pytest.raises(LenaValueError):
        hist1 + hist2f

    # 3-dimensional histograms work
    hist3 = histogram([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
    hist4 = histogram([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
    hist3.fill([1, 1, 1])
    # adding a zero histogram changes nothing
    assert hist3 + hist4 == hist3

    hist4.fill([1, 2, 1], weight=2)
    assert (hist3 + hist4).bins == [[[1, 0], [2, 0]], [[0, 0], [0, 0]]]


def test_histogram_3d():
    # new 3-dimensional histogram
    hist = histogram([[1, 2, 3], [1, 2, 3], [1, 2, 3]])

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
    assert hist.get_scale() == 2
    # change scale
    hist.scale_to(2)
    # assert h2.scale == 2
    assert hist.get_scale() == 2

    # rescale
    h1 = deepcopy(hist)
    h1 = h1.scale_to(1)
    assert h1.bins[0][0] == [0.5, 0.5]
    # hist didn't change
    assert hist.bins[0][0] == [1, 1]

    # scale 0 can't be rescaled
    h0 = deepcopy(hist)
    h0 = h0.scale_to(0)
    assert h0.get_scale() == 0
    with pytest.raises(LenaValueError):
        h0.scale_to(0)

    ## nevents work
    hnev = deepcopy(hist)
    assert hnev.get_n_events() == 2


def test_histogram_1d():
    hist1 = histogram([0, 1, 2])
    hist1.fill(-10)
    assert hist1.bins == [0, 0]
    hist1.fill(10)
    assert hist1.bins == [0, 0]
    assert repr(hist1) == ('histogram([0, 1, 2], bins=[0, 0], '
                           'out_of_range=[1, 1], n_out_of_range=2)')

    hist2 = histogram([0, 0.5, 1])
    hist2.fill(0.5)

    # _update_context works
    context = {}
    hist2._update_context(context)
    assert context == {
        "histogram":
            {
                "dim": 1,
                "nbins": 2,
                "ranges": (0, 1),
                "out_of_range": [0, 0],
                "n_out_of_range": 0,
            }
    }

    # scale is computed correctly
    assert hist2.get_scale() == 0.5

    assert hist2.get_n_events() == 1


def test_mul():
    ## multiplication of a 1-dimensional histogram works
    hist1 = histogram([0, 1, 2], [0, 1], n_out_of_range=2)
    # multiplication works
    hm2 = hist1 * 2
    assert hm2 == histogram([0, 1, 2], [0, 2], n_out_of_range=4)

    # histogram is not changed
    assert hist1 == histogram([0, 1, 2], [0, 1], n_out_of_range=2)

    ## multiplication of a 2-dimensional histogram works
    hist2 = histogram([[1, 2, 3], [1, 2, 3]])
    hist2.fill((1, 1))
    # multiplication in place works
    hist2 *= 0.5
    assert hist2 == histogram([[1, 2, 3], [1, 2, 3]], bins=[[0.5, 0], [0, 0]])

    # a histogram can only be multiplied on the right
    with pytest.raises(TypeError):
        2 * hist2
