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


class RunIf(object):
    """Run a sequence only for selected values.

    Note
    ----
        In general, different flows are transformed
        to common data types (like histograms).
        In some complicated analyses (like in :class:`.SplitIntoBins`)
        there can appear values of very different types,
        for which additional transformation must be run.
        Use this element in such cases.

        *RunIf* is similar to :class:`.Filter`,
        but the latter can be used as a :class:`.FillInto`
        element inside :class:`.Split`.

        *RunIf* with a selector *select* (let us call its opposite
        *not_select*) is equivalent to

        .. code-block:: python

            Split(
                [
                    (
                        select,
                        Sequence(*args)
                    ),
                    not_select
                    # not selected values pass unchanged
                ],
                bufsize=1,
                copy_buf=False
            )

        and can be considered "syntactic sugar". Use :class:`.Split`
        for more flexibility.
    """

    def __init__(self, select, *args):
        """*select* is a function that accepts a value
        (maybe with context) and returns a boolean.
        It is converted to a :class:`.Selector`.
        See its specifications for available options.

        *args* are an arbitrary number of elements
        that will be run for selected values.
        They are joined into a :class:`.Sequence`.

        .. versionadded:: 0.4
        """
        # this element was present in Lena for a long time,
        # but it was called TransformIf
        # and was deprecated (undocumented).

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

        if len(args) == 1 and isinstance(args[0], lena.core.Sequence):
            self._seq = args[0]
        else:
            try:
                seq = lena.core.Sequence(*args)
            except lena.core.LenaTypeError:
                raise lena.core.LenaTypeError(
                    "args must be a Sequence or convertible to that, "
                    "{} provided".format(*args)
                )
            else:
                self._seq = seq

    def run(self, flow):
        """Run the sequence for selected values from the *flow*.

        Warning
        -------
            *RunIf* disrupts the flow: it feeds values to the sequence
            one by one, and yields the results.
            If the sequence depends on the complete flow
            (for example, yields the maximum element),
            this will be incorrect.
            The flow after *RunIf* is not disrupted.

        Not selected values pass unchanged.
        """
        for val in flow:
            if self._select(val):
                for result in self._seq.run([val]):
                    yield result
            else:
                yield val


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
