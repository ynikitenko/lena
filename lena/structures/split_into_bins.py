"""Split analysis into groups defined by bins."""
import copy
import itertools

import lena.context
import lena.core
import lena.flow
import lena.math
import lena.structures
import lena.variables
from .hist_functions import (
    cell_to_string, get_example_bin, iter_bins_with_edges
)


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

            for histc, bin_edges in iter_bins_with_edges(data.bins,
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

    This class can be used when histogram bins
    contain complex structures.
    For example, in order to plot a histogram
    with a 3-dimensional vector in each bin, one can create 3 histograms
    corresponding to the vector's components.
    """

    def __init__(self, seq, select_bins=True, drop_bins_context=True):
        """*seq* is a sequence or an element applied to bin contents.
        If *seq* is not a :class:`.Sequence`
        or an element with *run* method, it is converted to a
        :class:`.Sequence`.
        Example: ``seq=Split([X(), Y(), Z()])``
        (provided that you have X, Y, Z variables).

        If *select_bins* applied to histogram bins is ``True``
        (tested on an arbitrary bin), the histogram is transformed.
        Bin types can be given in a ``list``
        or as a general :class:`.Selector`.
        For example, ``select_bins=[lena.math.vector3, list]``
        selects histograms where bins are vectors or lists.
        By default all histograms are accepted.

        :class:`.MapBins` creates histograms
        that may be plotted, because their bins contain only data
        without context.
        If *drop_bins_context* is ``False``, context remains in bins.
        By default, context of all histogram bins is discarded.
        This discourages compositions of :class:`.MapBins`:
        make compositions of their internal sequences instead.

        In case of incorrect arguments,
        :exc:`.LenaTypeError` is raised.
        """
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

        if not isinstance(select_bins, lena.flow.Selector):
            try:
                select_bins = lena.flow.Selector(select_bins)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "select_bins must be convertible to a Selector, "
                    "{} given".format(select_bins)
                )
        self._select_bins = select_bins

        self._drop_bins_context = bool(drop_bins_context)

    def run(self, flow):
        """Transform histograms from *flow*.

        *context.value* is updated with bin context (if that exists).
        It is assumed that all bins have the same context
        (because they were produced by the same sequence),
        therefore an arbitrary bin is taken
        and contexts of all other bins are ignored.

        Not selected values pass unchanged.
        """
        for val in flow:
            hist, context = lena.flow.get_data_context(val)
            update_nested = lena.context.update_nested

            # histograms are selected
            if not isinstance(hist, lena.structures.histogram):
                yield val
                continue

            # bin content is selected
            bin_ = get_example_bin(hist)
            if not self._select_bins(bin_):
                # no transformation needed
                yield val
                continue

            # bins are be transformed
            # Several iterations can happen, in principle.
            generators = _MdSeqMap(
                lambda cell: copy.deepcopy(self._seq).run([cell]),
                hist.bins
            )
            for new_bins in generators:
                if self._drop_bins_context:
                    new_data = lena.math.md_map(lena.flow.get_data, new_bins)
                else:
                    # leave context in bins
                    new_data = new_bins
                # deep copy, or make histogram.edges immutable
                edges = copy.deepcopy(hist.edges)
                new_hist = lena.structures.histogram(edges, new_data)

                ## update context
                new_context = copy.deepcopy(context)
                # no compositions of variables, because
                # there is no composition between edges'
                # and bins' transformations
                # (all common compositions are already counted)
                bin_context = copy.deepcopy(
                    lena.flow.get_context(get_example_bin(new_bins))
                )
                # instead of having SIB context in histogram,
                # it moved it to the histogram in this element!
                # hist_context = sib_context.get("histogram", {})
                # if hist_context:
                #     lena.context.update_nested(
                #         "histogram", context, copy.deepcopy(hist_context)
                #     )

                # we name it "value" and hope to have the same name
                # for graph values.
                if bin_context:
                    update_nested("value", new_context, bin_context)

                # one might optimise copying of the context here,
                # but we leave it like this (because it had bugs)
                yield (new_hist, new_context)


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
        # deep copy, because internal sequences may modify context
        # This is inefficient,
        # because only context of the last value is needed
        # todo: create a method _fill_data,
        # and fill with context only for the last time
        context = copy.deepcopy(context)
        bin_index = lena.structures.get_bin_on_value(self._arg_func(data),
                                                     self.edges)
        # we fill it manually, because histogram.fill does
        # subarr[ind] += weight
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
        # no copy, because cur_context is copied during fill()
        cur_context = self._cur_context
        # cur_context = copy.deepcopy(self._cur_context)
        # update context.variable
        self._arg_var._update_context(cur_context,
                                      copy.deepcopy(self._arg_var.var_context))

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

            yield (hist, copy.deepcopy(cur_context))
