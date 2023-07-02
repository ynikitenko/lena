"""FillSeq sequence and its helpers."""
from __future__ import print_function

from . import lena_sequence
from . import adapters
from . import exceptions


class _Fill(object):
    """Implement a chained *fill(value)* method."""

    def __init__(self, fill_into_el, fill_el):
        """*fill_into_el* has *fill_into* method,
        which fills the *fill_el* (which has *fill* method).
        """
        self._fill_into_el = fill_into_el
        self._fill_el = fill_el

    def fill(self, value):
        """Transform *value* in *fill_into_el* and fill *fill_el*."""
        self._fill_into_el.fill_into(self._fill_el, value)


class FillSeq(lena_sequence.LenaSequence):
    """Sequence with :meth:`fill` method.

    Sequence of :class:`.FillInto` elements,
    each filling the following ones.
    The last element has *fill* method and is filled itself.

    Each element must be convertible to *FillInto*.
    """

    def __init__(self, *args):
        """*args* except the last one are
        :class:`.FillInto` elements.
        The last argument must have a *fill* method.

        If any argument
        could not be converted to :class:`.FillInto`,
        or if the last argument has no *fill* method,
        or if an *args* is empty,
        :exc:`.LenaTypeError` is raised.
        """
        self._seq = []
        self._name = "FillSeq"

        if not args:
            raise exceptions.LenaTypeError(
                "FillSeq must have at least one element"
            )
        if not callable(getattr(args[-1], "fill", None)):
            raise exceptions.LenaTypeError(
                "the last argument must implement fill method, "
                "{} given".format(args[-1])
            )
        # convert all elements except last to FillInto (if needed)
        for elem in args[:-1]:
            fill_into = getattr(elem, "fill_into", None)
            if callable(fill_into):
                # default method found
                self._seq.append(elem)
            else:
                # try to convert to FillInto
                try:
                    fill_into_elem = adapters.FillInto(elem, explicit=False)
                except exceptions.LenaTypeError:
                    raise exceptions.LenaTypeError(
                        "arguments must implement fill_into method, "
                        "or be convertible to FillInto, "
                        "{} given".format(elem)
                    )
                else:
                    self._seq.append(fill_into_elem)
        self._seq.append(args[-1])
        # transform FillInto elements to _Fill
        fill_el = args[-1]
        for el in reversed(self._seq[:-1]):
            fill_el = _Fill(el, fill_el)
        # note that self._seq consists of original FillInto elements.
        self._fill_el = fill_el
        # self for these methods is different
        self.fill = fill_el.fill

    def fill(self, value):
        """Fill *value* into an *element*.

        *Value* is transformed by every element of
        this sequence, and after that fills the last element.
        """
        raise exceptions.LenaNotImplementedError
