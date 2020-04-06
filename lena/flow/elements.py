"""Elements which work with the flow."""
import copy

import lena.core
from . import functions


class Count(object):
    """Count items that pass through.

    After the flow is exhausted, add {*name*: count} to the *context*.

    Example:

    >>> flow = [1, 2, 3, "foo"]
    >>> c = Count("counter")
    >>> list(c.run(iter(flow))) == [
    ...     1, 2, 3, ('foo', {'counter': 4})
    ... ]
    True
    """

    def __init__(self, name="counter"):
        """*name* is this Counter's name."""

        self._name = name
        self._count = 0
        self._cur_context = {}

    def fill(self, value):
        """Increase counter and set context from *value*."""
        self._count += 1
        self._cur_context = lena.flow.get_context(value)

    def compute(self):
        """Yield *(count, context)* and reset self."""
        self._cur_context.update({self._name: self._count})
        yield (self._count, copy.deepcopy(self._cur_context))
        # reset
        self._count = 0
        self._cur_context = {}

    def fill_into(self, element, value):
        """Fill *element* with *value* and increase counter.

        *value* context is updated with the counter.

        Element must have a ``fill(value)`` method.
        """
        self._count += 1
        data, context = lena.flow.get_data_context(value)
        context.update({self._name: self._count})
        element.fill((data, context))

    def run(self, flow):
        """Yield incoming values and increase counter.

        When the incoming flow is exhausted,
        update last value's context with *(count, context)*.

        If the flow was empty, nothing is yielded
        (so *count* can be zero only from :meth:`compute`).
        """
        try:
            prev_val = next(flow)
        except StopIteration:
            # otherwise it will be an error since PEP 479
            # https://stackoverflow.com/a/51701040/952234
            return
            # raise StopIteration
        # todo: add an option to update context with every count,
        # not only last
        count = 1
        for val in flow:
            yield prev_val
            count += 1
            prev_val = val
        val = prev_val
        data, context = lena.flow.get_data_context(val)
        context.update({self._name: count})
        yield (data, context)


class TransformIf(object):
    """Transform selected flow.

    In general this sequence should not be used,
    and different flows should be transformed
    to common data types (like Histograms) before merging.
    In some cases, however, there emerge values of very different types
    (like in :class:`~lena.flow.SplitIntoBins`),
    and this class may be useful.
    Todo: probably it should be structure-transparent
    (that is work for histogram content directly)

    Warning
    -------
        This class may be changed or deleted.
    """

    def __init__(self, select, seq):
        """*select* is converted to :class:`~lena.flow.Selector`.
        See its specifications for available options.

        *seq* is converted to :class:`~lena.core.Sequence`.
        """
        if isinstance(select, lena.flow.Selector):
            self._select = select
        else:
            try:
                select = lena.flow.Selector(select)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "select must be a Selector or convertible to that, "
                    "{} provided".format(select)
                )
            else:
                self._select = select
        if isinstance(seq, lena.core.Sequence):
            self._seq = seq
        else:
            try:
                seq = lena.core.Sequence(seq)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "seq must be a Sequence or convertible to that, "
                    "{} provided".format(seq)
                )
            else:
                self._seq = seq

    def run(self, flow):
        """Transform selected flow.

        Not selected values pass unchanged.
        """
        for value in flow:
            if self._select(value):
                # transform with self._seq
                for result in self._seq.run([value]):
                    yield result
            else:
                # not selected pass unchanged
                yield value


class End(object):
    """Stop sequence here."""

    def run(self, flow):
        """Exhaust all preceding flow and stop iteration
        (yield nothing to the following flow).
        """
        for val in flow:
            pass
        return
        # otherwise it won't be a generator
        yield "unreachable"
