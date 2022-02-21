from . import adapters
from . import check_sequence_type
from . import exceptions
from . import fill_compute_seq
from . import lena_sequence
from . import sequence


class FillRequestSeq(lena_sequence.LenaSequence):
    """Sequence with one *FillRequest* element.

    Input flow is preprocessed with the sequence
    before the *FillRequest* element,
    then it fills the *FillRequest* element.
    
    When the results are yielded from the *FillRequest*,
    they are postprocessed with the elements that follow it.
    """

    def __init__(self, *args, **kwargs):
        """*args* form a sequence with a *FillRequest* element.

        If *args* contains several *FillRequest* elements,
        only the first one is chosen
        (the subsequent ones are used as simple *Run* elements).
        To change that, explicitly cast the first element
        to :class:`.FillInto`.

        *kwargs* can contain *bufsize* or *reset*.
        See :class:`FillRequest` for more information on them.
        By default *bufsize* is *1*.

        If *FillRequest* element was not found,
        the sequences could not be correctly initialized,
        or unknown keyword arguments were received,
        :exc:`.LenaTypeError` is raised.
        """
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
        ##| not sure now. Why is it not documented?
        # `-> *args* can consist of one tuple,
        #     which in that case is expanded.
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
