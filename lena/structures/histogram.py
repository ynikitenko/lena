"""Histogram structure *histogram* and element *Histogram*."""
import copy
from operator import add

import lena.context
from lena.core import LenaValueError, LenaTypeError
import lena.flow
import lena.math
from lena.math import md_map
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

        :attr:`n_out_of_range` is the number of entries filled
        outside the range of the histogram.

        :attr:`overflow` and :attr:`underflow` for a one-dimensional
        histogram are numbers of events above the highest
        (respectively, below the lowest) edges range.
        :attr:`n_out_of_range` is equal to the sum of
        :attr:`overflow` and :attr:`underflow` in that case.
        All these attributes are rescaled together with histogram bins
        during :meth:`set_nevents` and :meth:`scale`.
        For multidimensional histograms overflows and underflows
        are rarely used, and for efficiency reasons they are counted
        only for the last coordinate.

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

        # number of values filled outside of the histogram range.
        self.n_out_of_range = 0
        # useful only for a one-dimensional histogram.
        # Implemented that only because people on the internet
        # regularly ask about that (and Excel has it).
        # NumPy histograms don't have this logic, while ROOT
        # histograms have it too complicated (and mixed with
        # the histogram structure): 0th bin is underflow and
        # the last bin is overflow (now imagine those arrays
        # for multidimensional histograms).
        self.overflow = 0
        self.underflow = 0

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
            wrong_bins_error = LenaValueError(
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

    def add(self, other, weight=1):
        """Add a histogram *other* to this one.

        For each bin, the corresponding bin of *other*
        is added. It can be multiplied with *weight*.
        For example, to subtract *other*, use *weight* -1.

        Histograms must have the same edges.
        Note that floating numbers should be compared
        approximately (using :func:`math.isclose`).
        """
        if not isinstance(other, histogram):
            raise LenaTypeError("other must be a histogram")
        # For now we make a complete check.
        # # A simple check on their edges range and shape is performed.
        # # More sophisticated tests can be implemented by user.
        if self.edges != other.edges:
            raise LenaValueError("can not add histograms with different edges")

        if weight != 1:
            obins = md_map(lambda val: val*weight, other.bins)
        else:
            obins = other.bins
        new_bins = md_map(add, self.bins, obins)

        # self.bins = new_bins
        # functional approach, easier testing
        # (we have produced new bins anyway)
        new_hist = histogram(edges=copy.deepcopy(self.edges), bins=new_bins)

        # this definition might be misleading, because
        # if *self* had N overflow and *other* had N underflow,
        # new n_out_of_range would be zero, which does not mean
        # that all values fell into the histogram range
        # (in fact, 2N missed that).
        # This should be considered a histogram *new*, such that
        # *other* + *new* = *self* .
        new_oorange = self.n_out_of_range + other.n_out_of_range * weight
        new_hist.n_out_of_range = new_oorange
        new_hist.overflow = self.overflow + other.overflow * weight
        new_hist.underflow = self.underflow + other.underflow * weight

        return new_hist

    def __eq__(self, other):
        """Two histograms are equal, if and only if they have
        equal bins, edges and number of events outside of range.

        If *other* is not a :class:`.histogram`, return ``False``.

        Note that floating numbers should be compared
        approximately (using :func:`math.isclose`).
        """
        if not isinstance(other, histogram):
            # in Python comparison between different types is allowed
            return False
        return (self.bins == other.bins and self.edges == other.edges
                and self.overflow == other.overflow
                and self.underflow == other.underflow
                and self.n_out_of_range == other.n_out_of_range)
        # comparing n_out_of_range may seem redundant. However,
        # 1) it increases histogram cohesion. All attributes
        #    are important.
        # 2) the probability that when we fill with different data
        #    and get same bin content, but different n_out_of_range
        #    is very low.
        # For practical applications in Lena (comparing two sequences
        # before initialization) this is not important (it should be 0).

    def fill(self, coord, weight=1):
        """Fill histogram at *coord* with the given *weight*.

        Coordinates outside the histogram edges are ignored.
        """
        indices = hf.get_bin_on_value(coord, self.edges)
        subarr = self.bins
        for ind in indices[:-1]:
            # underflow
            if ind < 0:
                # we don't fill self.underflow here,
                # because an underflow for one coordinate
                # can be an overflow for another (later one)
                self.n_out_of_range += weight
                return
            try:
                ## finding the bin ##
                subarr = subarr[ind]
            # overflow
            except IndexError:
                self.n_out_of_range += weight
                return

        ind = indices[-1]
        # underflow
        if ind < 0:
            self.n_out_of_range += weight
            self.underflow += weight
            return

        try:
            ## filling the found bin ##
            subarr[ind] += weight
        except IndexError:
            self.n_out_of_range += weight
            self.overflow += weight
            return

    def get_nevents(self, include_out_of_range=False):
        """Return number of entries in the histogram.

        If the histogram was filled N times, return N.
        If the histogram was filled with weights w_i,
        return the sum of w_i.
        Values filled outside the histogram range
        are not counted unless *include_out_of_range* is ``True``.
        """
        # An event in probability theory is a subset
        # of all possible outcomes.
        # For a histogram it is filling a specific bin.
        # See Wikipedia: Outcome (probability).
        bin_contents = (val[1] for val in hf.iter_bins(self.bins))
        n_in_range = sum(bin_contents)

        if include_out_of_range:
            return n_in_range + self.n_out_of_range
        return n_in_range

    def set_nevents(self, nevents, include_out_of_range=False):
        """Scale histogram bins to contain *nevents*.

        *include_out_of_range* adds :attr:`n_out_of_range`
        to the estimated number of entries to be rescaled.
        For example, suppose we know the estimated number of events
        for the signal and the background, and our histograms
        have range encompassing only a part of data.
        Then if we want to plot these two histograms together
        scaled to the real number of events, we should take
        into account the efficiencies of each histogram,
        that is set *include_out_of_range* to ``True``.
        On the other hand, let us have two spectra in the given range
        and the data containing both of them. We fit the signals
        to the data and get their relative contributions in that region.
        After that we scale the histograms to those numbers of events
        with *include_out_of_range* set to ``False`` (default).
        In both examples :attr:`n_out_of_range` is scaled together
        with the histogram bins.

        Rescaling a histogram with zero entries raises a
        :exc:`.LenaValueError`.
        """
        old_nevents = self.get_nevents(
            include_out_of_range=include_out_of_range
        )
        if not old_nevents:
            raise LenaValueError(
                "can not rescale a histogram containing zero events"
            )
        scale = float(nevents/old_nevents)

        self.n_out_of_range *= scale
        self.overflow  *= scale
        self.underflow *= scale

        if scale == int(scale):
            scale = int(scale)
        self.bins = lena.math.md_map(
            lambda binc: binc*scale, self.bins
        )

    def __repr__(self):
        # n_out_of_range is not here,
        # because it is not used during __init__ .
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
                # since scale is an integral,
                # we can't take n_out_of_range into account
                # (it has bins of infinite length).
                self._scale = hf.integral(
                    *hf.unify_1_md(self.bins, self.edges)
                )
            return self._scale
        else:
            # rescale from other
            scale = self.scale()
            if scale == 0:
                raise LenaValueError(
                    "can not rescale histogram with zero scale"
                )
            self.bins = lena.math.md_map(lambda binc: binc*float(other) / scale,
                                         self.bins)
            self.n_out_of_range *= other/scale
            self.overflow  *= other/scale
            self.underflow *= other/scale
            self._scale = other
            return None

    def _update_context(self, context):
        """Update *context* with the properties of this histogram.

        *context.histogram* is updated with "dim", "nbins"
        and "ranges" with values for this histogram.

        Called on destruction of the histogram structure (for example,
        in when converting it to a CSV text).
        See also graph._update_context.
        """
        # actually this docstring is not openly published.
        # And this method is private.

        hist_context = {
            "dim": self.dim,
            "nbins": self.nbins,
            "n_out_of_range": self.n_out_of_range,
            "overflow": self.overflow,
            "underflow": self.underflow,
            "ranges": self.ranges,
        }

        # bad design. Context should not depend on
        # whether the scale was computed before or not.
        # A scale is important (also to be consistent with graphs),
        # but much less so after the histogram had been destroyed.
        # if self._scale is not None:
        #     hist_context["scale"] = self._scale

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
            raise LenaTypeError(
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
