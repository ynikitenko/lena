"""Elements that work with the flow."""
import collections
import copy
import itertools

import lena.core
from . import functions


class Count(object):
    """Count items that pass through.

    Example:

    >>> flow = [0, 1, 2]
    >>> c = Count("my_counter")
    >>> list(c.run(iter(flow))) == [
    ...     0, 1, (2, {'my_counter': 3})
    ... ]
    True
    """

    def __init__(self, name="count", count=0):
        """*name* is this counter's name (added to context).
        One can use the default name if *Count* is filled,
        but it is recommended to provide
        a meaningful name in a *Run* element.

        *count* is the initial counter.
        It is added to all countings.
        It is set to 0 during :meth:`reset`.

        *name* and *count* are public attributes.
        """

        self.name = name
        self.count = count
        # todo: move to update_context.
        self._cur_context = {}

    def fill(self, value):
        """Increase *count* and set current context from *value*."""
        self.count += 1
        self._cur_context = lena.flow.get_context(value)

    def compute(self):
        """Yield *(count, context)*.

        *context* is taken from the last filled value and 
        is updated with *{self.name: self.count}*.
        """
        # compute is idempotent
        self._cur_context.update({self.name: self.count})
        yield (self.count, copy.deepcopy(self._cur_context))

    def fill_into(self, element, value):
        """Fill *element* with *value* and increase *count*.

        *value* context is updated with *{self.name: self.count}*.

        *element* must have a ``fill(value)`` method.
        """
        self.count += 1
        data, context = lena.flow.get_data_context(value)
        context.update({self.name: self.count})
        element.fill((data, context))

    def reset(self):
        """Set *count* to zero. Clear current context."""
        # note that we reset not to the initialized count.
        self.count = 0
        self._cur_context = {}

    def run(self, flow):
        """Yield incoming values and increase *count*.

        After the flow is exhausted,
        update last value's context with *{self.name: self.count}*.

        If the *flow* was empty, nothing is yielded
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
        # not only last. But it may be better with a sort of zip.
        count = 1
        for val in flow:
            yield prev_val
            count += 1
            prev_val = val
        # we don't overwrite the count field, in case of a simultaneous
        # filling in another place.
        self.count += count

        val = prev_val
        data, context = lena.flow.get_data_context(val)
        # we yield the total count from all threads.
        # This is the same result (mod context) as for compute.
        context.update({self.name: self.count})
        yield (data, context)

    def __eq__(self, other):
        if not isinstance(other, Count):
            return NotImplemented
        return (self.name == other.name and self.count == other.count
                and self._cur_context == other._cur_context)

    def __repr__(self):
        return "Count(name=\"{}\", count={})".format(self.name, self.count)


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


class RunningChunkBy(object):
    """Split the flow into shifting intersecting chunks."""

    def __init__(self, chunk_size, container=tuple, from_iterable=False):
        """*container* is a callable constructor for new chunks.

        If *container* initialization requires an iterable,
        set *from_iterable* to ``True``.

        Example::

        >>> rcb = RunningChunkBy(2)
        >>> flow = range(5)
        >>> list(rcb.run(flow))
        >>> [(0, 1), (1, 2), (2, 3), (3, 4)]
        """
        # todo: add example of event selection
        self._cs = chunk_size
        if not callable(container):
            raise LenaTypeError(
                "container must be a callable constructor for new chunks"
            )
        self._container = container
        self._from_iterable = bool(from_iterable)
        # todo: create FillInto

    def run(self, flow):
        """If the *flow* contains fewer than *chunk_size* values,
        nothing is yielded.
        Prepend or append the *flow* with default elements
        to change this.
        """
        chunk_size = self._cs
        container = self._container
        # if flow appears to be a container, this will work correctly
        flow = iter(flow)

        chunk = collections.deque(itertools.islice(flow, chunk_size),
                                  maxlen=chunk_size)

        # we can't use isinstance(tuple), because
        # container is its constructor, not an object
        if (container == tuple) or self._from_iterable:
            for val in flow:
                yield container(chunk)
                chunk.append(val)  # head is popped automatically
            # flow contained enough elements
            if len(chunk) == chunk_size:
                yield container(chunk)
        else:
            # e.g. namedtuple
            for val in flow:
                yield container(*chunk)
                chunk.append(val)
            if len(chunk) == chunk_size:
                yield container(*chunk)


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

    def __eq__(self, other):
        return isinstance(other, End)

    def __repr__(self):
        return "End()"
