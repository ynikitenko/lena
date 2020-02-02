from __future__ import print_function

import pytest

from lena.core import LenaValueError
from lena.math import isclose

np = pytest.importorskip('numpy')
from lena.structures.numpy_histogram import NumpyHistogram


def test_numpy_histogram():
    nhist = NumpyHistogram(bins=list(range(0, 5)), density=True)
    data = list(range(0, 4))
    for val in data:
        nhist.fill(val)
    lhist, context = next(nhist.request())
    # request is idempotent
    assert lhist, context == next(nhist.request())

    # compute and request give same results
    computed = next(nhist.compute())
    assert all(isclose(v1, v2) for v1, v2 in zip(lhist.bins, computed[0].bins))
    assert context == computed[1]
    print(lhist, context, computed)

    true_bins = np.array([0.25, 0.25, 0.25, 0.25])
    for ind, bin in enumerate(true_bins):
        assert lhist.bins[ind] == bin
    assert lhist.scale() == 1
