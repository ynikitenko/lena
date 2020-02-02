"""Group data using :class:`GroupBy` class."""
from __future__ import print_function

import lena.core
import lena.flow


class GroupBy(object):
    """Group data.

    Data is added during :meth:`update`.
    Groups are available as :attr:`groups` attribute.

    Groups is a mapping of *keys* (return values of *group_by*)
    and lists of items with the same key.
    """

    def __init__(self, group_by):
        """Combine data with same attributes.

        *group_by* is a function, which returns
        distinct hashable results for items from different groups.

        It can be a dot-separated string, which corresponds to context.
        Otherwise, :exc:`~lena.core.LenaTypeError` is raised.
        """
        self.groups = dict()
        if callable(group_by):
            self._group_by = group_by
        elif isinstance(group_by, str):
            self._group_by = lambda val: lena.context.get_recursively(
                lena.flow.get_context(val), group_by
            )
        else:
            raise lena.core.LenaTypeError(
                "group_by must be a callable or a string, "
                "{} provided".format(group_by)
            )

    def update(self, val):
        """Find a group for *val* and add it there.

        A group key is calculated by *group_by*.
        If no such key exists, a new group is created.
        """
        key = self._group_by(val)
        if key in self.groups:
            self.groups[key].append(val)
        else:
            self.groups[key] = [val]

    def clear(self):
        """Remove all groups."""
        self.groups.clear()
