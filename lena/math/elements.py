"""Elements for mathematical calculations."""
import copy

import lena.core
import lena.flow


class Mean(object):
    """Calculate mean (average) of input values."""

    def __init__(self, start=0):
        """*start* is the initial value of sum."""
        # Initialization resets this object.
        # start is similar to Python's builtin *sum* start.
        # a special keyword would be needed
        # if we want default context of other type
        self._start = start
        self.reset()

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (if missing, it is considered empty)
        is saved for output.
        """
        data, context = (lena.flow.get_data(value),
                         lena.flow.get_context(value))
        self._sum += data
        self._count += 1
        self._cur_context = context

    def compute(self):
        """Calculate mean and yield.

        If the current context is not empty, yield *(mean, context)*.
        Otherwise yield only *mean*.

        If no values were filled (count is zero),
        mean can't be calculated and
        :exc:`~lena.core.LenaRuntimeError` is raised.
        """
        if not self._count:
            raise lena.core.LenaRuntimeError(
                "can't calculate average. No values were filled"
            )
        mean = self._sum / float(self._count)
        if not self._cur_context:
            yield mean
        else:
            yield (mean, self._cur_context)

    def reset(self):
        """Reset sum, count and context.

        Sum is reset to *start* value, count to zero and context to {}.
        """
        self._sum = copy.deepcopy(self._start)
        self._count = 0
        self._cur_context = {}


class Sum(object):
    """Calculate sum of input values."""

    def __init__(self, start=0):
        """*start* is the initial value of sum."""
        # start is similar to Python's builtin *sum* start.
        # a special keyword would be needed
        # if we want default context of other type
        self._start = start
        self.reset()

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (if missing, it is considered empty)
        is saved for output.
        """
        data, context = (lena.flow.get_data(value),
                         lena.flow.get_context(value))
        self._sum += data
        self._cur_context = context

    def compute(self):
        """Calculate the sum and yield.

        If the current context is not empty, yield *(sum, context)*.
        Otherwise yield only *sum*.
        """
        if not self._cur_context:
            yield self._sum
        else:
            yield (self._sum, self._cur_context)

    def reset(self):
        """Reset sum, count and context.

        Sum is reset to *start* value, count to zero and context to {}.
        """
        self._sum = copy.deepcopy(self._start)
        self._cur_context = {}
