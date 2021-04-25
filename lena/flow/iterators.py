"""Adapters to iterators from ``itertools``."""
try:
    from future_builtins import zip
except ModuleNotFoundError:
    # not existent in Python 3.9
    pass
import collections
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
    """Slice data flow from *start* to *stop* with *step*."""

    def __init__(self, *args):
        """Initialization:

        :class:`ISlice` (*stop*)

        :class:`ISlice` (*start, stop* [*, step*])

        Similar to :func:`itertools.islice` or :func:`range`.
        Negative indices for *start* and *stop* are supported
        during :meth:`run`.

        Examples:

        >>> ISlice(1000)  # doctest: +SKIP

        analyse only one thousand first events (no other values
        from flow are generated).
        Use it for quick checks of data on small subsamples.

        >>> ISlice(-1)  # doctest: +SKIP

        yields all elements from the flow except the last one.

        >>> ISlice(1, -1)  # doctest: +SKIP

        yields all elements from the flow
        except the first and the last one.
        
        Note that in case of negative indices it is necessary
        to store abs(start) or abs(stop) values in memory.
        For example, to discard the last 200 elements
        one has to a) read the whole flow, b) store 200 elements
        during each iteration.
        """
        # todo: rename to Slice in the next release.
        from itertools import islice
        if all([val is None or val >= 0 for val in args]):
            # if step=0, then error is raised not here,
            self._islice = lambda iterable: islice(iterable, *args)
            # but here when we use this lambda:
            try:
                self._indices = self._islice(itertools.count(0))
            except ValueError as err:
                raise lena.core.LenaValueError(err)
            self._next_index = -1
            self._index = 0
        else:
            # negative indices
            s = slice(*args)
            self._start, self._stop, step = s.start, s.stop, s.step
            # if step is None, it is 1 by default.
            step = step or 1
            if step <= 0:
                raise lena.core.LenaValueError(
                    "step must be a natural number (integer >= 1)"
                )
            if step != 1:
                # non-trivial step is computed here.
                self.run = lambda flow: islice(self._run_negative_islice(flow),
                                               None, None, step)
            else:
                self.run = lambda flow: self._run_negative_islice(flow)
            self._step = step

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

    def _run_negative_islice(self, flow):
        from collections import deque
        start, stop, step = self._start, self._stop, self._step

        def fill_deque(flow, maxlen):
            # Fill a deque with exactly maxlen values from *flow*
            # and return that. All other values remain in *flow*.
            d = deque(maxlen=maxlen)
            for _, val in zip(range(maxlen), flow):
                d.appendleft(val)
            return d

        if start is None:
            # we have only a stop, which is negative.
            # yield all values except the last (-stop) ones.
            to_skip = -stop
            # initially fill the deque
            d = fill_deque(flow, maxlen=to_skip)
            for val in flow:
                yield d.pop()
                d.appendleft(val)
        else:
            if start >= 0:
                # skip *start* values
                for _ in zip(range(start), flow):
                    pass
                if stop is None:
                    for val in flow:
                        yield val
                    return
                # stop is negative
                d = fill_deque(flow, -stop)
                if len(d) < -stop:
                    # stop is before start
                    return
                for val in flow:
                    yield d.pop()
                    d.appendleft(val)
            else:
                # start < 0
                if stop is None:
                    d = deque(flow, maxlen=-start)
                    while True:
                        try:
                            yield d.popleft()
                        except IndexError:
                            return
                if stop <= start:
                    return
                if stop < 0:
                    # will exhaust all flow and fill the deque
                    # with last maxlen elements
                    d = deque(flow, maxlen=-start)
                    ind = 0
                    # imitate
                    # for val in d[:stop-start]:
                    # which is not possible with a deque.
                    while ind < len(d) + stop:
                        yield d.popleft()
                        ind += 1
                else:
                    # stop is positive
                    ind = 0
                    d = deque(maxlen=-start)
                    stop_missed = False
                    for val in flow:
                        # we know that we'll never yield anything
                        # because stop is too small.
                        if ind >= stop - start:
                            return
                        d.append(val)
                        ind += 1
                    # deque is filled, flow is finished.
                    # we begin again from the start of the deque.
                    ind -= len(d)
                    while ind < stop:
                        try:
                            yield d.popleft()
                        except IndexError:
                            return
                        ind += 1


    def run(self, flow):
        """Yield values from *start* to *stop* with *step*."""
        return self._islice(flow)
