"""Source sequence."""
from __future__ import print_function

from . import lena_sequence
from . import sequence
from . import exceptions
from . import functions


class Source(lena_sequence.LenaSequence):
    """Sequence with no input flow."""

    def __init__(self, *args):
        """First argument is the initial element with no input flow.
        Following arguments (if present) form a sequence of elements,
        each accepting computational flow from the previous element.

        >>> from lena.flow import CountFrom, Slice
        >>> s = Source(CountFrom(), Slice(5))
        >>> # iterate in a cycle
        >>> for i in s():
        ...     if i == 5:
        ...         break
        ...     print(i, end=" ")
        0 1 2 3 4 
        >>> # if called twice, results depend on the generator
        >>> list(s()) == list(range(5, 10))
        True

        For a *sequence* which transforms the incoming flow,
        use :class:`Sequence`.
        """
        if not args:
            raise exceptions.LenaTypeError(
                "Source must be initialized with 1 argument or more (0 given)"
            )

        self._name = "Source"  # for repr
        super(Source, self).__init__(*args)

        first = self._seq[0]
        if not callable(first):
            raise exceptions.LenaTypeError(
                "first element {} ".format(first)
                + "must be callable"
            )
        self._first = first

        if len(args) > 1:
            self._sequence = sequence.Sequence(*(self._seq[1:]))
        else:
            self._sequence = ()

    def __call__(self):
        """Generate flow."""
        flow = self._first()
        if self._sequence:
            return self._sequence.run(flow)
        else:
            return functions.flow_to_iter(flow)

    def __eq__(self, other):
        if not isinstance(other, Source):
            return NotImplemented
        return self._seq == other._seq
