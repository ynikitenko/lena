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
        self._seq = []

        # Sequence can be initialized from a single tuple
        if len(args) == 1 and isinstance(args[0], tuple):
            args = args[0]

        for elem in args:
            run = getattr(elem, "run", None)
            if callable(run):
                self._seq.append(elem)
            else:
                try:
                    run_elem = adapters.Run(elem)
                except exceptions.LenaTypeError:
                    raise exceptions.LenaTypeError(
                        "arguments must implement run method, "
                        "or be callable generators (convertible to Run), "
                        "{} given".format(elem)
                    )
                else:
                    self._seq.append(run_elem)
        self._name = "Sequence"
        # we don't call super init (yet),
        # because it has no variables (and no init)
        # https://softwareengineering.stackexchange.com/a/318171/42050

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

        for elem in self._seq:
            flow = elem.run(flow)

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
