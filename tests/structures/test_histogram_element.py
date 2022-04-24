import pytest

from lena.core import LenaValueError, LenaTypeError
from lena.structures import histogram, Histogram


def test_histogram_1d():
    hist = histogram([0, 1, 2])

    # test simple initialization
    # probably should make a deep copy of these bins and edges here
    h0 = Histogram(hist.edges, hist.bins)
    res00 = list(h0.compute())
    assert res00[0][0] == hist

    # fill outside of edges doesn't change
    h0.fill(-1)
    res01 = list(h0.compute())
    assert res01[0][0] == hist

    # reset doesn't change in our case
    h0.reset()
    res02 = list(h0.compute())
    assert res02[0][0] == hist
