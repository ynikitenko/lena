"""Adapters to iterators from ``itertools``."""
import itertools

import lena.core


class Chain(object):
    """Chain generators.

    :class:`Chain` can be used as a ``Source`` to generate data.

    Example:

    >>> c = lena.flow.Chain([1, 2, 3], ['a', 'b'])
    >>> list(c())
    [1, 2, 3, 'a', 'b']
    """
    def __init__(self, *iterables):
        """*iterables* will be chained during ``__call__()``,
        that is after the first one is exhausted,
        the second is called, etc.
        """
        self._chain = itertools.chain(*iterables)

    def __call__(self):
        """Generate values from chained iterables."""
        for val in self._chain:
            yield val


class CountFrom(object):
    """Generate numbers from *start* to infinity, with *step* between values.

    Similar to :func:`itertools.count`.
    """
    def __init__(self, start=0, step=1):
        self._it = itertools.count(start, step)

    def __call__(self):
        """Yield values from *start* to infinity with *step*."""
        for val in self._it:
            yield val


class ISlice(object):
    """Slice iterable from *start* to *stop* with *step*."""
    def __init__(self, *args):
        """Initialization:

        :class:`ISlice` (*stop*)

        :class:`ISlice` (*start, stop* [*, step*])

        Similar to :func:`itertools.islice` or :func:`range`.
        """
        self._islice = lambda iterable: itertools.islice(iterable, *args)
        self._indices = self._islice(itertools.count(0))
        self._next_index = -1
        self._index = 0

    def fill_into(self, element, value):
        """Fill *element* with *value*.

        Element must have a ``fill(value)`` method.
        """
        if self._index > self._next_index:
            try:
                self._next_index = next(self._indices)
            except StopIteration:
                raise lena.core.LenaStopFill()
        if self._index == self._next_index:
            element.fill(value)
        self._index += 1

    def run(self, flow):
        """Yield values from *start* to *stop* with *step*."""
        for val in self._islice(flow):
            yield val
