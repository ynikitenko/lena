"""Group values using :class:`.GroupBy`."""
from warnings import warn

from lena.core import LenaTypeError, LenaKeyError, LenaValueError
from lena.context import format_context, to_string
from lena.context import make_include_exclude_tree
from lena.flow import get_context


class GroupBy(object):
    """Group values.

    Data is added during :meth:`fill`.
    Groups dictionary is available as :attr:`groups` attribute.
    :attr:`groups` is a mapping of *keys*
    (defined by *group_by* and *merge*)
    to lists of items with the same key.
    """

    def __init__(self, group_by="", merge=""):
        """*group_by* defines distinct hashable results
        for values from different groups.
        It is a dot-separated formatting string.
        Only the context part of the value is used for grouping
        (see :func:`context.format_context <.format_context>`).
        *group_by* can be a tuple of strings.
        In that case the hash value is combined from each
        part of the tuple.
        A tuple may be used when not all parts
        of context can be rendered (that would lead to an error
        or an empty string if they were combined
        into one formatting string).

        Setting *group_by* to an empty string (default)
        adds all values from the flow into one group.

        .. versionchanged:: 0.6
            *group_by* is no longer a function.

        .. versionadded:: 0.6
            *merge* allows ignoring keys.
        """
        if group_by == "" and merge == "":
            # for default arguments we adjust them manually here.
            merge = tuple()

        try:
            self._iet = make_include_exclude_tree(
                includes=group_by, excludes=merge
            )
        except TypeError:
            raise LenaTypeError(
                "group_by and merge should be strings or containers of strings"
            )

        self.groups = dict()

    def fill(self, val):
        """Find the corresponding group and fill it with *val*.

        A group key is calculated via *group_by* and *merge*.
        If no such key exists, a new group is created.

        If a formatting key was not found for *val*
        (or if no values for a tuple *group_by* could produce keys)
        :exc:`.LenaValueError` is raised.
        """
        # values are groupped by context
        context = get_context(val)
        key_dict = self._iet.get(context)

        try:
            # dicts are not hashable and can not be used
            # as keys in a dict. We need to transform them
            # to strings, but this can raise an error.
            key = to_string(key_dict)
        except LenaValueError:
            # alternatively we could ignore the value
            # (set an empty context) and provide an initialization key
            # for that behaviour.
            raise LenaValueError(
                "could not format context. Consider ignoring some keys "
                "in *merge*. value = {}".format(val)
            )

        if key in self.groups:
            self.groups[key].append(val)
        else:
            self.groups[key] = [val]

    def clear(self):
        """
        .. deprecated:: 0.6
           use the standard :meth:`reset` method.
        """
        warn("clear is deprecated since Lena 0.6. Use reset(). In:",
             DeprecationWarning, stacklevel=2)
        self.groups.clear()

    def compute(self):
        """Yield values groupped by distinct keys one by one.

        Each group is a tuple of filled values having the same key.
        """
        for grp in self.groups.values():
            yield grp

    def __eq__(self, other):
        if not isinstance(other, GroupBy):
            return NotImplemented
        return self._iet == other._iet

    def reset(self):
        """Remove all groups."""
        self.groups.clear()

    def update(self, val):
        """
        .. deprecated:: 0.6
           use the standard :meth:`fill` method.
        """
        warn("update is deprecated since Lena 0.6. Use fill. In:",
             DeprecationWarning, stacklevel=2)
        self.fill(val)


class _GroupBy(object):
    # old and deprecated GroupBy, left only for (deprecated) GroupPlots
    """Group values.

    Data is added during :meth:`fill`.
    Groups dictionary is available as :attr:`groups` attribute.
    :attr:`groups` is a mapping of *keys* (defined by *group_by*)
    to lists of items with the same key.
    """

    def __init__(self, group_by):
        """*group_by* is a function that returns
        distinct hashable results for values from different groups.
        It can be also a dot-separated formatting string.
        In that case only the context part of the value is used
        (see :func:`context.format_context <.format_context>`).
        *group_by* can be a tuple of strings or callables.
        In that case the hash value will be combined from each
        part of the tuple. A tuple may be used when not all parts
        of context can be always rendered (that would lead to an error
        or an empty string if they were combined
        into one formatting string).
        """
        self.groups = dict()
        # since context is always coupled with data here
        # (or if data would be solely used as a key),
        # we allow a general callable.
        def make_grpby(group_by):
            if callable(group_by):
                 return group_by
            elif isinstance(group_by, str):
                fc = format_context(group_by)
                return lambda val: fc(get_context(val))
            else:
                raise LenaTypeError(
                    "group_by must be a callable or a string, "
                    "{} provided".format(group_by)
                )

        def make_tupbg(group_bys):
            def tupgb(val):
                group = []
                for gb in group_bys:
                    try:
                        key = gb(val)
                    except LenaKeyError:
                        key = ""
                    group.append(key)
                if not any(group):
                    raise LenaValueError(
                        "no key found for {}".format(val)
                    )
                return tuple(group)
            return tupgb

        if isinstance(group_by, tuple):
            group_bys = [make_grpby(gb) for gb in group_by]
            self._group_by = make_tupbg(group_bys)
        else:
            self._group_by = make_grpby(group_by)

        # for equality testing
        self._init_group_by = group_by

    def fill(self, val):
        """Find the corresponding group and fill it with *val*.

        A group key is calculated by *group_by*.
        If no such key exists, a new group is created.

        If a formatting key was not found for *val*
        (or if no values for a tuple *group_by* could produce keys)
        :exc:`.LenaValueError` is raised.
        """
        try:
            key = self._group_by(val)
        except LenaKeyError:
            raise LenaValueError(
                "could not find a key for {}".format(val)
            )

        if key in self.groups:
            self.groups[key].append(val)
        else:
            self.groups[key] = [val]

    def clear(self):
        """
        .. deprecated:: 0.6
           use the standard :meth:`reset` method.
        """
        warn("clear is deprecated since Lena 0.6. Use reset(). In:",
                      DeprecationWarning, stacklevel=2)
        self.groups.clear()

    def __eq__(self, other):
        if not isinstance(other, GroupBy):
            return NotImplemented
        return self._init_group_by == other._init_group_by

    def reset(self):
        """Remove all groups."""
        self.groups.clear()

    def update(self, val):
        """
        .. deprecated:: 0.6
           use the standard :meth:`fill` method.
        """
        warn("update is deprecated since Lena 0.6. Use fill. In:",
             DeprecationWarning, stacklevel=2)
        self.fill(val)
