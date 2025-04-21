"""Fill data into a histogram using numpy histogram."""
import lena.flow
import lena.structures


class NumpyHistogram(object):
    """Create a histogram using a 1-dimensional *numpy.histogram*.

    The result of *compute* is a Lena :class:`.histogram`,
    but it is calculated using *numpy* histogram,
    and all its initialization arguments are passed to *numpy*.

    .. admonition:: Examples

        With the default arguments *NumpyHistogram()*,
        bins are automatically derived from data.

        With *NumpyHistogram(bins=list(range(0, 5)), density=True)*
        bins are set explicitly.

    .. warning::
        as *numpy* histogram is computed from an existing array,
        all values are stored in the internal data structure during *fill*,
        which is memory unsafe.
    """

    def __init__(self, *args, **kwargs):
        r"""Use *\*args* and *\*\*kwargs* for *numpy.histogram* initialization.

        Default *bins* keyword argument is *auto*.

        .. deprecated:: 0.6
            A keyword argument *reset* specifies the exact behaviour of *request*.
        """
        # todo: this interface is too broad.
        # One may ask a partial constructor (a function)
        # for the numpy histogram with proper arguments.
        import numpy
        self._create_hist = numpy.histogram

        self._reset = kwargs.pop("reset", True)
        self._args = args
        self._kwargs = kwargs
        if "bins" not in kwargs:
            self._kwargs.update({"bins": "auto"})
        # self.reset()
        # numpy.array can't be extended on the fly
        self._data = []
        self._cur_context = {}

    def fill(self, val):
        """Add data to the internal storage."""
        data, context = lena.flow.get_data_context(val)
        self._data.append(data)
        self._cur_context = context

    def compute(self):
        """Yield the computed :class:`.histogram` and context."""
        bins, edges = self._create_hist(self._data, *self._args, **self._kwargs)
        # since np.histogram returns exactly two arrays, bins and edges,
        # complete information is conserved in the Histogram.
        hist = lena.structures.histogram(edges, bins)
        yield (hist, self._cur_context)

    def request(self):
        """
        .. deprecated:: 0.6

        Compute the final histogram.

        Return :class:`.histogram` with context.

        If *reset* was set during the initialization,
        *reset* method is called.
        """
        bins, edges = self._create_hist(self._data, *self._args, **self._kwargs)
        # since np.histogram returns exactly two arrays, bins and edges,
        # complete information is conserved in the Histogram.
        hist = lena.structures.histogram(edges, bins)
        # deep copy is made here
        # hf.make_hist_context(hist, self._cur_context)
        if self._reset:
            self.reset()
        yield (hist, self._cur_context)

    def reset(self):
        """Reset data and context.

        Remove all data for this histogram and set current context to {}.
        """
        self._data = []
        self._cur_context = {}
