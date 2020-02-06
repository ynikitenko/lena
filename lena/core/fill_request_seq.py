from __future__ import print_function

from . import lena_sequence
from . import fill_compute_seq
from . import check_sequence_type
from . import sequence
from . import adapters
from . import exceptions


class FillRequestSeq(lena_sequence.LenaSequence):
    """Sequence with one :class:`FillRequest` element.

    Input flow is preprocessed with the *Sequence*
    before the *FillRequest* element,
    then it fills the *FillRequest* element.
    After the flow is exhausted
    and the results are yielded from the *FillRequest*,
    they are postprocessed with the *Sequence* after
    that element.
    """

    def __init__(self, *args, **kwargs):
        """*args* form a sequence with a *FillRequest* element.

        If *args* contain several *FillRequest* elements,
        only the first one is chosen
        (the subsequent ones are used as simple *Run* elements).
        To change that, explicitly cast the first element
        to :class:`~lena.core.Run`.
        *args* can consist of one tuple, which is in that case expanded.

        If *FillRequest* element was not found,
        or if the sequences before and after that
        could not be correctly initialized,
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        fill_compute_seq._init_sequence_with_el(
            self, args, "_fill_request",
            check_sequence_type.is_fill_request_el,
            el_name="FillRequest", seq_name="FillRequestSeq"
        )

    def _fill_directly(self, val):
        self._fill_request.fill(val)

    def _fill_from_sequence(self, val):
        self._before.fill_into(self._fill_request, val)

    def _fill_with_preprocess(self, val):
        args = self._before.run([val,])
        for arg in args:
            self._fill_request.fill(arg)

    def fill(self, value):
        """Fill *self* with *value*.

        If the sequence before *FillRequest* is not empty,
        it preprocesses the *value*
        before filling *FillRequest*.
        """

    def request(self):
        """Request the results and yield.

        If the sequence after *FillRequest* is not empty,
        it postprocesses the results yielded
        from the *FillRequest* element.
        """
        vals = self._fill_request.request()

        if self._after:
            results = self._after.run(vals)
        else:
            results = vals

        # FillRequest must produce a generator, so no conversion is needed.
        return results
