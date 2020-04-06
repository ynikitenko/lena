"""Numerical utilities functions."""
from numbers import Number

import lena.core


def clip(a, interval):
    """Clip (limit) the value.

    Given an interval *(a_min, a_max)*,
    values of *a* outside the interval are clipped to the interval edges.
    For example, if an interval of *[0, 1]* is specified,
    values smaller than 0 become 0, and values larger than 1 become 1.

    >>> clip(-1, (0, 1))
    0
    >>> # tuple looks better, but list can be used too
    >>> clip(2, [0, 1])
    1
    >>> clip(0.5, (0, 1))
    0.5

    If *a_min* > *a_max* or if *interval* has length more than 2,
    :exc:`~lena.core.LenaValueError` is raised.
    If *interval* is not a container,
    :exc:`~lena.core.LenaTypeError` is raised.
    """
    # Inspired by
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.clip.html
    # https://stackoverflow.com/a/9775761/952234
    try:
        l = len(interval)
    except TypeError:
        raise lena.core.LenaTypeError("interval must be a container of size 2.")
    if l != 2:
        raise lena.core.LenaValueError("interval must be a container of size 2.")
    a_min = interval[0]
    a_max = interval[1]
    if a_min > a_max:
        raise lena.core.LenaValueError(
            "interval must be increasing, "
            "({}, {}) provided.".format(a_min, a_max)
        )
    return max(min(a_max, a), a_min)


def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    # https://docs.python.org/3/whatsnew/3.5.html#pep-485-a-function-for-testing-approximate-equality
    # https://stackoverflow.com/a/33024979/952234
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    """Return ``True`` if *a* and *b* are approximately equal,
    and ``False`` otherwise.

    *rel_tol* is the relative tolerance.
    It is multiplied by the greater of the magnitudes
    of the two arguments;
    as the values get larger,
    so does the allowed difference between them
    while still considering them close.

    *abs_tol* is the absolute tolerance.
    If the difference is less than either of those tolerances,
    the values are considered equal.

    *a* and *b* must be either numbers
    or lists/tuples of same dimensions (may be nested),
    or have a method *isclose*.
    Otherwise :exc:`~lena.core.LenaTypeError` is raised.
    For containers, *isclose* is called elementwise.
    If every corresponding element is close, the containers are close.
    Dimensions are not checked to be equal.

    First, *a* and *b* are checked if any of them has *isclose* method.
    If *a* and *b* both have *isclose* method,
    then they must both return ``True`` to be close.
    Otherwise, if only one of *a* or *b* has *isclose* method,
    it is called.

    Special values of ``NaN``, ``inf``, and ``-inf`` are not supported.

    >>> isclose(1, 2)
    False
    >>> isclose([1, 2, 3], (1, 2., 3))
    True

    This function for scalar numbers
    appeared in ``math`` module in *Python 3.5*.
    """
    if hasattr(a, 'isclose') and hasattr(b, 'isclose'):
        # isclose should be reflexive
        return a.isclose(b, rel_tol, abs_tol) \
                and b.isclose(a, rel_tol, abs_tol)
    elif hasattr(a, 'isclose'):
        return a.isclose(b, rel_tol, abs_tol)
    elif hasattr(b, 'isclose'):
        return b.isclose(a, rel_tol, abs_tol)
    elif isinstance(a, Number):
        return _isclose(a, b, rel_tol, abs_tol)
    elif isinstance(a, (list, tuple)):
        for ind, el in enumerate(a):
            if not isclose(el, b[ind], rel_tol, abs_tol):
                return False
        return True
    else:
        raise lena.core.LenaTypeError("isclose doesn't support {} and {}".format(a, b))
