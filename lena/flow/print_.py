from __future__ import print_function

import sys


class Print():
    """Print values passing through.

    keyword arguments:

    *before* is a string appended before the first element in the item (which may be a container).

    *sep* separates elements, *end* is appended after the last element.

    *transform* is a function which transforms passing items.
    """

    def __init__(self, before='', sep='', end='\n', transform=None):
                 # **kwargs):
            # flush=True, file=sys.stdout
        self.before = before
        # *sep* and *end* keywords have the same semantics as in Python 3 *print()*.
        self.sep = sep
        self.end = end
        # self.file = file
        # self.flush = flush
        if transform is None:
            transform = lambda x: x
        self.transform = transform
        # if kwargs:
        #     self._data = kwargs.pop("data", None)

    def run(self, flow):
        """Print items from the *flow*.
        """
        for val in flow:
            print(self.before, self.transform(val), sep=self.sep, end=self.end, 
                    # file=self.file, flush=self.flush
                    )
            yield val
