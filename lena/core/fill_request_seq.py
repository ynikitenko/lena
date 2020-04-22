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
    
    When the results are yielded from the *FillRequest*,
    they are postprocessed with the *Sequence* after
    that element.
    """

    def __init__(self, *args, **kwargs):
        """*args* form a sequence with a *FillRequest* element.

        If *args* contains several *FillRequest* elements,
        only the first one is chosen
        (the subsequent ones are used as simple *Run* elements).
        To change that, explicitly cast the first element
        to :class:`.FillInto`.

        *kwargs* can contain *bufsize*, which is used during *run*.
        See :class:`FillRequest` for more information on *run*.
        By default *bufsize* is *1*. Other *kwargs* raise 
        :exc:`.LenaTypeError`.

        If *FillRequest* element was not found,
        or if the sequences before or after that
        could not be correctly initialized,
        :exc:`.LenaTypeError` is raised.
        """
        # *args* can consist of one tuple, which in that case is expanded.
        if "bufsize" in kwargs:
            self._bufsize = kwargs.pop("bufsize")
        else:
            self._bufsize = 1
        reset = kwargs.pop("reset", True)
        self._reset = reset

        if kwargs:
            raise exceptions.LenaTypeError(
                "unknown kwargs {}".format(kwargs)
            )
        fill_compute_seq._init_sequence_with_el(
            self, args, "_fill_request",
            check_sequence_type.is_fill_request_el,
            el_name="FillRequest", seq_name="FillRequestSeq"
        )
        fr = adapters.FillRequest(self, reset=reset, bufsize=self._bufsize)
        self.run = fr.run

    def fill(self, value):
        """Fill *self* with *value*.

        If the sequence before *FillRequest* is not empty,
        it preprocesses the *value*
        before filling *FillRequest*.
        """
        raise exceptions.LenaNotImplementedError

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

    def reset(self):
        """Reset the *FillRequest* element."""
        self._fill_request.reset()
