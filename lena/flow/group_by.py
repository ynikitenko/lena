"""Group data using :class:`.GroupBy` class."""
import lena.core
import lena.flow


class GroupBy(object):
    """Group values.

    Data is added during :meth:`update`.
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

        If *group_by* is not a callable or a string,
        :exc:`.LenaTypeError` is raised.
        """
        self.groups = dict()
        if callable(group_by):
            # callable(value) is allowed for generality.
            # I use group_by exclusively with context,
            # and the only example I can imagine when it can probe value
            # is histograms with same variables
            # but with different ranges (one wouldn't be able
            # to plot graphs with them without changing context though).
            # This is a weak example, because this information
            # could be added to context.
            self._group_by = group_by
        elif isinstance(group_by, str):
            fc = lena.context.format_context(group_by)
            self._group_by = lambda val: fc(lena.flow.get_context(val))
        else:
            raise lena.core.LenaTypeError(
                "group_by must be a callable or a string, "
                "{} provided".format(group_by)
            )

    def update(self, val):
        """Find a group for *val* and add it there.

        A group key is calculated by *group_by*.
        If no such key exists, a new group is created.

        If a formatting key was not found for *val*,
        :exc:`~LenaValueError` is raised.
        """
        try:
            key = self._group_by(val)
        except lena.core.LenaKeyError:
            raise lena.core.LenaValueError(
                "could not find a key for {}".format(val)
            )

        if key in self.groups:
            self.groups[key].append(val)
        else:
            self.groups[key] = [val]

    def clear(self):
        """Remove all groups."""
        self.groups.clear()
