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

        >>> from lena.flow import CountFrom
        >>> s = Source(CountFrom())
        >>> for i in s():
        ...     if i == 5:
        ...         break
        ...     print(i, end=" ")
        0 1 2 3 4 

        For a *sequence* which transforms the incoming flow,
        use :class:`Sequence`.
        """
        if not args:
            raise exceptions.LenaTypeError(
                "Source must be initialized with 1 argument or more (0 given)"
            )
        if not callable(args[0]):
            raise exceptions.LenaTypeError(
                "first element {} ".format(args[0])
                + "must be callable"
            )
        self._first = args[0]
        if len(args) > 1:
            self._sequence = sequence.Sequence(*args[1:])
        else:
            self._sequence = []
        # _seq is an attribute of LenaSequence
        self._seq = [self._first]
        self._seq.extend(self._sequence)

    def __call__(self):
        """Generate flow."""
        arg = self._first()
        if self._sequence:
            return self._sequence.run(arg)
        else:
            return functions.flow_to_iter(arg)
