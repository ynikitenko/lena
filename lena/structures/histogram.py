"""Histogram structure *histogram* and element *Histogram*."""
import copy
from operator import add

import lena.context
from lena.core import LenaValueError, LenaTypeError
import lena.flow
import lena.math
from lena.math import isclose, md_map
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

    def __init__(self, edges, bins=None, out_of_range=None, n_out_of_range=0,
                 initial_value=0):
        """*edges* is a sequence of one-dimensional arrays,
        each containing strictly increasing bin edges.
        *bins*, if not provided, are initialized with zeroes.

        .. deprecated:: 0.6
          create bins with the *initial_value* manually.

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

        :attr:`out_of_range` is a list of *dim* lists,
        each one corresponding to a coordinate.
        Each *out_of_range* sublist contains two items,
        the first one (index 0) for underflow, the second for overflow.

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

        ## useful only for a one-dimensional histogram.
        ## Implemented that only because people on the internet
        ## regularly ask about that (and Excel has it).
        ## NumPy histograms don't have this logic, while ROOT
        ## histograms have it too complicated (and mixed with
        ## the histogram structure): 0th bin is underflow and
        ## the last bin is overflow (now imagine those arrays
        ## for multidimensional histograms).
        # Removed because it does not help with the minimum and
        # maximum of the outliers. Hard to maintain generality
        # between 1 and multidimensional histograms if we have that.
        # self.overflow = 0
        # self.underflow = 0

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

        if out_of_range is None:
            out_of_range = [[0, 0] for _ in range(self.dim)]
        self.out_of_range = out_of_range
        self.n_out_of_range = n_out_of_range

    def add(self, other, weight=1, edges_abs_tol=0.0, edges_rel_tol=1e-9):
        """Add a histogram *other* to this one.

        For each bin, the corresponding bin of *other*
        is added. It can be multiplied with *weight*.
        For example, to subtract *other*, use *weight* -1.

        Histograms must have the same edges.
        They are compared approximately using :func:`math.isclose`
        with *edges_abs_tol* and *edges_rel_tol* tolerance levels.
        """
        if not isinstance(other, histogram):
            raise LenaTypeError("other must be a histogram")
        # check that their edges coincide.
        # The user can separately compare their edges if they
        # have different requirements.
        if not isclose(self.edges, other.edges,
                       abs_tol=edges_abs_tol, rel_tol=edges_rel_tol):
            raise LenaValueError("can not add histograms with different edges")

        if weight == 1:
            obins = other.bins
            oout_of_range = other.out_of_range
        else:
            obins = md_map(lambda val: val*weight, other.bins)
            oout_of_range = md_map(lambda val: val*weight, other.out_of_range)
        new_bins = md_map(add, self.bins, obins)

        # self.bins = new_bins
        # but we use functional approach
        # (we have produced new bins anyway)

        # note that if *self* had N overflow
        # and *other* had N underflow,
        # new n_out_of_range would be zero, which does not mean
        # that all values fell into the histogram range
        # (in fact, 2N missed that).
        # This should be considered a histogram *new*, such that
        # *other* + *new* = *self* .
        new_noorange = self.n_out_of_range + other.n_out_of_range * weight
        new_oorange = md_map(add, self.out_of_range, oout_of_range)

        # todo: edges should be immutable
        new_hist = histogram(
            edges=copy.deepcopy(self.edges), bins=new_bins,
            n_out_of_range=new_noorange, out_of_range=new_oorange
        )

        return new_hist

    def __eq__(self, other):
        """Two histograms are equal, if and only if they have
        equal bins, edges and numbers of outliers.

        If *other* is not a :class:`.histogram`, return ``False``.

        Note that floating numbers should be compared
        approximately (using :func:`math.isclose`).
        """
        # todo: introduce isclose here.
        if not isinstance(other, histogram):
            # in Python comparison between different types is allowed
            return False
        return (self.bins == other.bins and
                self.edges == other.edges and
                self.out_of_range == other.out_of_range and
                self.n_out_of_range == other.n_out_of_range)
        # comparing out_of_range may seem redundant. However,
        # 1) it increases histogram cohesion. All attributes
        #    are important. n_out_of_range is important for scaling.
        # 2) the probability that when we fill with different data
        #    and get same bin content, but different n_out_of_range
        #    is very low.
        # For practical applications in Lena (comparing two sequences
        # before initialization) this is not important (it should be 0).

    def fill(self, coord, weight=1):
        """Fill histogram at *coord* with the given *weight*.

        Coordinates outside the histogram edges
        are added to *n_out_of_range*.

        No additional accounting for weights is being done.
        For example, to calculate a sum of squares of weights like in ROOT,
        do it separately in parallel.
        """
        # `ROOT.TH1.GetSumw2() <https://root.cern.ch/doc/master/classTH1.html#ac79a1d40a4b33721a15e16d7cba4faaf>`_,
        indices = hf.get_bin_on_value(coord, self.edges)
        subarr  = self.bins
        oor = False
        # to be initialized correctly for 1d-histograms
        # if the cycle is not run.
        coord_ind = -1

        for coord_ind, ind in enumerate(indices[:-1]):
            # underflow
            if ind < 0:
                self.out_of_range[coord_ind][0] += weight
                oor = True
                # the exact index is no longer important,
                # for we won't fill anything more.
                subarr = subarr[0]
            else:
                try:
                    ## finding the bin ##
                    subarr = subarr[ind]
                # overflow
                except IndexError:
                    self.out_of_range[coord_ind][1] += weight
                    oor = True
                    subarr = subarr[0]

        ind = indices[-1]
        coord_ind += 1
        # underflow
        if ind < 0:
            self.out_of_range[coord_ind][0] += weight
            oor = True
        # overflow
        if ind >= len(subarr):
            self.out_of_range[coord_ind][1] += weight
            oor = True

        if oor:
            self.n_out_of_range += weight
            return

        ## filling the found bin ##
        subarr[ind] += weight

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

    # this function is wrong because n_out_of_range
    # is the number of entries outside the histogram range.
    # def get_n_out_of_range(self):
    #     """Get number of entries filled
    #     outside the range of the histogram.

    #     It is rescaled together with histogram bins
    #     during :meth:`set_nevents` and :meth:`scale`.
    #     """
    #     return sum(sum(coor) for coor in self.out_of_range)

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

        if scale == int(scale):
            scale = int(scale)
        self.bins = lena.math.md_map(
            lambda binc: binc*scale, self.bins
        )

    def __repr__(self):
        # give a useful representation for the user to spot
        # if a histogram has many outliers right from the flow.
        app = ""
        if self.n_out_of_range:
            app = ", out_of_range={}, n_out_of_range={}".format(
                self.out_of_range, self.n_out_of_range
            )
        return "histogram({}, bins={}".format(
            self.edges, self.bins, self.out_of_range
        ) + app + ")"

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

        # the fewer instance attributes we have,
        # the better it is for pickling.
        edges = self.edges
        if self.dim == 1:
            ranges = [(edges[0], edges[-1])]
            nbins = [len(edges)-1]
        else:
            ranges = [(axis[0], axis[-1]) for axis in edges]
            nbins =  [len(axis) - 1 for axis in edges]

        hist_context = {
            "dim": self.dim,
            "nbins": nbins,
            # we add out_of_range,
            # for it could be used during plotting
            "out_of_range": self.out_of_range,
            # even if it is zero, it is good to have it in context
            # for uniformity while plotting with others.
            "n_out_of_range": self.n_out_of_range,
            "ranges": ranges,
        }

        lena.context.update_recursively(context, {"histogram": hist_context})

        ## bad design. Context should not depend on
        ## whether the scale was computed before or not.
        ## A scale is important (also to be consistent with graphs),
        ## but much less so after the histogram had been destroyed.
        # if self._scale is not None:
        #     hist_context["scale"] = self._scale


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

        .. note::
            To allow weights, use :class:`.histogram` directly
            (not as an element).
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
