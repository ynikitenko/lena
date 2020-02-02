"""Split analysis on groups set by bins."""
from __future__ import print_function

import copy

import lena.context 
import lena.core
import lena.flow
import lena.math
import lena.structures
import lena.variables


def _iter_bins_with_edges(bins, edges):
    """Yield *(bin content, bin edges)* pairs.

    *Bin edges* is a tuple, such that at index *i*
    its element is bin's *(lower bound, upper bound)*,
    on *i*-th the coordinate.
    """
    if not isinstance(edges[0], list):
        edges = [edges]
    bins_sizes = [len(edge)-1 for edge in edges]
    index = [0] * len(edges)
    cur_ind = len(edges)-1
    zeroth_bin_yielded = False
    while cur_ind >= 0:
        var_ind = 0
        while var_ind < bins_sizes[cur_ind]:
            index[cur_ind] = var_ind
            bin_ = lena.structures.get_bin_on_index(index, bins)
            edges_low = []
            edges_high = []
            for i, cur_var in enumerate(index):
                edges_low.append(edges[i][cur_var])
                edges_high.append(edges[i][cur_var+1])
            if zeroth_bin_yielded is False or var_ind != 0:
                yield (bin_, tuple(zip(edges_low, edges_high)))
                # yield (bin_, (edges_low, edges_high))
                zeroth_bin_yielded = True
            var_ind += 1
        cur_ind -= 1


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


def cell_to_string(cell_edges, var_context=None, coord_names=None, 
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
    if coord_names is None:
        if var_context is None:
            coord_names = ["coord{}".format(ind) for ind in range(len(cell_edges))]
        else:
            if "combine" in var_context:
                coord_names = [var["name"]
                               for var in var_context["combine"]]
            else:
                coord_names = [var_context["name"]]
    if len(cell_edges) != len(coord_names):
        raise lena.core.LenaValueError(
            "coord_names must have same lenght as cell_edges, "
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

    *struct* can be a :class:`~lena.structures.Histogram`
    or an array of bins.
    """
    if isinstance(struct, lena.structures.Histogram):
        return lena.structures.get_bin_on_index([0] * struct.dim, struct.bins)
    else:
        bins = struct
        while isinstance(bins, list):
            bins = bins[0]
        return bins


class TransformBins(object):
    """Transform bins into a flattened sequence."""

    def __init__(self, create_edges_str=None):
        """*create_edges_str* is a callable, 
        which creates a string from bin's edges
        and coordinate names
        and adds that to context.
        It is passed parameters *(edges, var_context)*,
        where *var_context* is Variable context containing
        variable names (it can be a single
        :class:`~lena.variable.Variable`
        or :class:`~lena.variable.Combine`).
        
        By default, it is :func:`cell_to_string`.

        If *create_edges_str* is not callable,
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        if create_edges_str is None:
            # default
            pass
        elif not callable(create_edges_str):
            raise lena.core.LenaTypeError(
                "create_edges_str must be callable, "
                "{} provided".format(create_edges_str)
            )
        self._create_edges_str = create_edges_str

    def run(self, flow):
        for value in flow:
            data, context = (lena.flow.get_data(value),
                             lena.flow.get_context(value))
            if not isinstance(data, lena.structures.Histogram):
                yield value
                continue
            # data is a histogram
            # check bins
            data00 = lena.flow.get_data(get_example_bin(data))
            if not isinstance(data00, lena.structures.Histogram):
                yield value
                continue
            # bin is a histogram
            ## context is not shared, but yielded,
            ## so deep copy is not needed
            ## But in this case data can't be used twice!!
            # context = copy.deepcopy(context)
            for histc, bin_edges in _iter_bins_with_edges(data.bins, data.edges):
                hist, ana_context = (lena.flow.get_data(histc),
                                     lena.flow.get_context(histc))
                split_var = lena.context.get_recursively(
                    context, "split_into_bins.variable", None
                )
                if self._create_edges_str:
                    # use predefined function
                    edges_str = self._create_edges_str(bin_edges,
                                                       var_context=split_var)
                else:
                    # default
                    edges_str = cell_to_string(bin_edges,
                                               var_context=split_var)
                sib_context = context.pop("split_into_bins", {})
                # hide split_into_bins context into that.
                # this may be useful when context and ana_context differ
                sib_context["context"] = context
                bin_context = {"bin": {"edges": bin_edges,
                                       "edges_str": edges_str}}
                lena.context.update_nested(ana_context, {"split_into_bins": sib_context})
                lena.context.update_nested(ana_context, bin_context)
                yield (hist, ana_context)


class ReduceBinContent(object):
    """Transform bin content of histograms.

    This class is used when histogram bins contain complex structures.
    For example, in order to plot a histogram
    with a 3-dimensional vector in each bin,
    we shall create 3 histograms corresponding to vector's components.
    """

    def __init__(self, select, transform, drop_bins_context=True):
        """*Select* determines which types should be transformed.
        The types must be given in a ``list`` (not a tuple)
        or as a general :class:`Selector`.
        Example: ``select=[lena.math.vector3, list]``.

        *transform* is a *Sequence* or element applied to bin contents.
        If *transform* is not a :class:`~lena.core.Sequence`
        or an element with *run* method, it is converted to a 
        :class:`~lena.core.Sequence`.
        Example: ``transform=Split([X(), Y(), Z()])``
        (provided that you have X, Y, Z variables).

        :class:`ReduceBinContent` creates histograms,
        which may be plotted, that is bins contain only data
        without context.
        By default, context of all bins except one is not used.
        If *drop_bins_context* is ``False``, a histogram of 
        bin context is added to context.

        In case of wrong arguments,
        :exc:`~lena.core.LenaTypeError` is raised.
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

        if not lena.core.is_run_el(transform):
            try:
                transform = lena.core.Sequence(transform)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "transform must be a Sequence or convertible to that, "
                    "or an element with run method; "
                    "{} provided".format(transform)
                )
        self._transform = transform
        self._drop_bins_context = bool(drop_bins_context)

    def run(self, flow):
        """Transform histograms from *flow*.

        Not selected values pass unchanged.

        Context is updated with *variable*, *histogram*
        and *bin_content*.
        *variable" and *histogram* copy context from *split_into_bins*
        (if present there).
        *bin_content* includes context for example bin in "example_bin"
        and (optionally) for all bins in "all_bins".
        """
        for value in flow:
            hist, context = (lena.flow.get_data(value),
                             lena.flow.get_context(value))
            # data part must be a histogram
            if not isinstance(hist, lena.structures.Histogram):
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
                lambda cell: copy.deepcopy(self._transform).run([cell]), hist.bins
            )
            for new_bins in generators:
                new_data = lena.math.md_map(lena.flow.get_data, new_bins)
                ana_context = copy.deepcopy(
                    lena.flow.get_context(get_example_bin(new_bins))
                )
                cur_bin_context = {"bin_content": {"example_bin": ana_context}}
                if not self._drop_bins_context:
                    all_new_context = lena.math.md_map(
                        lena.flow.get_context, new_bins
                    )
                    cur_bin_context["bin_content"]["all_bins"] = all_new_context
                sib_context = context.get("split_into_bins", {})
                var_context = sib_context.get("variable", {})
                hist_context = sib_context.get("histogram", {})
                if var_context:
                    lena.context.update_nested(context, {"variable": var_context})
                if hist_context:
                    lena.context.update_nested(context, {"histogram": hist_context})
                lena.context.update_nested(context, cur_bin_context)
                # or make Histogram.edges immutable
                edges = copy.deepcopy(hist.edges)
                new_hist = lena.structures.Histogram(edges, new_data)
                yield (new_hist, context)


class SplitIntoBins(lena.core.FillCompute):
    """Split analysis into bins."""

    def __init__(self, seq, arg_func, edges, transform=None):
        """*seq* is a :class:`~lena.core.FillComputeSeq` sequence,
        which corresponds to the analysis being compared
        for different bins.
        It can be a tuple containing a *FillCompute* element.
        Deep copy of *seq* will be used to produce each bin's content.

        *arg_func* is a function which takes data
        and returns argument value used to compute the bin index.
        A :class:`~lena.variables.variable.Variable` must be provided.
        Example of a two-dimensional function:
        ``arg_func = lena.variables.Variable("xy",
        lambda event: (event.x, event.y))``.

        *edges* is a sequence of arrays containing
        monotonically increasing bin edges along each dimension.
        Example: ``edges = lena.math.mesh((0, 1), 10)``.

        *transform* is a :class:`~lena.core.Sequence`,
        which is applied to results.
        The final histogram may contain vectors, histograms and
        any other data the analysis produced. To be able to plot them,
        *transform* can extract vector components or do other work
        to simplify structures.
        By default, *transform* is :class:`TransformBins`. 
        Pass an empty tuple to disable it.

        **Attributes**: bins, edges.

        If *edges* are not increasing,
        :exc:`~lena.core.exceptions.LenaValueError` is raised.
        In case of other argument initialization problems, 
        :exc:`~lena.core.exceptions.LenaTypeError` is raised.
        """
        if not isinstance(seq, lena.core.FillComputeSeq):
            try:
                seq = lena.core.FillComputeSeq(seq)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "seq must contain a FillCompute element, "
                    "{} provided".format(seq)
                )
        if isinstance(arg_func, lena.variables.Variable):
            self._arg_var = arg_func
            self._arg_func = arg_func.getter
        else:
            raise lena.core.LenaTypeError(
                "arg_func must be a Variable, "
                "{} provided.".format(arg_func)
            )
        # may raise LenaValueError
        lena.structures.check_edges_increasing(edges)
        self.bins = lena.structures.init_bins(edges, seq, deepcopy=True)
        self.edges = edges
        if transform is None:
            transform = TransformBins()
        elif transform == ():
            pass
        elif not isinstance(transform, lena.core.Sequence):
            try:
                transform = lena.core.Sequence(transform)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "transform must be convertible to Sequence, "
                    "{} provided".format(transform)
                )
        self.transform = transform
        self._cur_context = {}

    def fill(self, val):
        """Fill the cell corresponding to *arg_func(val)* with *val*.

        Values outside of *edges* range are ignored.
        """
        data, context = lena.flow.get_data(val), lena.flow.get_context(val)
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
        """Yield a *(Histogram, context)* for *compute()* for each bin.

        :class:`~lena.structures.Histogram`
        is created from :attr:`edges`
        and bins taken from compute() for :attr:`bins`.
        Context is preserved in histogram bins.

        :class:`SplitIntoBins` context is added
        to *context.split_into_bins* as *histogram* 
        (corresponding to *edges*) and *variable*
        (corresponding to *arg_func*) subcontexts.

        In Python 3 the minimum number of *compute()*
        among all bins is used.
        In Python 2, if some bin is exhausted before the others,
        its content will be filled with None.
        """
        # cur_context is shared with some inner sequences
        cur_context = copy.deepcopy(self._cur_context)
        generators = _MdSeqMap(lambda cell: cell.compute(), self.bins)
        # generators = lena.math.md_map(lambda cell: cell.compute(), self.bins)
        while True:
            try:
                result = next(generators)
            except StopIteration:
                break
            # result = lena.math.md_map(next, generators)
            hist = lena.structures.Histogram(self.edges, result)
            old_sib = cur_context.pop("split_into_bins", {})
            if old_sib:
                # nest previous split_into_bins
                cur_context["split_into_bins"] = {"split_into_bins": old_sib}
            else:
                cur_context["split_into_bins"] = {}
            sib_context = cur_context["split_into_bins"]
            # todo. improve consistency below
            var_context = copy.deepcopy({"variable": self._arg_var.var_context})
            hist_context = copy.deepcopy(hist._hist_context)
            sib_context.update(var_context)
            sib_context.update(hist_context)
            if self.transform:
                results = self.transform.run([(hist, cur_context)])
                for result in results:
                    yield result
            else:
                yield (hist, cur_context)
