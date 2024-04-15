"""Functions to work with context (dictionary)."""

import copy
from json import dumps

import lena
from lena.core import LenaTypeError, LenaValueError, LenaKeyError

# pylint: disable=invalid-name
# d is a good name for a dictionary,
# used in Python documentation for dict.


def contains(d, s):
    """Check that a dictionary *d* contains a subdictionary
    defined by a string *s*.

    True if *d* contains a subdictionary that is represented by *s*.
    Dots in *s* mean nested subdictionaries.
    A string without dots means a key in *d*.

    Example:

    >>> d = {'fit': {'coordinate': 'x'}}
    >>> contains(d, "fit")
    True
    >>> contains(d, "fit.coordinate.x")
    True
    >>> contains(d, "fit.coordinate.y")
    False

    If the most nested element of *d* to be compared with *s*
    is not a string, its string representation is used for comparison.
    See also :func:`str_to_dict`.
    """
    # This function is used in string selectors.
    # todo: s can be a list, or a dict?
    # todo: should be rewritten through get_recursively or intersection
    levels = s.split(".")
    if len(levels) < 2:
        # todo: an empty string should return True.
        return s in d
    subdict = d
    for key in levels[:-1]:
        if key not in subdict:
            return False
        subdict = subdict[key]
    last_val = levels[-1]
    if isinstance(subdict, dict):
        return last_val in subdict
    else:
        # just a value
        try:
            # it's better to test for an object to be cast to str
            # than to disallow "dim.1"
            subd = str(subdict)
        except Exception:
            return False
        else:
            return subd == last_val


def difference(d1, d2, level=-1):
    """Return a dictionary with items from *d1* not contained in *d2*.

    *level* sets the maximum depth of recursion. For infinite recursion,
    set that to -1. For level 1,
    if a key is present both in *d1* and *d2* but has different values,
    it is included into the difference.
    See :func:`intersection` for more details.

    *d1* and *d2* remain unchanged. However, *d1* or some of its
    subdictionaries may be returned directly.
    Make a deep copy of the result when appropriate.

    .. versionadded:: 0.5
       add keyword argument *level*.
    """
    # can become not dicts during the recursion
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        return d1

    if d1 == d2:
        return {}
    elif level == 0:
        return d1

    # some keys differ
    result = {}
    for key in d1:
        if key not in d2:
            result[key] = d1[key]
        elif d1[key] != d2[key]:
            res = difference(d1[key], d2[key], level-1)
            # if d2[key] contains all d1[key] elements,
            # the difference will be empty
            if res:
                result[key] = res
    return result


def format_context(format_str):
    """Create a function that formats a context using the given string.

    It is recommended to use jinja2.Template.
    Use this function only if you don't have jinja2.

    *format_str* is a Python format string with double braces
    instead of single ones.
    It must contain all non-empty replacement fields,
    and only simplest formatting without attribute lookup.
    Example:

    >>> f = format_context("{{x}}")
    >>> f({"x": 10})
    '10'

    When calling *format_context*, arguments are bound and
    a new function is returned. When called with a context,
    its keys are extracted and formatted in *format_str*.

    Keys can be nested using a dot, for example:

    >>> f = format_context("{{x.y}}_{{z}}")
    >>> f({"x": {"y": 10}, "z": 1})
    '10_1'

    This function does not work with unbalanced braces.
    If a simple check fails, :exc:`.LenaValueError` is raised.
    If *format_str* is not a string, :exc:`.LenaTypeError` is raised.
    All other errors are raised only during formatting.
    If context doesn't contain the needed key,
    :exc:`.LenaKeyError` is raised.
    Note that string formatting can also raise a :exc:`ValueError`,
    so it is recommended to test your formatters before using them.
    """
    if not isinstance(format_str, str):
        raise LenaTypeError(
            "format_str must be a string, {} given".format(format_str)
        )

    # prohibit single or unbalanced braces
    if format_str.count('{') != format_str.count('}'):
        raise LenaValueError("unbalanced braces in '{}'".format(format_str))
    if '{' in format_str and not '{{' in format_str:
        raise LenaValueError(
            "double braces must be used for formatting instead of '{}'"
            .format(format_str)
        )

    # new format: now double braces instead of single ones.
    # but the algorithm may be left unchanged.
    format_str = format_str.replace("{{", "{").replace("}}", "}")
    new_str = []
    new_args = []
    prev_char = ''
    ind = 0
    within_field = False
    while ind < len(format_str):
        c = format_str[ind]
        if c != '{' and not within_field:
            prev_char = c
            new_str.append(c)
            ind += 1
            continue
        while c == '{' and ind < len(format_str):
            new_str.append(c)
            # literal formatting { are not allowed
            # if prev_char == '{':
            #     prev_char = ''
            #     within_field = False
            # else:
            prev_char = c
            within_field = True

            ind += 1
            c = format_str[ind]
        if within_field:
            new_arg = []
            while ind < len(format_str):
                if c in '}!:':
                    prev_char = c
                    within_field = False
                    new_args.append(''.join(new_arg))
                    break
                new_arg.append(c)
                ind += 1
                c = format_str[ind]
    format_str = ''.join(new_str)
    args = new_args
    def _format_context(context):
        new_args = []
        for arg in args:
            # LenaKeyError may be raised
            new_args.append(lena.context.get_recursively(context, arg))
        # other exceptions, like ValueError
        # (for bad string formatting) may be raised.
        s = format_str.format(*new_args)
        return s
    return _format_context


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
    otherwise :exc:`.LenaKeyError` is raised.

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

    If *d* is not a dictionary or if *keys* is not a string, a dict
    or a list, :exc:`.LenaTypeError` is raised.
    If *keys* is a dictionary with more than one key at some level,
    :exc:`.LenaValueError` is raised.
    """
    has_default = default is not _sentinel
    if not isinstance(d, dict):
        # for now we use only dictionaries, but this function
        # could be generalised to other containers (like sets).
        raise LenaTypeError(
            "need a dictionary, {} provided".format(d)
        )
    if isinstance(keys, str):
        # here empty substrings are skipped, but this is undefined.
        keys = [key for key in keys.split('.') if key]
    # todo: create dict_to_list and disable dict keys here?
    elif isinstance(keys, dict):
        new_keys = []
        while keys:
            if isinstance(keys, dict) and len(keys) != 1:
                raise LenaValueError(
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
            raise LenaTypeError(
                "all simple keys must be strings, "
                "{} given".format(keys)
            )
    else:
        raise LenaTypeError(
            "keys must be a dict, a string or a list of keys, "
            "{} given".format(keys)
        )

    for key in keys[:-1]:
        if key in d and isinstance(d.get(key), dict):
            d = d[key]
        elif has_default:
            return default
        else:
            raise LenaKeyError(
                "nested dict {} not found in {}".format(key, d)
            )

    if not keys:
        return d
    if keys[-1] in d:
        return d[keys[-1]]
    elif has_default:
        return default
    else:
        raise LenaKeyError(
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
    :exc:`.LenaTypeError` is raised.
    """
    if not all([isinstance(d, dict) for d in dicts]):
        raise LenaTypeError(
            "all dicts must be dictionaries, "
            "{} given".format(dicts)
        )

    level = kwargs.pop("level", -1)
    if kwargs:
        raise LenaTypeError(
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


def str_to_dict(s, value=_sentinel):
    """Create a dictionary from a dot-separated string *s*.

    If the *value* is provided, it becomes the value of 
    the deepest key represented by *s*.

    Dots represent nested dictionaries.
    If *s* is non-empty and *value* is not provided,
    then *s* must have at least two dot-separated parts
    (*"a.b"*), otherwise :exc:`.LenaValueError` is raised.
    If a *value* is provided, *s* must be non-empty.

    If *s* is empty, an empty dictionary is returned.

    Examples:

    >>> str_to_dict("a.b.c d")
    {'a': {'b': 'c d'}}
    >>> str_to_dict("output.changed", True)
    {'output': {'changed': True}}
    """
    if s == "":
        if value is _sentinel:
            return {}
        else:
            raise LenaValueError(
                "to make a dict with a value, "
                "provide at least one dot-separated key"
            )
    # """*s* can be a dictionary. In this case it is returned as it is.
    # If s were a dictionary, value mustn't had been allowed.
    # probably this is a bad design,
    # elif isinstance(s, dict):
    #     return s
    parts = s.split(".")
    if value is not _sentinel:
        parts.append(value)
    def nest_list(d, l):
        """Convert list *l* to nested dictionaries in *d*."""
        len_l = len(l)
        if len_l == 2:
            d.update([(l[0], l[1])])
        elif len_l < 2:
            raise LenaValueError(
                "to make a dict, provide at least two dot-separated values"
            )
        else:
            d.update([(l[0], nest_list({}, l[1:]))])
        return d
    d = nest_list({}, parts)
    return d


def str_to_list(s):
    """Like :func:`str_to_dict`, but return a flat list.

    If the string *s* is empty, an empty list is returned.
    This is different from *str.split*: the latter would
    return a list with one empty string.
    Contrarily to :func:`str_to_dict`, this function allows
    an arbitrary number of dots in *s* (or none).
    """
    if s == "":
        return []
    # s can't be a list. This function is not used as a general
    # interface (as str_to_dict could be).

    # s may contain empty substrings, like in "a..b"
    # this is not encouraged, of course, but may suit:
    # if there are two errors in some user's context logic,
    # they may compensate and not destroy all.
    # Another variant would be to treat empty strings
    # as whole context. The variant with '' seems more understandable
    # to the user.
    return s.split(".")


def to_string(d):
    """Convert a dictionary *d* to a string.

    Example:

    >>> d = {"a": 1, "b": {"c": 3}}
    >>> to_string(d)
    '{"a":1,"b":{"c":3}}'

    *d* can have nested subdictionaries, lists and other
    JSON-serializable items. *d* keys are sorted.

    .. note::
        The returned representation is terse and can be used for hashing
        (though more optimal solutions for that may exist).
        *d* can be not only a dictionary, but for example to hash a list
        one can simply convert it to a tuple.
        Use :class:`.Context` for a human-friendlier formatting.
        Use ``json.dumps`` for more flexibility.

    If an item is unserializable (for example, *d* contains a *set*),
    :exc:`.LenaValueError` is raised.

    .. versionadded:: 0.6
    """
    # keys should be sorted, because we want dictionary representations
    # to be invariant with respect to key order.
    try:
        s = dumps(d, skipkeys=False, separators=(',', ':'), sort_keys=True)
    except (TypeError, OverflowError, ValueError) as e:
        # JSON serialization errors.
        # A ValueError can raise from floats like inf or nan.
        # We don't raise a TypeError, for in general we test
        # only contexts and it means "a wrong context".
        raise LenaValueError(
            "can not serialize. " + repr(e)
        )
    return s


def update_nested(key, d, other):
    """Update *d[key]* with the *other* dictionary preserving data.

    If *d* doesn't contain the *key*, it is updated with *{key: other}*.
    If *d* contains the *key*, *d[key]* is inserted into *other[key]*
    (so that it is not overriden).
    If *other* contains *key* (and possibly more nested *key*-s),
    then *d[key]* is inserted into the deepest level
    of *other.key.key...* Finally, *d[key]* becomes *other*.

    Example:

    >>> context = {"variable": {"name": "x"}}
    >>> new_var_context = {"name": "n"}
    >>> update_nested("variable", context, copy.deepcopy(new_var_context))
    >>> context == {'variable': {'name': 'n', 'variable': {'name': 'x'}}}
    True
    >>>
    >>> update_nested("variable", context, {"name": "top"})
    >>> context == {
    ...    'variable': {'name': 'top',
    ...                 'variable': {'name': 'n', 'variable': {'name': 'x'}}}
    ... }
    True

    *other* is modified in general. Create that on the fly
    or use *copy.deepcopy* when appropriate.

    Recursive dictionaries (containing references to themselves)
    are strongly discouraged and meaningless when nesting.
    If *other[key]* is recursive, :exc:`.LenaValueError` may be raised.
    """
    # there was an idea to add a keyword argument copy_other
    # (by default True), but the user can do that him/herself
    # with copy.deepcopy when needed. Otherwise it would be 
    # unnecessary complication of this interface.

    # Only one key is nested. This encourages design when
    # 1) elements combine their contexts into one key
    # (like {"split_into_bins": {"variable": {}, "histogram": {}}})
    # 2) elements change only one key ("variable", "histogram",...).

    def get_most_nested_subdict_with(key, d):
        nested_dicts = []
        while True:
            if key in d:
                if d in nested_dicts:
                    raise LenaValueError(
                        "recursive *other* is forbidden"
                    )
                nested_dicts.append(d)
                d = d[key]
            else:
                return d

    if key in d:
        other_most_nested = get_most_nested_subdict_with(key, other)
        # insert d[key] at the lowest other.key.key....
        other_most_nested[key] = d[key]

    d[key] = other


def update_recursively(d, other, value=_sentinel):
    """Update dictionary *d* with items from *other* dictionary.

    *other* can be a dot-separated string. In this case
    :func:`str_to_dict` is used to convert it and the *value*
    to a dictionary.
    A *value* argument is allowed only when *other* is a string,
    otherwise :exc:`.LenaValueError` is raised.

    Existing values are updated recursively,
    that is including nested subdictionaries.
    Example:

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
    """
    # skip this docstring, because it's trivial.
    # Both *d* and *other* must be dictionaries,
    # otherwise :exc:`.LenaTypeError` is raised.
    # it would be cleaner to allow only dict as other,
    # but it's very clear and useful to allow
    # lena.context.update_recursively(context, "output.changed", True)
    if isinstance(other, str):
        other = str_to_dict(other, value)
    else:
        if value is not _sentinel:
            raise LenaValueError(
                "explicit value is allowed only when other is a string"
            )
    if not isinstance(d, dict) or not isinstance(other, dict):
        raise LenaTypeError(
            "d and other must be dicts, {} and {} provided".format(d, other)
        )
    for key, val in other.items():
        if not isinstance(val, dict):
            d[key] = val
        else:
            if key in d:
                if not isinstance(d[key], dict):
                    d[key] = {}
                update_recursively(d[key], other[key])
            else:
                d[key] = val
