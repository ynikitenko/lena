"""Source sequence."""

from __future__ import print_function

import warnings

from .lena_sequence import LenaSequence
from .sequence import Sequence
from .exceptions import LenaTypeError
from .functions import flow_to_iter


class Source(LenaSequence):
    """Sequence with no input flow."""

    def __init__(self, *args):
        """First argument is the initial element with no input flow.
        It can be an an object with a generator function `__call__()`
        or an iterable.
        Following arguments (if present) form a sequence of elements,
        each accepting computational flow from the previous element.

        >>> from lena.flow import CountFrom, Slice
        >>> s = Source(CountFrom(), Slice(5))
        >>> list(s()) == list(range(5))
        True

        For a *sequence* that transforms the incoming flow
        use :class:`Sequence`.
        """
        if not args:
            raise LenaTypeError(
                "Source must be initialized with 1 argument or more (0 given)"
            )

        self._name = "Source"  # for repr
        super(Source, self).__init__(*args)

        first = self._data_seq[0]
        if not (callable(first) or hasattr(first, "__iter__")):
            # I think checking __iter__ is the same as calling
            # isinstance(first, collections.abc.Iterable)
            raise LenaTypeError(
                "first element {} ".format(first)
                + "must be callable or iterable"
            )
        # hint: may additionaly check that elements of the iterable
        # are not Lena elements, to avoid errors like
        # Source((cnt0, Slice(1))). However, an error in Source will be
        # discovered quickly (unless it is within a Split).
        self._first = first
        if not callable(first) and not self._data_seq[1:]:
            # a sequence with only one iterable. An iter would suffice.
            warnings.warn(
                "the only element of Source is an iterable. "
                "Is a Source needed here? Consider using iter().",
                UserWarning, stacklevel=2
            )

        if len(args) > 1:
            self._tail = Sequence(*(self._data_seq[1:]))
        else:
            self._tail = ()

    def __call__(self):
        """Generate flow."""
        first = self._first
        if callable(first):
            # a generator
            flow = first()
        elif hasattr(first, "__iter__"):
            # iterable
            flow = first
        if self._tail:
            return self._tail.run(flow)
        else:
            return flow_to_iter(flow)

    def __eq__(self, other):
        if not isinstance(other, Source):
            return NotImplemented
        return self._seq == other._seq
