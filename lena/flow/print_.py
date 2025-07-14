from __future__ import print_function

import sys


# do not develop this class much, for it will be most likely
# substituted by the standard print.
class Print():
    """Print values passing through."""

    def __init__(self, transform=None, before='', sep='', end='\n'):
        """*transform* is a function which transforms passing items
        (for example, it can select its specific fields).

        *before* is a string appended before the first element in the item
        (which may be a container).

        The first argument is defined according to its type:
        a function is considered *transform*, while a string is considered *before*.

        *sep* separates elements, *end* is appended after the last element.
        """
        # flush=True, file=sys.stdout
        if isinstance(transform, str):
            before, transform = (transform, before)
        self.before = before
        # *sep* and *end* keywords have the same semantics as in Python 3 *print()*.
        self.sep = sep
        self.end = end
        self.transform = transform

    def __call__(self, value):
        """Print and return *value*."""
        if self.transform is None:
            print(self.before, value, sep=self.sep, end=self.end)
        else:
            print(self.before, self.transform(value),
                  sep=self.sep, end=self.end)
        return value

    def __eq__(self, other):
        if not isinstance(other, Print):
            return NotImplemented
        return (self.before == other.before and self.sep == other.sep and
                self.end == other.end and self.transform == other.transform)
