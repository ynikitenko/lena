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

    >>> # a one-dimensional histogram
    >>> hist = histogram([1, 2, 3])
    >>> hist.fill(1)
    >>> hist.bins
    [1, 0]
    >>> # a two-dimensional histogram
    >>> hist = histogram([[0, 1, 2], [0, 1, 2]])
    >>> hist.fill([0, 1])
    >>> hist.bins
    [[0, 1], [0, 0]]
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

    # Bad design: out_of_range and n_out_of_range should be consistent.
    # A user should not be allowed to create e.g. n_out_of_range = 1
    # and an empty out_of_range. Todo: maybe a simple check.
    # However, a user should not be generally allowed to create n_out_of_range
    # for a new histogram (only during a copy).

    def __init__(self, edges, bins=None, out_of_range=None, n_out_of_range=0):
        """*edges* is a sequence of one-dimensional arrays,
        each containing strictly increasing bin edges.
        *bins*, if not provided, are initialized with zeroes.

        A histogram bin can be any object that supports addition with
        *weight* during *fill* (if you plan to fill the histogram).
        See :func:`.init_bins` on how to create initial bins manually.

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

        .. admonition:: Developer's note

            one- and multidimensional histograms
            have different formats of *bins* and *edges*.
            For a better user experience, 1-dimensional edges are simply
            a list of x-edges, which is more intuitive,
            and also one-dimensional histograms are used more often.
            To be unified internally, 1-dimensional edges are nested
            into a list (like *[[1, 2, 3]]*).
            To unify 1- and multidimensional interfaces in your code,
            use :func:`.unify_1_md`.
        """
        # it is easier and more flexible to use created edges
        # than to complicate the interface here
        # like histogram(xlow, xmax, nbins,...)

        # it is fine that we have to kwarg no_check=False,
        # just to simplify interface.
        if bins is None:
            # otherwise we assume that we create histogram
            # from an existing one, and don't check its edges.
            hf.check_edges_increasing(edges)

        if hasattr(edges[0], "__iter__"):
            self.dim = len(edges)
            self._edges = edges
        else:
            self.dim = 1
            # unify 1- and multidimensional histograms internally
            self._edges = [edges]

        if bins is None:
            self.bins = hf.init_bins(self._edges, 0)
        else:
            self.bins = bins
            # a simple check along the first coordinate
            if len(bins) != len(self._edges[0]) - 1:
                raise LenaValueError(
                    "bins of incorrect shape given, {}".format(bins)
                )

        # out_of_range are implemented in Excel.
        # NumPy histograms don't have that, while ROOT
        # histograms have it too complicated (and mixed with
        # the histogram structure): 0th bin is underflow and
        # the last bin is overflow (now imagine those arrays
        # for multidimensional histograms).

        # In statistics an "outlier" is "a data point that differs
        # significantly from other observations", which is charged.
        # That is why we use a more neutral term "out_of_range".
        if out_of_range is None:
            out_of_range = [[0, 0] for _ in range(self.dim)]
            self._out_of_range = out_of_range
        elif self.dim == 1:
            # out of range is a list of two elements
            assert len(out_of_range) == 2
            self._out_of_range = [out_of_range]
        else:
            # out of range is a list of two-element lists
            assert all(len(oor) == 2 for oor in out_of_range)
            self._out_of_range = out_of_range
        self.n_out_of_range = n_out_of_range

    # emulating numeric types
    def __add__(self, other, edges_abs_tol=0.0, edges_rel_tol=1e-9):
        """Add a histogram *other* to this one.

        For each bin, the corresponding bin of *other* is added.

        Histograms must have the same edges.
        They are compared approximately using :func:`math.isclose`
        with *edges_abs_tol* and *edges_rel_tol* tolerance levels.
        Use :meth:`__sub__` for subtraction.
        """
        if not isinstance(other, histogram):
            raise LenaTypeError("other must be a histogram")
        # check that the edges coincide
        if not isclose(self._edges, other._edges,
                       abs_tol=edges_abs_tol, rel_tol=edges_rel_tol):
            raise LenaValueError("can not add histograms with different edges")

        obins = other.bins
        oout_of_range = other.out_of_range
        new_bins = md_map(add, self.bins, obins)

        new_noorange = self.n_out_of_range + other.n_out_of_range
        new_oorange = md_map(add, self.out_of_range, oout_of_range)

        # maybe todo: edges should be immutable
        new_hist = histogram(
            edges=copy.deepcopy(self._edges), bins=new_bins,
            n_out_of_range=new_noorange, out_of_range=new_oorange
        )

        return new_hist

    def __mul__(self, num):
        r"""Multiply bins by *num* and return a new histogram.

        Number of events outside of histogram range are also rescaled.

        A histogram should be multiplied on the right,
        *hist2 = hist \* 2*.
        An inplace multiplication with \*= is also allowed.
        """
        new_bins = lena.math.md_map(
            lambda binc: binc*num, self.bins
        )
        new_out_of_range = lena.math.md_map(
            lambda binc: binc*num, self.out_of_range
        )
        nnoor = self.n_out_of_range * num
        return histogram(copy.deepcopy(self.edges), new_bins, out_of_range=new_out_of_range, n_out_of_range=nnoor)

    def __sub__(self, other, edges_abs_tol=0.0, edges_rel_tol=1e-9):
        """Subtract *other* from this histogram and return the result.

        See :meth:`__add__` on keyword arguments.
        """
        return self.__add__(other*(-1), edges_abs_tol, edges_rel_tol)

    # read-only attributes to unify 1- and multidimensional histograms
    @property
    def edges(self):
        if self.dim == 1:
            return self._edges[0]
        return self._edges

    @property
    def out_of_range(self):
        if self.dim == 1:
            return self._out_of_range[0]
        return self._out_of_range

    def __eq__(self, other, abs_tol=0.0, rel_tol=1e-9):
        """Two histograms are equal, if and only if they have
        equal bins, edges and numbers of outliers.

        Note that floating numbers are compared
        approximately using :func:`math.isclose`.
        """
        if not isinstance(other, histogram):
            # in Python comparison between different types is allowed
            return False
        # everything is compared approximately,
        # even n_out_of_range because of possible weights
        isclose_ = lambda a, b: isclose(
            a, b, abs_tol=abs_tol, rel_tol=rel_tol
        )
        return (isclose_(self.bins, other.bins) and
                isclose_(self._edges, other._edges) and
                isclose_(self._out_of_range, other._out_of_range) and
                isclose_(self.n_out_of_range, other.n_out_of_range))
        # return (self.bins == other.bins and
        #         self._edges == other._edges and
        #         self._out_of_range == other._out_of_range and
        #         self.n_out_of_range == other.n_out_of_range)
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
                self._out_of_range[coord_ind][0] += weight
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
                    self._out_of_range[coord_ind][1] += weight
                    oor = True
                    subarr = subarr[0]

        ind = indices[-1]
        coord_ind += 1
        # underflow
        if ind < 0:
            self._out_of_range[coord_ind][0] += weight
            oor = True
        # overflow
        if ind >= len(subarr):
            self._out_of_range[coord_ind][1] += weight
            oor = True

        if oor:
            self.n_out_of_range += weight
            return

        ## filling the found bin ##
        subarr[ind] += weight

    def get_n_events(self):
        """Return number of events in the histogram (with weights).

        If the histogram was filled N times (with weights w_i),
        return N (sum of w_i).
        To get events outside of the histogram range,
        use :attr:`n_out_of_range`.
        """
        # An event in probability theory is a subset
        # of all possible outcomes.
        # For a histogram it is filling a specific bin.
        # See Wikipedia: Outcome (probability).
        bin_contents = (val[1] for val in hf.iter_bins(self.bins))
        return sum(bin_contents)

    def get_scale(self):
        """Calculate integral of the histogram.

        The integral (area under the histogram) is the sum
        of bin contents multiplied by bin size.
        """
        return hf.integral(self.bins, self._edges)

    def __repr__(self):
        # give a useful representation for the user to spot
        # right from the flow whether a histogram has many outliers.
        app = ""
        if self.n_out_of_range:
            app = ", out_of_range={}, n_out_of_range={}".format(
                self.out_of_range, self.n_out_of_range
            )
        return "histogram({}, bins={}".format(
            self.edges, self.bins
        ) + app + ")"

    def scale_to(self, other):
        """Return a histogram rescaled to *other*.

        *other* must be a number or a structure
        with a get_scale() method.

        If outliers should be taken into account, use
        :attr:`n_out_of_range` and the multiplication operator directly.

        Histograms with scale equal to zero can not be rescaled,
        or :exc:`.LenaValueError` is raised.
        """
        # Of course, get_scale(scale_to(a)) is a.
        # On including events out of histogram range:
        # For example, suppose we know the estimated number of events
        # for the signal and the background, and our histograms
        # have range encompassing only a part of data.
        # Then if we want to plot these two histograms together
        # scaled to the real number of events, we should take
        # into account the efficiencies of each histogram,
        # that is set *include_out_of_range* to ``True``.
        # On the other hand, let us have two spectra in the given range
        # and the data containing both of them. We fit the signals
        # to the data and get their relative contributions in that region.
        # After that we scale the histograms to those numbers of events
        # with *include_out_of_range* set to ``False`` (default).

        # we call this method scale_to, because this way it is clear
        # that we don't change the *other*
        # (compared to hist.scale(other)).

        scale = float(self.get_scale())
        if scale == 0:
            raise LenaValueError(
                "can not rescale histogram with zero scale"
            )
        if hasattr(other, "get_scale"):
            oscale = other.get_scale()
            mul = float(oscale) / scale
        else:
            # other is a number
            try:
                mul = float(other) / scale
            except TypeError:
                raise LenaTypeError("other must be a number "
                                    "or a structure with a get_scale() method")
        return self * mul

    def _update_context(self, context):
        """Update *context* with the properties of this histogram.

        *context.histogram* is updated with "dim", "nbins"
        and "ranges" with values for this histogram.

        Called on destruction of the histogram structure (for example,
        in when converting it to a CSV text).
        See also graph._update_context.
        """
        # this docstring is not openly published
        # and this method is private.

        # the fewer instance attributes we have,
        # the better it is for pickling.
        ranges = [(axis[0], axis[-1]) for axis in self._edges]
        nbins  = [len(axis) - 1 for axis in self._edges]
        if self.dim == 1:
            ranges = ranges[0]
            nbins  = nbins[0]

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

    def __init__(self, edges, bins=None, make_bins=None):
        """*edges* and *bins* have the same meaning
        as during creation of a :class:`histogram`.

        *make_bins* is a function without arguments
        that creates new bins if provided
        (it will be called during :meth:`__init__` and :meth:`reset`),
        bin check is made.
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
            self.bins = hf.init_bins(self.edges, 0)

        self._cur_context = {}
