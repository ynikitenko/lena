"""FillSeq sequence and its helpers."""

from .lena_sequence import LenaSequence
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


class FillSeq(LenaSequence):
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
        if not args:
            raise exceptions.LenaTypeError(
                "FillSeq must have at least one element"
            )

        self._name = "FillSeq"  # for repr
        super(FillSeq, self).__init__(*args)

        seq = []
        last = self._data_seq[-1]

        if not callable(getattr(last, "fill", None)):
            raise exceptions.LenaTypeError(
                "the last argument must implement fill method, "
                "{} given".format(last)
            )
        # convert all elements except last to FillInto (if needed)
        for el in self._data_seq[:-1]:
            if hasattr(el, "fill_into") and callable(el.fill_into):
                seq.append(el)
            else:
                # try to convert to FillInto (e.g. Call)
                try:
                    fill_into_el = adapters.FillInto(el, explicit=False)
                except exceptions.LenaTypeError:
                    raise exceptions.LenaTypeError(
                        "arguments must implement fill_into method, "
                        "or be convertible to FillInto, "
                        "{} given".format(el)
                    )
                else:
                    seq.append(fill_into_el)
        seq.append(last)
        # transform FillInto elements into _Fill
        fill_el = last
        for el in reversed(seq[:-1]):
            fill_el = _Fill(el, fill_el)
        # note that self._data_seq consists of original FillInto elements.
        self._fill_el = fill_el
        # self for these methods is different
        self.fill = fill_el.fill
        self._data_seq = seq

    def fill(self, value):
        """Fill *value* into an *element*.

        *Value* is transformed by every element of
        this sequence, and after that fills the last element.
        """
        raise exceptions.LenaNotImplementedError

    def __eq__(self, other):
        if not isinstance(other, FillSeq):
            return NotImplemented
        return self._seq == other._seq
