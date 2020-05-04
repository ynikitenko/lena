"""Functions for histograms.

These functions are used for low-level work
with histograms and their contents.
They are not needed for normal usage.
"""
from __future__ import print_function

import copy
import operator
import sys
if sys.version_info.major == 3:
    # we don't want to import reduce to this module.
    from functools import reduce as _reduce
else:
    _reduce = reduce

import lena.core
from . import graph


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

    >>> from lena.structures import Histogram, get_bin_on_index
    >>> hist = Histogram([0, 1], [0])
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


def hist_to_graph(hist, context, make_graph_value=None, bin_coord="left"):
    """Convert a :class:`.Histogram` *hist*
    to a :class:`.Graph`.

    *context* becomes graph's context.
    For example, it can contain a scale.

    *make_graph_value* is a function to set graph point's value.
    By default it is bin content. This option could be used to
    create graph error bars.
    *make_graph_value* must accept bin content and bin context
    as positional arguments.

    *bin_coord* signifies which will be the coordinate
    of a graph's point created from histogram's bin.
    Can be "left" (default), "right" and "middle".

    Return the resulting graph.
    """
    gr = graph.Graph(context=context)
    def get_coord(edges, bin_coord):
        if bin_coord == "left":
            return tuple(coord[0] for coord in edges)
        elif bin_coord == "right":
            return tuple(coord[1] for coord in edges)
        # or center?
        elif bin_coord == "middle":
            return tuple(0.5*(coord[0] + coord[1]) for coord in edges)
        else:
            raise lena.core.LenaValueError(
                "bin_coord must be one of left, right or middle, "
                "{} provided".format(bin_coord)
            )
    # todo: move it here, of course
    from lena.flow.split_into_bins import _iter_bins_with_edges as ibe
    for value, edges in ibe(hist.bins, hist.edges):
        coord = get_coord(edges, bin_coord)
        bin_value, bin_context = lena.flow.get_data_context(value)
        if not hasattr(bin_value, "__iter__"):
            bin_value = (bin_value,)
        if make_graph_value is None:
            graph_value = bin_value
        else:
            graph_value = make_graph_value(bin_value, bin_context)
        gr.fill((coord, graph_value))
    return gr


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
    Their format is defined in :class:`.Histogram` description.
    """
    total = 0
    for ind, bin_content in iter_bins(bins):
        # print(bins, edges)
        # print(ind, bin_content)
        bin_lengths = [
            edges[coord][i+1] - edges[coord][i]
            for coord, i in enumerate(ind)
        ]
        # print(bin_lengths)
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


def iter_cells(hist):
    """Iterate cells of a histogram *hist*.

    For each bin, yield a *(bin edges, bin content)* tuple.
    The order of iteration is the same as for :func:`iter_bins`.
    """
    for bin_ind, bin_ in iter_bins(hist.bins):
        yield (get_bin_edges(bin_ind, hist.edges), bin_)


def make_hist_context(hist, context):
    """Update *context* with the context
    of a :class:`.Histogram` *hist*.

    Deep copy of updated context is returned.
    """
    all_context = copy.deepcopy(context)
    hist_context = {
        "histogram": {
            "dim": hist.dim,
            "ranges": hist.ranges, "nbins": hist.nbins
        }
    }
    all_context.update(hist_context)
    return all_context
    # return copy.deepcopy(all_context)


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
