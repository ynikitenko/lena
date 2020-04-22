"""Elements for mathematical calculations."""
import copy

import lena.core
import lena.flow


class Mean(object):
    """Calculate mean (average) of input values."""

    def __init__(self, start=0, pass_on_empty=False):
        """*start* is the initial value of sum.

        If *pass_on_empty* is True, then if nothing was filled,
        don't yield anything.
        By default it raises an error (see :meth:`compute`)."""
        # Initialization resets this object.
        # start is similar to Python's builtin *sum* start.
        # a special keyword would be needed
        # if we want default context of other type
        self._start = start
        self._pass_on_empty = pass_on_empty
        self.reset()

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (if missing, it is considered empty)
        is saved for output.
        """
        data, context = lena.flow.get_data_context(value)
        self._sum += data
        self._count += 1
        self._cur_context = context

    def compute(self):
        """Calculate mean and yield.

        If the current context is not empty, yield *(mean, context)*.
        Otherwise yield only *mean*.

        If no values were filled (count is zero),
        mean can't be calculated and
        :exc:`.LenaZeroDivisionError` is raised.
        This can be changed to yielding nothing
        if *pass_on_empty* was initialized to True.
        """
        if not self._count:
            if self._pass_on_empty:
                return
            raise lena.core.LenaZeroDivisionError(
                "can't calculate average. No values were filled"
            )
        mean = self._sum / float(self._count)
        if not self._cur_context:
            yield mean
        else:
            yield (mean, copy.deepcopy(self._cur_context))

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
        The last *context* value (considered empty if missing)
        sets the current context.
        """
        data, context = lena.flow.get_data_context(value)
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
            yield (self._sum, copy.deepcopy(self._cur_context))

    def reset(self):
        """Reset sum and context.

        Sum is reset to *start* value and context to {}.
        """
        self._sum = copy.deepcopy(self._start)
        self._cur_context = {}
