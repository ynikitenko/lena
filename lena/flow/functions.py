"""Functions to deal with data and context, and :func:`seq_map`.

A value is considered a (data, context) pair,
if it is a tuple of length 2,
and the second element is a dictionary or its subclass.
"""
import lena.core


def get_context(value):
    """Get context from a possible *(data, context)* pair.

    If context is not found, return an empty dictionary.
    """
    if _has_context(value):
        return value[1]
    else:
        return {}


def get_data(value):
    """Get data from *value* (a possible *(data, context)* pair).

    If context is not found, return *value*.
    """
    if _has_context(value):
        return value[0]
    else:
        return value


def get_data_context(value):
    """Get (data, context) from *value* (a possible *(data, context)* pair).

    If context is not found, (value, {}) is returned.

    Since :func:`get_data` and :func:`get_context`
    both check whether context is present,
    this function may be slightly more efficient
    and compact than the other two.
    """
    if _has_context(value):
        return (value[0], value[1])
    else:
        return (value, {})


def _has_context(value):
    """A *value* is a *(data, context)* pair, if it is a tuple of length 2,
    where the second element is derived from a *dictionary*.
    """
    if isinstance(value, tuple):
        if len(value) == 2:
            if isinstance(value[1], dict):
                return True
    return False


def seq_map(seq, container, one_result=True):
    """Map Lena Sequence *seq* to the *container*.

    For each value from the *container*, calculate ``seq.run([value])``.
    This can be a list or a single value.
    If *one_result* is True, the result must be a single value.
    In this case, if results contain less than or more than one element,
    :exc:`~lena.core.LenaValueError` is raised.

    The list of results (lists or single values) is returned. 
    The results are in the same order as read from the *container*.
    """
    results = list(list(seq.run([val])) for val in container)
    if one_result and not all(map(lambda l: len(l) == 1, results)):
        raise lena.core.LenaValueError(
            "some results are not of length one, {}".format(results)
        )
    if one_result:
        return [l[0] for l in results]
    return results
