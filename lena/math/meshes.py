"""mesh, md_map, flatten work with multidimensional data."""
from __future__ import print_function

from itertools import count, islice


def flatten(array):
    """Flatten an *array* of arbitrary dimension.

    *array* must be list or a tuple (can be nested).
    Depth-first flattening is used.

    Return an iterator over the flattened array.

    Examples:

    >>> arr = [1, 2, 3]
    >>> list(flatten(arr)) == arr
    True
    >>> arr = [[1, 2, 3, [4]], 5, [[6]], 7]
    >>> list(flatten(arr))
    [1, 2, 3, 4, 5, 6, 7]
    >>> arr = [[1, 2, [3], 4], 5, [[6]], 7]
    >>> list(flatten(arr))
    [1, 2, 3, 4, 5, 6, 7]
    """
    for el in array:
        if isinstance(el, (list, tuple)):
            for val in flatten(el):
                yield val
        else:
            yield el


def md_map(f, array):
    """Multidimensional map.

    Return function *f* mapped to contents
    of a multidimensional *array*.
    *f* is a function of one argument.

    *Array* must be a list of (possibly nested) lists.
    Its contents remain unchanged.
    Returned array has same dimensions as the initial one.
    If *array* is not a list, :exc:`.LenaTypeError`
    is raised.

    >>> from lena.math import md_map
    >>> arr = [-1, 1, 0]
    >>> md_map(abs, arr)
    [1, 1, 0]
    >>> arr = [[0, -1], [2, 3]]
    >>> md_map(abs, arr)
    [[0, 1], [2, 3]]
    """
    # multidimensional map with iterables is pretty useless,
    # because it iterables can be used in a simple 1-dimensional map.
    # All containers must be materialized.

    # This idea abandoned, because Lena vector3 has len.
    # if hasattr(arr_0, '__len__'):
    ## numpy.array has length, but not always:
    ## >>> len(numpy.array(0))
    ## Traceback (most recent call last):
    ##   File "<stdin>", line 1, in <module>
    ## TypeError: len() of unsized object
    ## >>> len(numpy.array([0])) works fine.
    ## strings have length too, which is probably not so good,
    ## but there are also bytes, unicode,
    ## and we don't want to deal with all of that zoo - that's why
    ## we don't check for those types explicitly.
    ## Python complex numbers don't have len, fortunately.

    if not isinstance(array, list):
        raise lena.core.LenaTypeError(
            "array must be a list, {} provided".format(array)
        )
    # If *array* was empty, empty list is returned.
    # In this implementation we explicitly check that array is a list.
    ## We don't check for exception here, because it will be raised
    ## in case of any problems, and it will be simple to understand.
    if not len(array):
        return []

    arr_0 = array[0]
    # Tuples can be (data, context) pairs,
    # they should not be expanded in ReduceBinContent.
    # if isinstance(arr_0, (list, tuple)):
    if isinstance(arr_0, list):
        return [md_map(f, ar) for ar in array]
    else:
        # return list(map(f, array))
        return [f(val) for val in array]


def mesh(ranges, nbins):
    """Generate equally spaced mesh of *nbins* cells in the given range.

    Parameters:
        ranges: a pair of (min, max) values for 1-dimensional range,
                or a list of ranges in corresponding dimensions.

        nbins: number of bins for 1-dimensional range,
               or a list of number of bins in corresponding dimensions.

    >>> from lena.math import mesh
    >>> mesh((0, 1), 2)
    [0, 0.5, 1]
    >>> mesh(((0, 1), (10, 12)), (1, 2))
    [[0, 1], [10, 11.0, 12]]

    Note that because of rounding errors
    two meshes should not be naively compared,
    they will probably appear different.
    One should use :ref:`isclose <isclose_label>` for comparison.

    >>> from lena.math import isclose
    >>> isclose(mesh((0, 1), 10),
    ...         [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    True
    """
    # >>> mesh((0, 1), 10) ==
    # ...    [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # False, because of 0.30000000000000004

    def mesh_1d(nbins, range_):
        step = float(range_[1] - range_[0]) / nbins
        res = list(islice(count(range_[0], step), nbins)) + [range_[1]]
        # res = [range_[0] + val * step for val in range(nbins + 1)]
        return res

    if not isinstance(nbins, (tuple, list)):
        return mesh_1d(nbins, ranges)

    dim = len(nbins)
    edges = []
    for i in range(dim):
        edges.append(mesh_1d(nbins[i], ranges[i]))
    return edges


def refine_mesh(arr, refinement):
    """Refine (subdivide) one-dimensional mesh *arr*.

    *refinement* is the number of subdivisions.
    It must be not less than 1.

    Note that to create a new mesh may be faster.
    Use this function only for convenience.
    """
    # *arr* must be one-dimensional.
    new_mesh = [arr[0]]
    for low, up in zip(arr, arr[1:]):
        new_mesh.extend(mesh((low, up), refinement)[1:])
    return new_mesh
