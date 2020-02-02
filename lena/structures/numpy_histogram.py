"""Fill data into a histogram using numpy histogram."""
from __future__ import print_function

import numpy

import lena.flow
import lena.structures
from . import hist_functions as hf


class NumpyHistogram(object):
    """Create a Histogram using a 1-dimensional *numpy.histogram*.

    The result of *compute* is a Lena *Histogram*,
    but it is calculated using *numpy* histogram,
    and all its initialization arguments are passed to *numpy*.

    .. admonition:: Examples

        With *NumpyHistogram()*
        bins are automatically derived from data.

        With *NumpyHistogram(bins=list(range(0, 5)), density=True)*
        bins are set explicitly.

    Warning
    -------
    as *numpy* histogram is computed from an existing array,
    all values are stored in the internal data structure during *fill*,
    which may take much memory.
    """

    def __init__(self, *args, **kwargs):
        r"""Use *\*args* and *\*\*kwargs* for *numpy.histogram* initialization.

        Default *bins* keyword argument is *auto*.
        """
        self._args = args
        self._kwargs = kwargs
        if "bins" not in kwargs:
            self._kwargs.update({"bins": "auto"})
        # numpy.array can't be extended on the fly
        self._data = []
        self._context = {}

    def fill(self, val):
        """Add data to the internal storage."""
        data, context = lena.flow.get_data(val), lena.flow.get_context(val)
        self._data.append(data)
        self._context = context

    def compute(self):
        """Compute the final histogram.

        Return :ref:`Histogram <Histogram>` with context.

        All data for this histogram is reset.
        """
        bins, edges = numpy.histogram(self._data, *self._args, **self._kwargs)
        self._data = []
        # self._context.update({"type": "histogram"})
        hist = lena.structures.Histogram(edges, bins)
        context = hf.make_hist_context(hist, self._context)
        yield (hist, context)

    def request(self):
        """Calculate histogram.

        Return :ref:`Histogram <Histogram>` with context.
        """
        bins, edges = numpy.histogram(self._data, *self._args, **self._kwargs)
        hist = lena.structures.Histogram(edges, bins)
        context = hf.make_hist_context(hist, self._context)
        yield (hist, context)
