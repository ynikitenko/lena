"""Source sequence."""
from __future__ import print_function

from .lena_sequence import LenaSequence
from .sequence import Sequence
from .exceptions import LenaTypeError
from .functions import flow_to_iter


class Source(LenaSequence):
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
            raise LenaTypeError(
                "Source must be initialized with 1 argument or more (0 given)"
            )

        self._name = "Source"  # for repr
        super(Source, self).__init__(*args)

        first = self._data_seq[0]
        if not callable(first):
            raise LenaTypeError(
                "first element {} ".format(first)
                + "must be callable"
            )
        self._first = first

        if len(args) > 1:
            self._tail = Sequence(*(self._data_seq[1:]))
        else:
            self._tail = ()

    def __call__(self):
        """Generate flow."""
        flow = self._first()
        if self._tail:
            return self._tail.run(flow)
        else:
            return flow_to_iter(flow)

    def __eq__(self, other):
        if not isinstance(other, Source):
            return NotImplemented
        return self._seq == other._seq
