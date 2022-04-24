"""Histogram structure *histogram* and element *Histogram*."""
import copy

import lena.context
import lena.core
import lena.flow
import lena.math
from . import hist_functions as hf


class histogram():
    """A multidimensional histogram.

    Arbitrary dimension, variable bin size and weights are supported.
    Lower bin edge is included, upper edge is excluded.
    Underflow and overflow values are skipped.
    Bin content can be of arbitrary type,
    which is defined during initialization.

    Examples:

    >>> # a two-dimensional histogram
    >>> hist = histogram([[0, 1, 2], [0, 1, 2]])
    >>> hist.fill([0, 1])
    >>> hist.bins
    [[0, 1], [0, 0]]
    >>> values = [[0, 0], [1, 0], [1, 1]]
    >>> # fill the histogram with values
    >>> for v in values:
    ...     hist.fill(v)
    >>> hist.bins
    [[1, 1], [1, 1]]
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

    def __init__(self, edges, bins=None, initial_value=0):
        """*edges* is a sequence of one-dimensional arrays,
        each containing strictly increasing bin edges.

        Histogram's bins by default
        are initialized with *initial_value*.
        It can be any object that supports addition with *weight*
        during *fill* (but that is not necessary
        if you don't plan to fill the histogram).
        If the *initial_value* is compound and requires special copying,
        create initial bins yourself (see :func:`.init_bins`).

        A histogram can be created from existing *bins* and *edges*.
        In this case a simple check of the shape of *bins* is done
        (raising :exc:`.LenaValueError` if failed).

        **Attributes**

        :attr:`edges` is a list of edges on each dimension.
        Edges mark the borders of the bin.
        Edges along each dimension are one-dimensional lists,
        and the multidimensional bin is the result of all intersections
        of one-dimensional edges.
        For example, a 3-dimensional histogram has edges of the form
        *[x_edges, y_edges, z_edges]*,
        and the 0th bin has borders
        *((x[0], x[1]), (y[0], y[1]), (z[0], z[1]))*.

        Index in the edges is a tuple, where a given position corresponds
        to a dimension, and the content at that position
        to the bin along that dimension.
        For example, index *(0, 1, 3)* corresponds to the bin
        with lower edges *(x[0], y[1], z[3])*.

        :attr:`bins` is a list of nested lists.
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

        If subarrays of *edges* are not increasing
        or if any of them has length less than 2,
        :exc:`.LenaValueError` is raised.

        .. admonition:: Programmer's note

            one- and multidimensional histograms
            have different *bins* and *edges* format.
            To be unified, 1-dimensional edges should be
            nested in a list (like *[[1, 2, 3]]*).
            Instead, they are simply the x-edges list,
            because it is more intuitive and one-dimensional histograms
            are used more often.
            To unify the interface for bins and edges in your code,
            use :func:`.unify_1_md` function.
        """
        # todo: allow creation of *edges* from tuples
        # (without lena.math.mesh). Allow bin_size in this case.
        hf.check_edges_increasing(edges)
        self.edges = edges
        self._scale = None

        if hasattr(edges[0], "__iter__"):
            self.dim = len(edges)
        else:
            self.dim = 1

        # todo: add a kwarg no_check=False to disable bins testing
        if bins is None:
            self.bins = hf.init_bins(self.edges, initial_value)
        else:
            self.bins = bins
            # We can't make scale for an arbitrary histogram,
            # because it may contain compound values.
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
        if self.dim > 1:
            self.ranges = [(axis[0], axis[-1]) for axis in edges]
            self.nbins =  [len(axis) - 1 for axis in edges]
        else:
            self.ranges = [(edges[0], edges[-1])]
            self.nbins = [len(edges)-1]

    def __eq__(self, other):
        """Two histograms are equal, if and only if they have
        equal bins and equal edges.

        If *other* is not a :class:`.histogram`, return ``False``.

        Note that floating numbers should be compared
        approximately (using :func:`math.isclose`).
        """
        if not isinstance(other, histogram):
            # in Python comparison between different types is allowed
            return False
        return self.bins == other.bins and self.edges == other.edges

    def fill(self, coord, weight=1):
        """Fill histogram at *coord* with the given *weight*.

        Coordinates outside the histogram edges are ignored.
        """
        indices = hf.get_bin_on_value(coord, self.edges)
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
        ind = indices[-1]
        # underflow
        if ind < 0:
            return

        # fill
        try:
            subarr[ind] += weight
        except IndexError:
            return

    def __repr__(self):
        return "histogram({}, bins={})".format(self.edges, self.bins)

    def scale(self, other=None, recompute=False):
        """Compute or set scale (integral of the histogram).

        If *other* is ``None``, return scale of this histogram.
        If its scale was not computed before,
        it is computed and stored for subsequent use
        (unless explicitly asked to *recompute*).
        Note that after changing (filling) the histogram
        one must explicitly recompute the scale
        if it was computed before.

        If a float *other* is provided, rescale self to *other*.

        Histograms with scale equal to zero can't be rescaled.
        :exc:`.LenaValueError` is raised if one tries to do that.
        """
        # see graph.scale comments why this is called simply "scale"
        # (not set_scale, get_scale, etc.)
        if other is None:
            # return scale
            if self._scale is None or recompute:
                self._scale = hf.integral(
                    *hf.unify_1_md(self.bins, self.edges)
                )
            return self._scale
        else:
            # rescale from other
            scale = self.scale()
            if scale == 0:
                raise lena.core.LenaValueError(
                    "can not rescale histogram with zero scale"
                )
            self.bins = lena.math.md_map(lambda binc: binc*float(other) / scale,
                                         self.bins)
            self._scale = other
            return None

    def _update_context(self, context):
        """Update *context* with the properties of this histogram.

        *context.histogram* is updated with "dim", "nbins"
        and "ranges" with values for this histogram.
        If this histogram has a computed scale, it is also added
        to the context.

        Called on "destruction" of the histogram structure (for example,
        in :class:`.ToCSV`). See graph._update_context for more details.
        """

        hist_context = {
            "dim": self.dim,
            "nbins": self.nbins,
            "ranges": self.ranges
        }

        if self._scale is not None:
            hist_context["scale"] = self._scale

        lena.context.update_recursively(context, {"histogram": hist_context})


class Histogram():
    """An element to produce histograms."""

    def __init__(self, edges, bins=None, make_bins=None, initial_value=0):
        """*edges*, *bins* and *initial_value* have the same meaning
        as during creation of a :class:`histogram`.

        *make_bins* is a function without arguments
        that creates new bins
        (it will be called during :meth:`__init__` and :meth:`reset`).
        *initial_value* in this case is ignored, but bin check is made.
        If both *bins* and *make_bins* are provided,
        :exc:`.LenaTypeError` is raised.
        """
        self._hist = histogram(edges, bins)

        if make_bins is not None and bins is not None:
            raise lena.core.LenaTypeError(
                "either initial bins or make_bins must be provided, "
                "not both: {} and {}".format(bins, make_bins)
            )

        # may be None
        self._initial_bins = copy.deepcopy(bins)

        # todo: bins, make_bins, initial_value look redundant
        # and may be reconsidered when really using reset().
        if make_bins:
            bins = make_bins()
        self._make_bins = make_bins

        self._cur_context = {}

    def fill(self, value):
        """Fill the histogram with *value*.

        *value* can be a *(data, context)* pair. 
        Values outside the histogram edges are ignored.
        """
        data, self._cur_context = lena.flow.get_data_context(value)
        self._hist.fill(data)
        # filling with weight is only allowed in histogram structure
        # self._hist.fill(data, weight)

    def compute(self):
        """Yield histogram with context."""
        yield (self._hist, self._cur_context)

    def reset(self):
        """Reset the histogram.

        Current context is reset to an empty dict.
        Bins are reinitialized with the *initial_value*
        or with *make_bins()* (depending on the initialization).
        """
        if self._make_bins is not None:
            self.bins = self._make_bins()
        elif self._initial_bins is not None:
            self.bins = copy.deepcopy(self._initial_bins)
        else:
            self.bins = hf.init_bins(self.edges, self._initial_value)

        self._cur_context = {}
