"""Sequence with a FillCompute element."""

from . import lena_sequence
from . import sequence
from . import adapters
from . import fill_seq
from . import exceptions
from . import check_sequence_type


def _init_sequence_with_el(self, args, el_attr, check_el_type,
                           el_name, seq_name):
    # todo: remove after we remove FillRequestSeq
    before = []
    after = []
    el = None

    # same as for Sequence
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]

    for ind, arg in enumerate(args):
        if not check_el_type(arg):
            before.append(arg)
        else:
            el = arg
            break
    if el is None:
        raise exceptions.LenaTypeError(
            "{} must contain a {} element, ".format(seq_name, el_name) +
            "none provided: {}".format(args)
        )
    setattr(self, el_attr, el)

    for arg in args[ind+1:]:
        after.append(arg)

    # for syntactical reasons; otherwise (*before, el) is impossible
    before.append(el)
    try:
        before_seq = fill_seq.FillSeq(*before)
    except exceptions.LenaTypeError as err:
        raise err
    self._fill_seq = before_seq
    self.fill = self._fill_seq.fill
    # to do: add exception handling here.
    self._after = sequence.Sequence(*after)

    # _seq is an attribute of LenaSequence
    self._seq = []
    self._seq.extend(self._fill_seq)
    # self._seq.append(el)
    self._seq.extend(self._after)


class FillComputeSeq(lena_sequence.LenaSequence):
    """Sequence with one :class:`FillCompute` element.

    Input flow is preprocessed with the *Sequence*
    before the *FillCompute* element,
    then it fills the *FillCompute* element.
    
    When the results are *computed*,
    they are postprocessed with the *Sequence* after
    that element.
    """

    def __init__(self, *args):
        """*args* form a sequence with a *FillCompute* element.

        If *args* contain several *FillCompute* elements,
        only the first one is chosen
        (the subsequent ones are used as simple *Run* elements).
        To change that, explicitly cast the first element
        to :class:`.FillInto`.

        If *FillCompute* element was not found,
        or if the sequences before and after that
        could not be correctly initialized,
        :exc:`.LenaTypeError` is raised.
        """
        self._name = "FillComputeSeq"
        super(FillComputeSeq, self).__init__(*args)
        seq = self._seq

        before = []
        fc_el = None
        after = []

        for ind, el in enumerate(seq):
            if not check_sequence_type.is_fill_compute_el(el):
                before.append(el)
            else:
                fc_el = el
                break

        if fc_el is None:
            raise exceptions.LenaTypeError(
                "FillComputeSeq must contain a FillCompute element, "
                "none provided: {}".format(args)
            )
        self._fill_compute = fc_el

        for el in seq[ind+1:]:
            after.append(el)

        before.append(fc_el)
        try:
            before_seq = fill_seq.FillSeq(*before)
        except exceptions.LenaTypeError as err:
            raise err
        self._fill_seq = before_seq
        self.fill = self._fill_seq.fill
        # to do: do we check for exceptions like above
        # or skip like here?
        self._after = sequence.Sequence(*after)

    def fill(self, value):
        """Fill *self* with *value*.

        If the sequence before FillCompute is not empty,
        it preprocesses the *value*
        before filling *FillCompute*.
        """
        raise exceptions.LenaNotImplementedError

    def compute(self):
        """Compute the results and yield.

        If the sequence after *FillCompute* is not empty,
        it postprocesses the results yielded
        from *FillCompute* element.
        """
        flow = self._fill_compute.compute()
        results = self._after.run(flow)
        return results

    def __eq__(self, other):
        if not isinstance(other, FillComputeSeq):
            return NotImplemented
        return self._seq == other._seq
