"""Functions to work with context (dictionary)."""
import copy

import lena.core

# pylint: disable=invalid-name
# d is a good name for dictionary,
# used in Python documentation for dict.


def check_context_str(d, s):
    """Check that dictionary *d* satisfies a dot-separated string *s*.

    True if *d* contains a subdictionary, which is represented by *s*.
    Dots in *s* signify nesting.
    *s* must have at least two dot-separated parts,
    otherwise :exc:`~lena.core.LenaValueError` is raised.

    See also :func:`str_to_dict`.
    """
    # todo: rename to is_subdictionary?
    # add examples
    levels = s.split(".")
    if len(levels) < 2:
        raise lena.core.LenaValueError(
            "provide at least two dot-separated values."
        )
    subdict = d
    for key in levels[:-1]:
        if key not in subdict:
            return False
        subdict = subdict[key]
    last_val = levels[-1]
    if isinstance(subdict, dict):
        return last_val in subdict
    else: # just a value
        return subdict == last_val


def difference(d1, d2):
    """Return a dictionary with items from *d1* not contained in *d2*.

    If a key is present both in *d1* and *d2* but has different values,
    it is included into the difference.
    """
    result = {}
    for key in d1:
        if key not in d2 or d1[key] != d2[key]:
            result[key] = d1[key]
    return result


_sentinel = object()


def get_recursively(d, keys, default=_sentinel):
    """Get value from a dictionary *d* recursively.

    *keys* can be a list of simple keys (strings),
    a dot-separated string
    or a dictionary with at most one key at each level.
    A string is split by dots and used as a list.
    A list of keys is searched in the dictionary recursively
    (it represents nested dictionaries).
    If any of them is not found, *default* is returned
    if "default" is given,
    otherwise :exc:`~lena.core.LenaKeyError` is raised.

    If *keys* is empty, *d* is returned.

    Examples:

    >>> context = {"output": {"latex": {"name": "x"}}}
    >>> get_recursively(context, ["output", "latex", "name"], default="y")
    'x'
    >>> get_recursively(context, "output.latex.name")
    'x'

    .. note::
        Python's dict.get in case of a missing value
        returns ``None`` and never raises an error.
        We implement it differently,
        because it allows more flexibility.

    If *d* is not a dictionary or if *keys* have unknown types,
    :exc:`~lena.core.LenaTypeError` is raised.
    If *keys* is a dictionary with more than one key at some level,
    :exc:`~lena.core.LenaValueError` is raised.
    """
    has_default = default is not _sentinel
    if not isinstance(d, dict):
        raise lena.core.LenaTypeError(
            "need a dictionary, {} provided".format(d)
        )
    if isinstance(keys, str):
        keys = keys.split('.')
    elif isinstance(keys, dict):
        new_keys = []
        while keys:
            if isinstance(keys, dict) and len(keys) != 1:
                raise lena.core.LenaValueError(
                    "keys must have exactly one key at each level, "
                    "{} given".format(keys)
                )
            else:
                if not isinstance(keys, dict):
                    new_keys.append(keys)
                    break
                for key in keys:
                    new_keys.append(key)
                    keys = keys[key]
                    break
        keys = new_keys
    elif isinstance(keys, list):
        if not all(isinstance(k, str) for k in keys):
            raise lena.core.LenaTypeError(
                "all simple keys must be strings, "
                "{} given".format(keys)
            )
    else:
        raise lena.core.LenaTypeError(
            "keys must be a dict, a string or a list of keys, "
            "{} given".format(keys)
        )

    for key in keys[:-1]:
        if key in d and isinstance(d.get(key), dict):
            d = d[key]
        elif has_default:
            return default
        else:
            raise lena.core.LenaKeyError(
                "nested dict {} not found in {}".format(key, d)
            )

    if not keys:
        return d
    if keys[-1] in d:
        return d[keys[-1]]
    elif has_default:
        return default
    else:
        raise lena.core.LenaKeyError(
            "nested key {} not found in {}".format(keys[-1], d)
        )


def intersection(*dicts, **kwargs):
    """Return a dictionary, such that each of its items
    are contained in all *dicts* (recursively).

    *dicts* are several dictionaries.
    If *dicts* is empty, an empty dictionary is returned.

    A keyword argument *level* sets maximum number of recursions.
    For example, if *level* is 0, all *dicts* must be equal
    (otherwise an empty dict is returned).
    If *level* is 1, the result contains those subdictionaries
    which are equal.
    For arbitrarily nested subdictionaries set *level* to -1 (default).

    Example:

    >>> from lena.context import intersection
    >>> d1 = {1: "1", 2: {3: "3", 4: "4"}}
    >>> d2 = {2: {4: "4"}}
    >>> # by default level is -1, which means infinite recursion
    >>> intersection(d1, d2) == d2
    True
    >>> intersection(d1, d2, level=0)
    {}
    >>> intersection(d1, d2, level=1)
    {}
    >>> intersection(d1, d2, level=2)
    {2: {4: '4'}}

    This function always returns a dictionary
    or its subtype (copied from dicts[0]).
    All values are deeply copied.
    No dictionary or subdictionary is changed.

    If any of *dicts* is not a dictionary
    or if some *kwargs* are unknown,
    :exc:`~lena.core.LenaTypeError` is raised.
    """
    if not all([isinstance(d, dict) for d in dicts]):
        raise lena.core.LenaTypeError(
            "all dicts must be dictionaries, "
            "{} given".format(dicts)
        )

    level = kwargs.pop("level", -1)
    if kwargs:
        raise lena.core.LenaTypeError(
            "unknown kwargs {}".format(kwargs)
        )

    if not dicts:
        return {}
    res = copy.deepcopy(dicts[0])
    for d in dicts[1:]:
        if level == 0:
            if d == res and d:
                continue
            else:
                return {}
        to_delete = []
        for key in res:
            if key in d:
                if d[key] != res[key]:
                    if level == 1:
                        to_delete.append(key)
                    elif isinstance(res[key], dict) and isinstance(d[key], dict):
                        res[key] = intersection(res[key], d[key], level=level-1)
                    else:
                        to_delete.append(key)
            else:
                # keys can't be deleted during iteration
                to_delete.append(key)
        for key in to_delete:
            del res[key]
        if not res:
            # res was calculated empty
            return res
    return res


def iterate_update(d, updates):
    """Iterate on updates of *d* with *updates*.

    *d* is a dictionary. It remains unchanged.

    *updates* is a list of dictionaries.
    For each element *update*
    a copy of *d* updated with *update* is yielded.

    If *updates* is empty, nothing is yielded.
    """
    # todo: do I need this function?
    for update in updates:
        d_copy = copy.deepcopy(d)
        update_recursively(d_copy, update)
        yield d_copy


def make_context(obj, *attrs):
    """Return context for object *obj*.

    *attrs* is a list of attributes of *obj* to be inserted
    into the context.
    If an attribute starts with an underscore '_',
    it is inserted without the underscore.
    If an attribute is absent or None, it is skipped.
    """
    # todo: rename to to_dict
    # not used anywhere, change it freely.
    # add examples.
    context = {}
    for attr in attrs:
        val = getattr(obj, attr, None)
        if val is not None:
            if attr.startswith("_"):
                attr = attr[1:]
            context.update({attr: val})
    return context


def str_to_dict(s):
    """Create a dictionary from a dot-separated string *s*.

    Dots represent nested dictionaries.
    *s*, if not empty, must have at least two dot-separated parts
    (*a.b*), otherwise :exc:`~lena.core.LenaValueError` is raised.

    If *s* is empty, an empty dictionary is returned.
    *s* can be a dictionary. In this case it is returned as it is.

    Example:

    >>> str_to_dict("a.b.c d")
    {'a': {'b': 'c d'}}
    """
    # todo: add a parameter to recover ints from ints?
    if s == "":
        return {}
    elif isinstance(s, dict):
        return s
    parts = s.split(".")
    d = {}
    def nest_list(d, l):
        """Convert list *l* to nested dictionaries in *d*."""
        len_l = len(l)
        if len_l == 2:
            d.update([(l[0], l[1])])
        elif len_l < 2:
            raise lena.core.LenaValueError(
                "to make a dict, provide at least two dot-separated values."
            )
        else:
            d.update([(l[0], nest_list({}, l[1:]))])
        return d
    nest_list(d, parts)
    return d


def update_nested(d, other):
    """Update dictionary *d* with items from *other* dictionary.

    *other* must be a dictionary of one element, which is used
    as a key. If *d* doesn't contain the key,
    *d* is updated with *other*.
    If *d* contains the key, the value with that key is nested
    inside the copy of *other* at the level
    which doesn't contain the key. *d* is updated.

    If *d[key]* is not a dictionary
    or if there is not one key in *other*,
    :exc:`~lena.core.LenaValueError` is raised.
    """
    if not isinstance(other, dict) or len(other) != 1:
        raise lena.core.LenaValueError(
            "other must be a dictionary of size one, "
            "{} provided".format(other)
        )
    def get_most_nested_subdict_with(key, d):
        while True:
            if key in d:
                d = d[key]
            else:
                return d
    for val in other:
        key = val
    if key in d:
        if not isinstance(d[key], dict):
            raise lena.core.LenaValueError(
                "d[{}] must be a dict, {} given"
                .format(key, d[key])
            )
        other_most_nested = get_most_nested_subdict_with(key, other)
        # d[key] must be a dict
        other_most_nested.update(d[key])
    d.update(other)


def update_recursively(d, other):
    """Update dictionary *d* with items from *other* dictionary.

    *other* can be a dot-separated string. In this case
    :func:`str_to_dict` is used to convert it to a dictionary.

    Existing values are updated recursively,
    that is including nested subdictionaries.
    For example:

    >>> d1 = {"a": 1, "b": {"c": 3}}
    >>> d2 = {"b": {"d": 4}}
    >>> update_recursively(d1, d2)
    >>> d1 == {'a': 1, 'b': {'c': 3, 'd': 4}}
    True
    >>> # Usual update would have made d1["b"] = {"d": 4}, erasing "c".

    Non-dictionary items from *other* overwrite those in *d*:

    >>> update_recursively(d1, {"b": 2})
    >>> d1 == {'a': 1, 'b': 2}
    True

    Both *d* and *other* must be dictionaries,
    otherwise :exc:`~lena.core.LenaTypeError` is raised.
    """
    if isinstance(other, str):
        other = str_to_dict(other)
    if not isinstance(d, dict) or not isinstance(other, dict):
        raise lena.core.LenaTypeError(
            "d and other must be dicts, {} and {} provided".format(d, other)
        )
    for key, val in other.items():
        if not isinstance(val, dict):
            d[key] = val
        else:
            if key in d:
                update_recursively(d[key], other[key])
            else:
                d[key] = val
