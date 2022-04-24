"""Functions for histograms.

These functions are used for low-level work
with histograms and their contents.
They are not needed for normal usage.
"""
import collections
import copy
import itertools
import operator
import re
import sys
if sys.version_info.major == 3:
    from functools import reduce as _reduce
else:
    _reduce = reduce

import lena.core
from .graph import graph as _graph


class HistCell(collections.namedtuple("HistCell", ("edges, bin, index"))):
    """A namedtuple with fields *edges, bin, index*."""
    # from Aaron Hall's answer https://stackoverflow.com/a/28568351/952234
    __slots__ = ()


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


def _check_edges_increasing_1d(arr):
    if len(arr) <= 1:
        raise lena.core.LenaValueError("size of edges should be more than one,"
                                       " {} provided".format(arr))
    increasing = (tup[0] < tup[1] for tup in zip(arr, arr[1:]))
    if not all(increasing):
        raise lena.core.LenaValueError(
            "expected strictly increasing values, "
            "{} provided".format(arr)
        )


def check_edges_increasing(edges):
    """Assure that multidimensional *edges* are increasing.

    If length of *edges* or its subarray is less than 2
    or if some subarray of *edges*
    contains not strictly increasing values,
    :exc:`.LenaValueError` is raised.
    """
    if not len(edges):
        raise lena.core.LenaValueError("edges must be non-empty")
    elif not hasattr(edges[0], '__iter__'):
        _check_edges_increasing_1d(edges)
        return
    for arr in edges:
        if len(arr) <= 1:
            raise lena.core.LenaValueError(
                "size of edges should be more than one. "
                "{} provided".format(arr)
            )
        _check_edges_increasing_1d(arr)


def get_bin_edges(index, edges):
    """Return edges of the bin for the given *edges* of a histogram.

    In one-dimensional case *index* must be an integer and a tuple
    of *(x_low_edge, x_high_edge)* for that bin is returned.

    In a multidimensional case *index* is a container of numeric indices
    in each dimension.
    A list of bin edges in each dimension is returned."""
    # todo: maybe give up this 1- and multidimensional unification
    # and write separate functions for each case.
    if not hasattr(edges[0], '__iter__'):
        # 1-dimensional edges
        if hasattr(index, '__iter__'):
            index = index[0]
        return (edges[index], edges[index+1])
    # multidimensional edges
    return [(edges[coord][i], edges[coord][i+1])
            for coord, i in enumerate(index)]


def get_bin_on_index(index, bins):
    """Return bin corresponding to multidimensional *index*.

    *index* can be a number or a list/tuple.
    If *index* length is less than dimension of *bins*,
    a subarray of *bins* is returned.

    In case of an index error, :exc:`.LenaIndexError` is raised.

    Example:

    >>> from lena.structures import histogram, get_bin_on_index
    >>> hist = histogram([0, 1], [0])
    >>> get_bin_on_index(0, hist.bins)
    0
    >>> get_bin_on_index((0, 1), [[0, 1], [0, 0]])
    1
    >>> get_bin_on_index(0, [[0, 1], [0, 0]])
    [0, 1]
    """
    if not isinstance(index, (list, tuple)):
        index = [index]
    subarr = bins
    for ind in index:
        try:
            subarr = subarr[ind]
        except IndexError:
            raise lena.core.LenaIndexError(
                "bad index: {}, bins = {}".format(index, bins)
            )
    return subarr


def get_bin_on_value_1d(val, arr):
    """Return index for value in one-dimensional array.

    *arr* must contain strictly increasing values
    (not necessarily equidistant),
    it is not checked.

    "Linear binary search" is used,
    that is our array search by default assumes
    the array to be split on equidistant steps.

    Example:

    >>> from lena.structures import get_bin_on_value_1d
    >>> arr = [0, 1, 4, 5, 7, 10]
    >>> get_bin_on_value_1d(0, arr)
    0
    >>> get_bin_on_value_1d(4.5, arr)
    2
    >>> # upper range is excluded
    >>> get_bin_on_value_1d(10, arr)
    5
    >>> # underflow
    >>> get_bin_on_value_1d(-10, arr)
    -1
    """
    # may also use numpy.searchsorted
    # https://docs.scipy.org/doc/numpy-1.15.0/reference/generated/numpy.searchsorted.html
    ind_min = 0
    ind_max = len(arr) - 1
    while True:
        if ind_max - ind_min <= 1:
            # lower bound is close
            if val < arr[ind_min]:
                return ind_min - 1
            # upper bound is open
            elif val >= arr[ind_max]:
                return ind_max
            else:
                return ind_min
        if val == arr[ind_min]:
            return ind_min
        if val < arr[ind_min]:
            return ind_min - 1
        elif val >= arr[ind_max]:
            return ind_max
        else:
            shift = int(
                (ind_max - ind_min) * (
                    float(val - arr[ind_min]) / (arr[ind_max] - arr[ind_min])
                ))
            ind_guess = ind_min + shift

            if ind_min == ind_guess:
                ind_min += 1
                continue
            # ind_max is always more that ind_guess,
            # because val < arr[ind_max] (see the formula for shift).
            # This branch is not needed and can't be tested.
            # But for the sake of numerical inaccuracies, let us keep this
            # so that we never get into an infinite loop.
            elif ind_max == ind_guess:
                ind_max -= 1
                continue

            if val < arr[ind_guess]:
                ind_max = ind_guess
            else:
                ind_min = ind_guess


def get_bin_on_value(arg, edges):
    """Get the bin index for *arg* in a multidimensional array *edges*.

    *arg* is a 1-dimensional array of numbers
    (or a number for 1-dimensional *edges*),
    and corresponds to a point in N-dimensional space.

    *edges* is an array of N-1 dimensional arrays (lists or tuples) of numbers.
    Each 1-dimensional subarray consists of increasing numbers.

    *arg* and *edges* must have the same length
    (otherwise :exc:`.LenaValueError` is raised).
    *arg* and *edges* must be iterable and support *len()*.

    Return list of indices in *edges* corresponding to *arg*.

    If any coordinate is out of its corresponding edge range,
    its index will be ``-1`` for underflow
    or ``len(edge)-1`` for overflow.

    Examples:

    >>> from lena.structures import get_bin_on_value
    >>> edges = [[1, 2, 3], [1, 3.5]]
    >>> get_bin_on_value((1.5, 2), edges)
    [0, 0]
    >>> get_bin_on_value((1.5, 0), edges)
    [0, -1]
    >>> # the upper edge is excluded
    >>> get_bin_on_value((3, 2), edges)
    [2, 0]
    >>> # one-dimensional edges
    >>> edges = [1, 2, 3]
    >>> get_bin_on_value(2, edges)
    [1]
    """
    # arg is a one-dimensional index
    if not isinstance(arg, (tuple, list)):
        return [get_bin_on_value_1d(arg, edges)]
    # arg is a multidimensional index
    if len(arg) != len(edges):
        raise lena.core.LenaValueError(
            "argument should have same dimension as edges. "
            "arg = {}, edges = {}".format(arg, edges)
        )
    indices = []
    for ind, array in enumerate(edges):
        cur_bin = get_bin_on_value_1d(arg[ind], array)
        indices.append(cur_bin)
    return indices


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


def hist_to_graph(hist, make_value=None, get_coordinate="left",
                  field_names=("x", "y"), scale=None):
    """Convert a :class:`.histogram` to a :class:`.graph`.

    *make_value* is a function to set the value of a graph's point.
    By default it is bin content.
    *make_value* accepts a single value (bin content) without context.

    This option could be used to create graph's error bars.
    For example, to create a graph with errors
    from a histogram where bins contain
    a named tuple with fields *mean*, *mean_error* and a context
    one could use

    >>> make_value = lambda bin_: (bin_.mean, bin_.mean_error)

    *get_coordinate* defines what the coordinate
    of a graph point created from a histogram bin will be.
    It can be "left" (default), "right" and "middle".

    *field_names* set field names of the graph. Their number
    must be the same as the dimension of the result.
    For a *make_value* above they would be
    *("x", "y_mean", "y_mean_error")*.

    *scale* becomes the graph's scale (unknown by default).
    If it is ``True``, it uses the histogram scale.

    *hist* must contain only numeric bins (without context)
    or *make_value* must remove context when creating a numeric graph.

    Return the resulting graph.
    """
    ## Could have allowed get_coordinate to be callable
    # (for generality), but 1) first find a use case,
    # 2) histogram bins could be adjusted in the first place.
    # -- don't understand 2.
    if get_coordinate == "left":
        get_coord = lambda edges: tuple(coord[0] for coord in edges)
    elif get_coordinate == "right":
        get_coord = lambda edges: tuple(coord[1] for coord in edges)
    # *middle* between the two edges, not the *center* of the bin
    # as a whole (because the graph corresponds to a point)
    elif get_coordinate == "middle":
        get_coord = lambda edges: tuple(0.5*(coord[0] + coord[1])
                                        for coord in edges)
    else:
        raise lena.core.LenaValueError(
            'get_coordinate must be one of "left", "right" or "middle"; '
            '"{}" provided'.format(get_coordinate)
        )

    # todo: make_value may be bad design.
    # Maybe allow to change the graph in the sequence.
    # However, make_value allows not to recreate a graph
    # or its coordinates (if that is not needed).

    if isinstance(field_names, str):
        # copied from graph.__init__
        field_names = tuple(re.findall(r'[^,\s]+', field_names))
    elif not isinstance(field_names, tuple):
        raise lena.core.LenaTypeError(
            "field_names must be a string or a tuple"
        )
    coords = [[] for _ in field_names]

    chain = itertools.chain

    if scale is True:
        scale = hist.scale()

    for value, edges in iter_bins_with_edges(hist.bins, hist.edges):
        coord = get_coord(edges)

        # Since we never use contexts here, it will be optimal
        # to ignore them completely (remove them elsewhere).
        # bin_value = lena.flow.get_data(value)
        bin_value = value

        if make_value is None:
            graph_value = bin_value
        else:
            graph_value = make_value(bin_value)

        # for iteration below
        if not hasattr(graph_value, "__iter__"):
            graph_value = (graph_value,)

        # add each coordinate to respective array
        for arr, coord_ in zip(coords, chain(coord, graph_value)):
            arr.append(coord_)

    return _graph(coords, field_names=field_names, scale=scale)


def init_bins(edges, value=0, deepcopy=False):
    """Initialize cells of the form *edges* with the given *value*.

    Return bins filled with copies of *value*.

    *Value* must be copyable, usual numbers will suit.
    If the value is mutable, use *deepcopy =* ``True``
    (or the content of cells will be identical).

    Examples:

    >>> edges = [[0, 1], [0, 1]]
    >>> # one cell
    >>> init_bins(edges)
    [[0]]
    >>> # no need to use floats,
    >>> # because integers will automatically be cast to floats
    >>> # when used together
    >>> init_bins(edges, 0.0)
    [[0.0]]
    >>> init_bins([[0, 1, 2], [0, 1, 2]])
    [[0, 0], [0, 0]]
    >>> init_bins([0, 1, 2])
    [0, 0]
    """
    nbins = len(edges) - 1
    if not isinstance(edges[0], (list, tuple)):
        # edges is one-dimensional
        if deepcopy:
            return [copy.deepcopy(value) for _ in range(nbins)]
        else:
            return [value] * nbins
    for ind, arr in enumerate(edges):
        if ind == nbins:
            if deepcopy:
                return [copy.deepcopy(value) for _ in range(len(arr)-1)]
            else:
                return list([value] * (len(arr)-1))
        bins = []
        for _ in range(len(arr)-1):
            bins.append(init_bins(edges[ind+1:], value, deepcopy))
        return bins


def integral(bins, edges):
    """Compute integral (scale for a histogram).

    *bins* contain values, and *edges* form the mesh
    for the integration.
    Their format is defined in :class:`.histogram` description.
    """
    total = 0
    for ind, bin_content in iter_bins(bins):
        bin_lengths = [
            edges[coord][i+1] - edges[coord][i]
            for coord, i in enumerate(ind)
        ]
        # product
        vol = _reduce(operator.mul, bin_lengths, 1)
        cell_integral = vol * bin_content
        total += cell_integral
    return total


def iter_bins(bins):
    """Iterate on *bins*. Yield *(index, bin content)*.

    Edges with higher index are iterated first
    (that is z, then y, then x for a 3-dimensional histogram).
    """
    # if not isinstance(bins, (list, tuple)):
    if not hasattr(bins, '__iter__'):
        # cell
        yield ((), bins)
    else:
        for ind, _ in enumerate(bins):
            for sub_ind, val in iter_bins(bins[ind]):
                yield (((ind,) + sub_ind), val)


def iter_bins_with_edges(bins, edges):
    """Generate *(bin content, bin edges)* pairs.

    Bin edges is a tuple, such that
    its item at index i is *(lower bound, upper bound)*
    of the bin at i-th coordinate.

    Examples:

    >>> from lena.math import mesh
    >>> list(iter_bins_with_edges([0, 1, 2], edges=mesh((0, 3), 3)))
    [(0, ((0, 1.0),)), (1, ((1.0, 2.0),)), (2, ((2.0, 3),))]
    >>>
    >>> # 2-dimensional histogram
    >>> list(iter_bins_with_edges(
    ...     bins=[[2]], edges=mesh(((0, 1), (0, 1)), (1, 1))
    ... ))
    [(2, ((0, 1), (0, 1)))]

    .. versionadded:: 0.5
       made public.
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


def iter_cells(hist, ranges=None, coord_ranges=None):
    """Iterate cells of a histogram *hist*, possibly in a subrange.

    For each bin, yield a :class:`HistCell`
    containing *bin edges, bin content* and *bin index*.
    The order of iteration is the same as for :func:`iter_bins`.

    *ranges* are the ranges of bin indices to be used
    for each coordinate
    (the lower value is included, the upper value is excluded).

    *coord_ranges* set real coordinate ranges based on histogram edges.
    Obviously, they can be not exactly bin edges.
    If one of the ranges for the given coordinate
    is outside the histogram edges,
    then only existing histogram edges within the range are selected.
    If the coordinate range is completely outside histogram edges,
    nothing is yielded.
    If a lower or upper *coord_range*
    falls within a bin, this bin is yielded.
    Note that if a coordinate range falls on a bin edge,
    the number of generated bins can be unstable
    because of limited float precision.

    *ranges* and *coord_ranges* are tuples of tuples of limits
    in corresponding dimensions. 
    For one-dimensional histogram it must be a tuple 
    containing a tuple, for example
    *((None, None),)*.

    ``None`` as an upper or lower *range* means no limit
    (*((None, None),)* is equivalent to *((0, len(bins)),)*
    for a 1-dimensional histogram).

    If a *range* index is lower than 0 or higher than possible index,
    :exc:`.LenaValueError` is raised.
    If both *coord_ranges* and *ranges* are provided,
    :exc:`.LenaTypeError` is raised.
    """
    # for bin_ind, bin_ in iter_bins(hist.bins):
    #     yield HistCell(get_bin_edges(bin_ind, hist.edges), bin_, bin_ind)
    # if bins and edges are calculated each time, save the result now
    bins, edges = hist.bins, hist.edges
    # todo: hist.edges must be same
    # for 1- and multidimensional histograms.
    if hist.dim == 1:
        edges = (edges,)

    if coord_ranges is not None:
        if ranges is not None:
            raise lena.core.LenaTypeError(
                "only ranges or coord_ranges can be provided, not both"
            )
        ranges = []
        if not isinstance(coord_ranges[0], (tuple, list)):
            coord_ranges = (coord_ranges, )
        for coord, coord_range in enumerate(coord_ranges):
            # todo: (dis?)allow None as an infinite range.
            # todo: raise or transpose unordered coordinates?
            # todo: change the order of function arguments.
            lower_bin_ind = get_bin_on_value_1d(coord_range[0], edges[coord])
            if lower_bin_ind == -1:
                 lower_bin_ind = 0
            upper_bin_ind = get_bin_on_value_1d(coord_range[1], edges[coord])
            max_ind = len(edges[coord])
            if upper_bin_ind == max_ind:
                 upper_bin_ind -= 1
            if lower_bin_ind >= max_ind or upper_bin_ind <= 0:
                 # histogram edges are outside the range.
                 return
            ranges.append((lower_bin_ind, upper_bin_ind))

    if not ranges:
        ranges = ((None, None),) * hist.dim

    real_ind_ranges = []
    for coord, coord_range in enumerate(ranges):
        low, up = coord_range
        if low is None:
            low = 0
        else:
            # negative indices should not be supported
            if low < 0:
                raise lena.core.LenaValueError(
                    "low must be not less than 0 if provided"
                )
        max_ind = len(edges[coord]) - 1
        if up is None:
            up = max_ind
        else:
            # huge indices should not be supported as well.
            if up > max_ind:
                raise lena.core.LenaValueError(
                    "up must not be greater than len(edges)-1, if provided"
                )
        real_ind_ranges.append(list(range(low, up)))

    indices = list(itertools.product(*real_ind_ranges))
    for ind in indices:
        yield HistCell(get_bin_edges(ind, edges),
                       get_bin_on_index(ind, bins),
                       ind)


def make_hist_context(hist, context):
    """Update a deep copy of *context* with the context
    of a :class:`.histogram` *hist*.

    .. deprecated:: 0.5
       histogram context is updated automatically
       during conversion in :class:`~.output.ToCSV`.
       Use histogram._update_context explicitly if needed.
    """
    # absolutely unnecessary.
    context = copy.deepcopy(context)

    hist_context = {
        "histogram": {
            "dim": hist.dim,
            "nbins": hist.nbins,
            "ranges": hist.ranges
        }
    }
    context.update(hist_context)
    # just bad.
    return context


def unify_1_md(bins, edges):
    """Unify 1- and multidimensional bins and edges.

    Return a tuple of *(bins, edges)*.  
    Bins and multidimensional *edges* return unchanged,
    while one-dimensional *edges* are inserted into a list.
    """
    if hasattr(edges[0], '__iter__'):
    # if isinstance(edges[0], (list, tuple)):
        return (bins, edges)
    else:
        return (bins, [edges])
