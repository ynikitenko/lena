from __future__ import print_function

import sys


class Print():
    """Print values passing through."""

    def __init__(self, before='', sep='', end='\n', transform=None):
        """*before* is a string appended before the first element in the item
        (which may be a container).

        *sep* separates elements, *end* is appended after the last element.

        *transform* is a function which transforms passing items
        (for example, it can select its specific fields).
        """
        # flush=True, file=sys.stdout
        self.before = before
        # *sep* and *end* keywords have the same semantics as in Python 3 *print()*.
        self.sep = sep
        self.end = end

        if transform is None:
            transform = lambda x: x
        self.transform = transform

    def __call__(self, value):
        """Print and return *value*."""
        print(self.before, self.transform(value), sep=self.sep, end=self.end)
        return value
