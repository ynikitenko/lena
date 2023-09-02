"""Sequence class."""
import sys

from . import lena_sequence
from . import adapters
from . import exceptions
from . import functions


class Sequence(lena_sequence.LenaSequence):
    """Sequence of elements, such that next takes input
    from the previous during *run*.

    :meth:`Sequence.run` must accept input flow.
    For sequence with no input data use :class:`Source`.
    """

    def __init__(self, *args):
        """*args* are objects
        which implement a method *run(flow)* or callables.

        *args* can be a single tuple of such elements.
        In this case one doesn't need to check argument type
        when initializing a Sequence in a general function.

        For more information about the *run* method and callables,
        see :class:`Run`.
        """
        seq = []

        for el in args:
            if hasattr(el, "run") and callable(el.run):
                seq.append(el)
            else:
                try:
                    # convert to a Run element
                    # (for example, el could be a Call)
                    run_el = adapters.Run(el)
                except exceptions.LenaTypeError:
                    raise exceptions.LenaTypeError(
                        "arguments must implement run method, "
                        "or be callable generators (convertible to Run), "
                        "{} given".format(el)
                    )
                else:
                    seq.append(run_el)
        # _name is used for representation.
        # Subclass must set its own name or provide a different repr
        self._name = "Sequence"

        super(Sequence, self).__init__(*seq)

    def run(self, flow):
        """Generator, which transforms the incoming flow.

        If this :class:`Sequence` is empty,
        the flow passes untransformed,
        with a small change.
        This function converts input flow to an iterator,
        so that it always contains both *iter* and *next* methods.
        This is done for the flow entering the first
        sequence element and exiting from the sequence.
        """
        flow = functions.flow_to_iter(flow)

        for el in self:
            flow = el.run(flow)

        flow = functions.flow_to_iter(flow)

        # This function is not a generator, but returns a generator.
        # The difference is very subtle.
        # Most important is that the function is evaluated immediately,
        # and raises in case of errors.
        return flow

    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return NotImplemented
        return self._seq == other._seq
