"""Histogram class."""
from __future__ import print_function

import lena.core
import lena.flow
from . import hist_functions as hf


class Histogram(lena.core.FillCompute):
    """Multidimensional histogram.

    Arbitrary dimension, variable bin size
    and a weight function during :meth:`fill` are supported.
    Lower bin edge is included, upper edge is excluded.
    Underflow and overflow values are skipped.
    Bin content type is defined during the initialization.

    Examples:

    >>> # two-dimensional histogram
    >>> hist = Histogram([[0, 1, 2], [0, 1, 2]])
    >>> hist.fill([0, 1])
    >>> hist.bins
    [[0, 1], [0, 0]]
    >>> values = [[0, 0], [1, 0], [1, 1]]
    >>> # use fill method
    >>> for v in values:
    ...     hist.fill(v)
    >>> hist.bins
    [[1, 1], [1, 1]]
    >>> # use as a Lena FillCompute element
    >>> # (yielded only after fully computed)
    >>> hseq = lena.core.Sequence(hist)
    >>> h, context = next(hseq.run(values))
    >>> print(h.bins)
    [[2, 1], [2, 2]]
    """
    # Note the differences from existing packages.
    # Numpy 1.16 (numpy.histogram): all but the last
    # (righthand-most) bin is half-open.
    # This histogram class has bin limits as in ROOT
    # (but without overflow and underflow).

    # Numpy: the first element of the range must be less than or equal to the second.
    # This histogram requires strictly increasing edges.
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html
    # https://root.cern.ch/root/htmldoc/guides/users-guide/Histograms.html#bin-numbering

    def __init__(self, edges, bins=None, make_bins=None, initial_value=0):
        """*edges* is a sequence of one-dimensional arrays,
        each containing strictly increasing bin edges.
        If *edges*' subarrays are not increasing
        or any of them has length less than 2,
        :exc:`.LenaValueError` is raised.

        Histogram bins by default are initialized with *initial_value*.
        It can be any object,
        which supports addition of a *weight* during *fill*
        (but that is not necessary if you don't plan to fill the histogram).
        If the *initial_value* is compound and requires special copying,
        create initial bins yourself (see :func:`.init_bins`).

        *Histogram* may be created from existing *bins* and *edges*.
        In this case a simple check of the shape of *bins* is done.
        If that is incorrect, :exc:`.LenaValueError` is raised.

        *make_bins* is a function without arguments, which creates new bins
        (it will be called during :meth:`__init__` and :meth:`reset`).
        *initial_value* in this case is ignored, but bin check is being done.
        If both *bins* and *make_bins* are provided,
        :exc:`.LenaTypeError` is raised.

        **Attributes**

        :attr:`Histogram.edges` is a list of edges on each dimension.
        Edges mark the borders of the bin.
        Edges along each dimension is a one-dimensional list,
        and the multidimensional bin is the result of all intersections
        of one-dimensional edges.
        For example, 3-dimensional histogram has edges of the form
        *[x_edges, y_edges, z_edges]*,
        and the 0th bin has the borders
        *((x[0], x[1]), (y[0], y[1]), (z[0], z[1]))*.

        Index in the edges is a tuple, where a given position corresponds
        to a dimension, and the content at that position
        to the bin along that dimension.
        For example, index *(0, 1, 3)* corresponds to the bin
        with lower edges *(x[0], y[1], z[3])*.

        :attr:`Histogram.bins` is a list of nested lists.
        Same index as for edges can be used to get bin content:
        bin at *(0, 1, 3)* can be obtained as *bins[0][1][3]*.
        Most nested arrays correspond to highest
        (further from x) coordinates.
        For example, for a 3-dimensional histogram bins equal to
        *[[[1, 1], [0, 0]], [[0, 0], [0, 0]]]*
        mean that the only filled bins are those
        where x and y indices are 0, and z index is 0 and 1.

        :attr:`dim` is the dimension of a histogram
        (length of its *edges* for a multidimensional histogram).

        .. admonition:: Programmer's note

            one- and multidimensional histograms
            have different *bins* and *edges* format.
            To be unified, 1-dimensional edges should be
            nested in a list (like *[[1, 2, 3]]*).
            Instead, they are simply the x-edges list,
            because it is more intuitive and one-dimensional histograms
            are used more often.
            To unify the interface for bins and edges in your code,
            use :func:`unify_1_md` function.
        """
        hf.check_edges_increasing(edges)
        self.edges = edges
        # self.fill_called = False
        self._scale = None
        if isinstance(edges[0], (list, tuple)):
            self.dim = len(edges)
        else:
            self.dim = 1

        self._initial_bins = bins
        self._make_bins = make_bins
        if make_bins is not None and bins is not None:
            raise lena.core.LenaTypeError(
                "either initial bins or make_bins must be provided, "
                "not both: {} and {}".format(bins, make_bins)
            )
        if make_bins:
            bins = make_bins()
        if bins is None:
            self.bins = hf.init_bins(self.edges, initial_value)
            self._initial_value = initial_value
        else:
            self.bins = bins
            # We can't make scale for an arbitrary histogram,
            # because it may contain complex values.
            # self._scale = self.make_scale()
            wrong_bins_error = lena.core.LenaValueError(
                "bins of incorrect shape given, {}".format(bins)
            )
            if self.dim == 1:
                if len(bins) != len(edges) - 1:
                    raise wrong_bins_error
            else:
                if len(bins) != len(edges[0]) - 1:
                    raise wrong_bins_error
        self._cur_context = {} # context from flow
        if self.dim > 1:
            self.ranges = [(axis[0], axis[-1]) for axis in edges]
            self.nbins = [len(axis) - 1 for axis in edges]
        else:
            self.ranges = [(edges[0], edges[-1])]
            self.nbins = [len(edges)-1]
        # run method is inherited automatically from FillCompute
        super(Histogram, self).__init__(self)
        self._hist_context = {
            "histogram": {
                "dim": self.dim,
                "ranges": self.ranges, "nbins": self.nbins
            }
        }

    def scale(self, other=None, recompute=False):
        """Compute or set scale (integral of the histogram).

        If *other* is None, return scale of this histogram.
        If its scale was not computed before,
        it is computed and stored for subsequent use
        (unless explicitly asked to *recompute*).

        If a float *other* is provided, rescale to *other*.
        A new histogram with the scale equal to *other*
        is returned, the original histogram remains unchanged.

        Histograms with scale equal to zero can't be rescaled.
        :exc:`.LenaValueError` is raised if one tries to do that.
        """
        if other is None:
            # return scale
            if self._scale is None or recompute:
                return hf.integral(*hf.unify_1_md(self.bins, self.edges))
            return self._scale
        else:
            # rescale from other
            scale = self.scale()
            if scale == 0:
                raise lena.core.LenaValueError(
                    "can't rescale histogram with zero scale"
                )
            new_hist = Histogram(
                self.edges,
                lena.math.md_map(lambda binc: binc * float(other) / scale,
                                 self.bins)
            )
            # don't recompute the scale if needed.
            new_hist._scale = other
            return new_hist

    def fill(self, value, weight=1):
        """Fill histogram with *value* with the given *weight*.

        *Value* can be a *(data, context)* pair. 
        Values outside the histogram edges are ignored.
        """
        # self.fill_called = True
        data, self._cur_context = lena.flow.get_data_context(value)
        indices = hf.get_bin_on_value(data, self.edges)
        subarr = self.bins
        for ind in indices[:-1]:
            # underflow
            if ind < 0:
                return
            try:
                subarr = subarr[ind]
            # overflow
            except IndexError:
                return
        # fill
        ind = indices[-1]
        # underflow
        if ind < 0:
            return
        try:
            subarr[ind] += weight
        except IndexError:
            return

    def compute(self):
        """Yield this histogram with context."""
        ## When used in split_into_bins, some cells might not be filled.
        ## This should not be an error.
        ## If your code really requires filled histograms, check it yourself.
        # if not self.fill_called:
        #     # no data filled, no histogram is returned.
        #     raise StopIteration
        yield (self, hf.make_hist_context(self, self._cur_context))

    def reset(self):
        """Reset the histogram.

        Current context is reset to an empty dict.
        Bins are reinitialized with the *initial_value*
        or with *make_bins* (depending on the initialization).

        If bins were set explicitly during the initialization,
        :exc:`.LenaRuntimeError` is raised.
        """
        self._cur_context = {}
        if self._make_bins is not None:
            self.bins = self._make_bins()
        elif self._initial_bins is None:
            self.bins = hf.init_bins(self.edges, self._initial_value)
        else:
            raise lena.core.LenaRuntimeError(
                "Histogram.reset() is called, but no make_bins is provided, "
                "because bins were set explicitly during the initialization"
            )

    def __eq__(self, other):
        """Note that in many cases floating numbers should be compared
        approximately (isclose).
        """
        if not isinstance(other, Histogram):
            return False
        return self.bins == other.bins and self.edges == other.edges

    def __repr__(self):
        return "Histogram({}, bins={})".format(self.edges, self.bins)
