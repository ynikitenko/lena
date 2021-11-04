import pytest

from lena.core import LenaValueError, LenaTypeError
from lena.structures import histogram, Histogram


def test_histogram_1d():
    hist = histogram([0, 1, 2])
    # context must be a dict
    with pytest.raises(LenaTypeError):
        Histogram(hist.edges, hist.bins, context=0)
    # abandoned this idea. No exception is raised.
    # with pytest.raises(StopIteration):
    #     next(hist.compute())
