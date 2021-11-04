from __future__ import print_function

import pytest

from lena.core import LenaValueError
from lena.math import isclose

np = pytest.importorskip('numpy')
from lena.structures import histogram
from lena.structures.numpy_histogram import NumpyHistogram


## Ignore numpy warning raised when trying to use an empty histogram.
# /usr/local/lib64/python3.7/site-packages/numpy/lib/histograms.py:908: RuntimeWarning: invalid value encountered in true_divide
#    return n/db/n.sum(), bin_edges

@pytest.mark.filterwarnings("ignore:::numpy.lib.histograms")
def test_numpy_histogram():
    nhist = NumpyHistogram(bins=list(range(0, 5)), density=True)
    filled_hist = histogram([0, 1, 2, 3, 4], bins=[0.25, 0.25, 0.25 ,0.25])
    filled_context = {'histogram': {'ranges': [(0, 4)], 'dim': 1, 'nbins': [4]}}

    empty_hist, empty_cont = next(nhist.request())
    assert empty_cont == filled_context

    data = list(range(0, 4))
    for val in data:
        nhist.fill(val)
    lhist, context = next(nhist.request())
    # assert lhist.bins == filled_hist.bins
    assert all(v1 == v2 for v1, v2 in zip(lhist.bins, filled_hist.bins))
    assert all(v1 == v2 for v1, v2 in zip(lhist.edges, filled_hist.edges))
    assert context == filled_context

    # histogram is reset after request
    next_hist, next_cont = next(nhist.request())
    assert next_hist, next_cont == (empty_hist, empty_cont)

    true_bins = np.array([0.25, 0.25, 0.25, 0.25])
    for ind, bin in enumerate(true_bins):
        assert lhist.bins[ind] == bin
    assert lhist.scale() == 1

    nhist1 = NumpyHistogram(bins=list(range(0, 5)), density=True, reset=False)
    for val in data:
        nhist1.fill(val)
    lhist1, context1 = next(nhist1.request())
    assert all(v1 == v2 for v1, v2 in zip(lhist1.bins, filled_hist.bins))
    assert all(v1 == v2 for v1, v2 in zip(lhist1.edges, filled_hist.edges))
    assert context1 == filled_context
    # request is idempotent if no reset was called
    assert lhist1, context1 == next(nhist1.request())
