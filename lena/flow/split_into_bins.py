"""Split analysis into groups defined by bins."""
import copy
import itertools

import lena.context
import lena.core
import lena.flow
import lena.math
import lena.structures
import lena.variables


def _iter_bins_with_edges(bins, edges):
    """Yield *(bin content, bin edges)* pairs.

    *Bin edges* is a tuple, such that at index *i*
    its element is bin's *(lower bound, upper bound)*
    along *i*-th the coordinate.
    """
    # todo: only a list or also a tuple, an array?
    if not isinstance(edges[0], list):
        edges = [edges]
    bins_sizes = [len(edge)-1 for edge in edges]
    indices = [list(range(nbins)) for nbins in bins_sizes]
    for index in itertools.product(*indices):
        bin_ = lena.structures.get_bin_on_index(index, bins)
        edges_low = []
        edges_high = []
        for var, var_ind in enumerate(index):
            edges_low.append(edges[var][var_ind])
            edges_high.append(edges[var][var_ind+1])
        yield (bin_, tuple(zip(edges_low, edges_high)))
        # old interface:
        # yield (bin_, (edges_low, edges_high))


class _MdSeqMap(object):
    """Multidimensional mapping of a *Sequence*."""

    def __init__(self, generator, array):
        """*generator* is mapped to *array*'s contents.
        Example when a bin is a sequence:
        ``generator=lambda cell: cell.compute()``.
        """
        self._generators = lena.math.md_map(generator, array)
        # self._arr = arr
        #, self.bins)

    def next(self):
        # Python 2
        return lena.math.md_map(next, self._generators)

    def __next__(self):
        # Python 3
        return self.next()

    def __iter__(self):
        return self


def cell_to_string(
        cell_edges, var_context=None, coord_names=None,
        coord_fmt="{}_lte_{}_lt_{}", coord_join="_", reverse=False):
    """Transform cell edges into a string.

    *cell_edges* is a tuple of pairs *(lower bound, upper bound)*
    for each coordinate.

    *coord_names* is a list of coordinates names.

    *coord_fmt* is a string,
    which defines how to format individual coordinates.

    *coord_join* is a string, which joins coordinate pairs.

    If *reverse* is True, coordinates are joined in reverse order.
    """
    # todo: do we really need var_context?
    # todo: even if so, why isn't that a {}? Is that dangerous?
    if coord_names is None:
        if var_context is None:
            coord_names = [
                "coord{}".format(ind) for ind in range(len(cell_edges))
            ]
        else:
            if "combine" in var_context:
                coord_names = [var["name"]
                               for var in var_context["combine"]]
            else:
                coord_names = [var_context["name"]]
    if len(cell_edges) != len(coord_names):
        raise lena.core.LenaValueError(
            "coord_names must have same length as cell_edges, "
            "{} and {} given".format(coord_names, cell_edges)
        )
    coord_strings = [coord_fmt.format(edge[0], coord_names[ind], edge[1])
                     for (ind, edge) in enumerate(cell_edges)]
    if reverse:
        coord_strings = reversed(coord_strings)
    coord_str = coord_join.join(coord_strings)
    return coord_str


def get_example_bin(struct):
    """Return bin with zero index on each axis of the histogram bins.

    For example, if the histogram is two-dimensional, return hist[0][0].

    *struct* can be a :class:`.histogram`
    or an array of bins.
    """
    if isinstance(struct, lena.structures.histogram):
        return lena.structures.get_bin_on_index([0] * struct.dim, struct.bins)
    else:
        bins = struct
        while isinstance(bins, list):
            bins = bins[0]
        return bins


class IterateBins(object):
    """Iterate bins of histograms."""

    def __init__(self, create_edges_str=None, select_bins=None):
        """*create_edges_str* is a callable
        that creates a string from bin's edges
        and coordinate names and adds that to the context.
        It is passed parameters *(edges, var_context)*,
        where *var_context* is *variable* context containing
        variable names (it can be a single
        :class:`.Variable` or :class:`.Combine`).
        By default it is :func:`.cell_to_string`.

        *select_bins* is a callable used to test bin contents.
        By default, only those histograms are iterated where
        bins contain histograms. Use *select_bins* to choose other classes.
        See :class:`.Selector` for examples.

        If *create_edges_str* is not callable,
        :exc:`.LenaTypeError` is raised.
        """
        if create_edges_str is None:
            # default
            create_edges_str = cell_to_string
        elif not callable(create_edges_str):
            raise lena.core.LenaTypeError(
                "create_edges_str must be callable, "
                "{} provided".format(create_edges_str)
            )
        self._create_edges_str = create_edges_str

        # todo: create a selector for bins
        # (example bins or some iterable)
        if select_bins is None:
            # select if bins contain histograms
            self._select_bins = lena.flow.Selector(lena.structures.histogram)
        else:
            self._select_bins = lena.flow.Selector(select_bins)

    def run(self, flow):
        """Yield histogram bins one by one.

        For each :class:`.histogram` from the *flow*,
        if its bins pass *select_bins*, they are iterated.

        The resulting context is taken from bin's context.
        Histogram's context is preserved in *context.bins*.
        *context.bin* is updated with
        "edges" (with bin edges) and "edges_str" (their representation).
        If histogram's context contains *variable*, that is used for
        edges' representation.

        Not histograms pass unchanged.
        """
        update_nested = lena.context.update_nested
        for val in flow:
            data, hist_context = lena.flow.get_data_context(val)
            # select histograms
            if not isinstance(data, lena.structures.histogram):
                yield val
                continue
            # bins also contain histograms
            data00 = lena.flow.get_data(get_example_bin(data))
            if not self._select_bins(data00):
                yield val
                continue

            for histc, bin_edges in _iter_bins_with_edges(data.bins,
                                                          data.edges):
                hist, bin_context = lena.flow.get_data_context(histc)
                # we assume that context.variable corresponds to
                # the variable used for bins.
                # If that is some old variable left in the context,
                # remove that first! Anyway SplitIntoBins would create
                # its correct variable (if called before this element).
                split_var_context = lena.context.get_recursively(
                    hist_context, "variable", None
                )
                # split_var_context is not modified here.
                edges_str = self._create_edges_str(
                    bin_edges, var_context=split_var_context
                )
                context_bin = {"edges": bin_edges, "edges_str": edges_str}

                # bin_context is main analysis context.
                # Update it with the surrounding histogram context.
                # It will have some duplication, but a complete copy
                # is needed, because it can be different in general.
                update_nested("bins", bin_context, copy.deepcopy(hist_context))
                # Bin position details are in *context.bin*
                update_nested("bin", bin_context, context_bin)
                yield (hist, bin_context)


class MapBins(object):
    """Transform bin content of histograms.

    This class is used when histogram bins contain complex structures.
    For example, in order to plot a histogram
    with a 3-dimensional vector in each bin,
    we shall create 3 histograms corresponding to vector's components.
    """

    def __init__(self, select, seq, drop_bins_context=True):
        """*Select* determines which types should be transformed.
        The types must be given in a ``list`` (not a tuple)
        or as a general :class:`.Selector`.
        Example: ``select=[lena.math.vector3, list]``.

        *seq* is a *Sequence* or element applied to bin contents.
        If *seq* is not a :class:`.Sequence`
        or an element with *run* method, it is converted to a
        :class:`.Sequence`.
        Example: ``seq=Split([X(), Y(), Z()])``
        (provided that you have X, Y, Z variables).

        :class:`.MapBins` creates histograms
        that may be plotted, and their bins contain only data
        without context.
        By default, context of all bins except one is not used.
        If *drop_bins_context* is ``False``, a histogram of
        bin context is added to context.

        In case of wrong arguments,
        :exc:`.LenaTypeError` is raised.
        """
        if not isinstance(select, lena.flow.Selector):
            try:
                select = lena.flow.Selector(select)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "select must be convertible to a Selector, "
                    "{} given".format(select)
                )
        self._selector = select

        if not lena.core.is_run_el(seq):
            try:
                seq = lena.core.Sequence(seq)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "seq must be a Sequence or convertible to that, "
                    "or an element with run method; "
                    "{} provided".format(seq)
                )
        self._seq = seq
        self._drop_bins_context = bool(drop_bins_context)

    def run(self, flow):
        """Transform histograms from *flow*.

        Not selected values pass unchanged.

        Context is updated with *variable*, *histogram*
        and *bin_content*.
        *variable* and *histogram* copy context from *split_into_bins*
        (if present there).
        *bin_content* includes context for example bin in *example_bin*
        and (optionally) for all bins in *all_bins*.
        """
        for value in flow:
            hist, context = lena.flow.get_data_context(value)
            # data part must be a histogram
            if not isinstance(hist, lena.structures.histogram):
                yield value
                continue
            val = get_example_bin(hist)
            # value must be selected
            ## types are checked against data part of the bin
            if not self._selector(val):
                # no transformation needed
                yield value
                continue
            # bins should be transformed.
            # Several iterations can happen, in principle.
            generators = _MdSeqMap(
                lambda cell: copy.deepcopy(self._seq).run([cell]),
                hist.bins
            )
            for new_bins in generators:
                new_data = lena.math.md_map(lena.flow.get_data, new_bins)
                ana_context = copy.deepcopy(
                    lena.flow.get_context(get_example_bin(new_bins))
                )
                cur_bin_context = {"example_bin": ana_context}
                if not self._drop_bins_context:
                    all_new_context = lena.math.md_map(
                        lena.flow.get_context, new_bins
                    )
                    cur_bin_context["all_bins"] = all_new_context
                sib_context = context.get("split_into_bins", {})
                var_context = ana_context.get("variable", {})
                hist_context = sib_context.get("histogram", {})
                # todo: why explicitly these contexts?
                # What other contexts could be updated?
                if var_context:
                    # this ugly fix should be avoided:
                    # variable.compose must be changed to variable.variable,
                    # so that update_nested always works directly.
                    # if "variable" in context:
                    #     cvar = context["variable"]
                    #     key = "compose"
                    # else:
                    #     cvar = context
                    #     key = "variable"
                    #
                    # todo: unify variable.variable and variable.compose
                    lena.context.update_nested(
                        "variable", context, copy.deepcopy(var_context)
                        # key, cvar, copy.deepcopy(var_context)
                    )
                if hist_context:
                    lena.context.update_nested(
                        "histogram", context, copy.deepcopy(hist_context)
                    )
                lena.context.update_nested("bin_content", context, cur_bin_context)
                # or make histogram.edges immutable
                edges = copy.deepcopy(hist.edges)
                new_hist = lena.structures.histogram(edges, new_data)
                # one might optimise copying of the context here,
                # but for now we leave it like this (because it had bugs)
                yield (new_hist, copy.deepcopy(context))


class SplitIntoBins():
    """Split analysis into groups defined by bins."""

    def __init__(self, seq, arg_var, edges):
        """*seq* is a :class:`.FillComputeSeq` sequence
        (or will be converted to that)
        that corresponds to the analysis being performed
        for different bins.
        Deep copy of *seq* is done for each bin.

        *arg_var* is a :class:`.Variable` that takes data
        and returns value used to compute the bin index.
        Example of a two-dimensional function:
        ``arg_var = lena.variables.Variable("xy",
        lambda event: (event.x, event.y))``.

        *edges* is a sequence of arrays containing
        monotonically increasing bin edges along each dimension.
        Example: ``edges = lena.math.mesh((0, 1), 10)``.

        Note
        ----
            The final histogram may contain vectors, histograms and
            any other data the analysis produced.
            To plot them, one can extract vector components with e.g.
            :class:`.MapBins`.
            If bin contents are histograms,
            they can be yielded one by one with :class:`.IterateBins`.

        **Attributes**: bins, edges.

        If *edges* are not increasing,
        :exc:`.LenaValueError` is raised.
        In case of other argument initialization problems,
        :exc:`.LenaTypeError` is raised.
        """

        if not isinstance(seq, lena.core.FillComputeSeq):
            try:
                seq = lena.core.FillComputeSeq(seq)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "seq must contain a FillCompute element, "
                    "{} provided".format(seq)
                )

        if isinstance(arg_var, lena.variables.Variable):
            self._arg_var = arg_var
            self._arg_func = arg_var.getter
        else:
            raise lena.core.LenaTypeError(
                "arg_var must be a Variable, "
                "{} provided.".format(arg_var)
            )

        # may raise LenaValueError
        lena.structures.check_edges_increasing(edges)

        self.bins = lena.structures.init_bins(edges, seq, deepcopy=True)
        self.edges = edges
        self._cur_context = {}

    def fill(self, val):
        """Fill the cell corresponding to *arg_var(val)* with *val*.

        Values outside the :attr:`edges` are ignored.
        """
        data, context = lena.flow.get_data_context(val)
        bin_index = lena.structures.get_bin_on_value(self._arg_func(data),
                                                     self.edges)
        subarr = self.bins
        for ind in bin_index:
            # underflow
            if ind < 0:
                return
            try:
                subarr = subarr[ind]
            # overflow
            except IndexError:
                return
        # subarr is now the cell self.edges[bin_index]
        subarr.fill(val)
        self._cur_context = context

    def compute(self):
        """Yield a *(histogram, context)* pair for each *compute()*
        for all bins.

        The :class:`.histogram` is created from :attr:`edges`
        with bin contents taken from *compute()* for :attr:`bins`.
        Computational context is preserved in histogram's bins.

        :class:`.SplitIntoBins` adds context
        as *histogram* (corresponding to :attr:`edges`)
        and *variable* (corresponding to *arg_var*) subcontexts.
        This allows unification of :class:`.SplitIntoBins`
        with common analysis using histograms and variables
        (useful when creating plots from one template).
        Old contexts, if exist,
        are preserved in nested subcontexts
        (that is *histogram.histogram* or *variable.variable*).

        Note
        ----
            In Python 3 the minimum number of *compute()*
            among all bins is used.
            In Python 2, if some bin is exhausted before the others,
            its content will be filled with ``None``.
        """
        # deep copy, because cur_context is shared with inner sequences
        cur_context = copy.deepcopy(self._cur_context)
        # update context.variable
        var = self._arg_var
        var._update_context(cur_context, var.var_context)

        # update histogram context
        _hist = lena.structures.histogram(self.edges, self.bins)
        # histogram context depends only on edges, not on data,
        # and is thus same for all results
        hist_context = lena.structures.hist_functions._make_hist_context(_hist)
        lena.context.update_nested("histogram", cur_context, hist_context)

        generators = _MdSeqMap(lambda cell: cell.compute(), self.bins)
        # generators = lena.math.md_map(lambda cell: cell.compute(), self.bins)
        while True:
            try:
                result = next(generators)
            except StopIteration:
                break
            # result = lena.math.md_map(next, generators)

            hist = lena.structures.histogram(self.edges, result)

            yield (hist, cur_context)
