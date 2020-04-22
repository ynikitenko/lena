"""Split data flow and run analysis in parallel."""
# Split and helper functions.
from __future__ import print_function

import copy
import itertools

from . import fill_compute_seq
from . import check_sequence_type as ct
from . import fill_request_seq
from . import sequence
from . import exceptions
from . import source
from . import meta


def _get_seq_with_type(seq):
    """Return a (sequence, type) pair.
    Sequence is derived from *seq*
    (or is *seq*, if that is of a sequence type).
    """
    seq_type = ""
    if isinstance(seq, source.Source):
        seq_type = "source"
    elif isinstance(seq, fill_compute_seq.FillComputeSeq):
        seq_type = "fill_compute"
    elif isinstance(seq, fill_request_seq.FillRequestSeq):
        seq_type = "fill_request"
    elif isinstance(seq, sequence.Sequence):
        seq_type = "sequence"

    if seq_type:
        # append later
        pass
    ## If no explicit type is given, check seq's methods
    elif ct.is_fill_compute_seq(seq):
        seq_type = "fill_compute"
        if not ct.is_fill_compute_el(seq):
            seq = fill_compute_seq.FillComputeSeq(*seq)
    elif ct.is_fill_request_seq(seq):
        seq_type = "fill_request"
        if not ct.is_fill_request_el(seq):
            seq = fill_request_seq.FillRequestSeq(*seq)
    # Source is not checked,
    # because it must be Source explicitly.
    else:
        try:
            if isinstance(seq, tuple):
                seq = sequence.Sequence(*seq)
            else:
                seq = sequence.Sequence(seq)
        except exceptions.LenaTypeError:
            raise exceptions.LenaTypeError(
                "unknown argument type. Must be one of "
                "FillComputeSeq, FillRequestSeq or Source, "
                "{} provided".format(seq)
            )
        else:
            seq_type = "sequence"
    return (seq, seq_type)


class Split(object):
    """Split data flow and run analysis in parallel."""

    def __init__(self, seqs, bufsize=1000, copy_buf=True):
        """*seqs* must be a list of Sequence, Source, FillComputeSeq
        or FillRequestSeq sequences
        (any other container will raise :exc:`.LenaTypeError`).
        If *seqs* is empty, *Split* acts as an empty *Sequence* and
        yields all values it receives.

        *bufsize* is the size of the buffer for the input flow.
        If *bufsize* is ``None``,
        whole input flow is materialized in the buffer.
        *bufsize* must be a natural number or ``None``,
        otherwise :exc:`.LenaValueError` is raised.

        *copy_buf* sets whether the buffer should be copied during *run*.
        This is important if different sequences can change input data
        and interfere with each other.

        Common type:
            If each sequence from *seqs* has a common type,
            *Split* creates methods corresponding to this type.
            For example, if each sequence is *FillCompute*,
            *Split* creates methods *fill* and *compute*
            and can be used as a *FillCompute* sequence.
            *fill* fills all its subsequences (with copies
            if *copy_buf* is True), and *compute*
            yields values from all sequences in turn
            (as would also do *request* or *Source.__call__*).
        """
        # todo: copy_buf must be always True. Isn't that?
        if not isinstance(seqs, list):
            raise exceptions.LenaTypeError(
                "seqs must be a list of sequences, "
                "{} provided".format(seqs)
            )
        seqs = [meta.alter_sequence(seq) for seq in seqs]
        self._sequences = []
        self._seq_types = []

        for sequence in seqs:
            try:
                seq, seq_type = _get_seq_with_type(sequence)
            except exceptions.LenaTypeError:
                raise exceptions.LenaTypeError(
                    "unknown argument type. Must be one of "
                    "FillComputeSeq, FillRequestSeq or Source, "
                    "{} provided".format(sequence)
                )
            self._sequences.append(seq)
            self._seq_types.append(seq_type)

        different_seq_types = set(self._seq_types)
        self._n_seq_types = len(different_seq_types)
        if self._n_seq_types == 1:
            seq_type = different_seq_types.pop()
            # todo: probably remove run to avoid duplication?
            if seq_type == "fill_compute":
                self.fill = self._fill
                self.compute = self._compute
            elif seq_type == "fill_request":
                self.fill = self._fill
                self.request = self._request
            elif seq_type == "source":
                pass
        elif self._n_seq_types == 0:
            self.run = self._empty_run

        self._copy_buf = bool(copy_buf)

        if bufsize is not None:
            if bufsize != int(bufsize) or bufsize < 1:
                raise exceptions.LenaValueError(
                    "bufsize should be a natural number "
                    "or None, {} provided".format(bufsize)
                )
        self._bufsize = bufsize

    def __call__(self):
        """Each initialization sequence generates flow.
        After its flow is empty, next sequence is called, etc.

        This method is available only if each self sequence is a
        :class:`.Source`,
        otherwise :exc:`.LenaAttributeError` is raised during the execution.
        """
        if self._n_seq_types != 1 or not ct.is_source(self._sequences[0]):
            raise exceptions.LenaAttributeError(
                "Split has no method '__call__'. It should contain "
                "only Source sequences to be callable"
            )
        for seq in self._sequences:
            for result in seq():
                yield result

    def _fill(self, val):
        for seq in self._sequences[:-1]:
            if self._copy_buf:
                seq.fill(copy.deepcopy(val))
            else:
                seq.fill(val)
        self._sequences[-1].fill(val)

    def _compute(self):
        for seq in self._sequences:
            for val in seq.compute():
                yield val

    def _request(self):
        for seq in self._sequences:
            for val in seq.request():
                yield val

    def _empty_run(self, flow):
        """If self sequence is empty, yield all flow unchanged."""
        for val in flow:
            yield val

    def run(self, flow):
        """Iterate input *flow* and yield results.

        The *flow* is divided into subslices of *bufsize*.
        Each subslice is processed by sequences
        in the order of their initializer list.

        If a sequence is a *Source*,
        it doesn't accept the incoming *flow*,
        but produces its own complete flow
        and becomes inactive (is not called any more).

        A *FillRequestSeq* is filled with the buffer contents.
        After the buffer is finished,
        it yields all values from *request()*.

        A *FillComputeSeq* is filled with values from each buffer,
        but yields values from *compute* only after the whole *flow*
        is finished.

        A *Sequence* is called with *run(buffer)*
        instead of the whole flow. The results are yielded
        for each buffer (and also if the *flow* was empty).
        If the whole flow must be analysed at once,
        don't use such a sequence in *Split*.

        If the *flow* was empty, each *call*, *compute*,
        *request* or *run* is called nevertheless.

        If *copy_buf* is True,
        then the buffer for each sequence except the last one is a deep copy
        of the current buffer.
        """
        active_seqs = self._sequences[:]
        active_seq_types = self._seq_types[:]

        n_of_active_seqs = len(active_seqs)
        ind = 0
        flow = iter(flow)
        flow_was_empty = True
        while True:
            ## iterate on flow
            # If stop is None, then iteration continues
            # until the iterator is exhausted, if at all
            # https://docs.python.org/3/library/itertools.html#itertools.islice
            orig_buf = list(itertools.islice(flow, self._bufsize))
            if orig_buf:
                flow_was_empty = False
            else:
                break

            # iterate on active sequences
            ind = 0
            while ind < n_of_active_seqs:
                if self._copy_buf and n_of_active_seqs - ind > 1:
                    # last sequence doesn't need a copy of the buffer
                    buf = copy.deepcopy(orig_buf)
                else:
                    buf = orig_buf
                seq = active_seqs[ind]
                seq_type = active_seq_types[ind]

                if seq_type == "source":
                    for val in seq():
                        yield val
                    del active_seqs[ind]
                    del active_seq_types[ind]
                    n_of_active_seqs -= 1
                    continue
                elif seq_type == "fill_compute":
                    stopped = False
                    for val in buf:
                        try:
                            seq.fill(val)
                        except exceptions.LenaStopFill:
                            stopped = True
                            break
                    if stopped:
                        for result in seq.compute():
                            yield result
                        # we don't have goto in Python,
                        # so we have to repeat this
                        # each time we break double cycle.
                        del active_seqs[ind]
                        del active_seq_types[ind]
                        n_of_active_seqs -= 1
                        continue
                elif seq_type == "fill_request":
                    stopped = False
                    for val in buf:
                        try:
                            seq.fill(val)
                        except exceptions.LenaStopFill:
                            stopped = True
                            break
                    # FillRequest yields each time after buffer is filled
                    for result in seq.request():
                        yield result
                    if stopped:
                        del active_seqs[ind]
                        del active_seq_types[ind]
                        n_of_active_seqs -= 1
                        continue
                elif seq_type == "sequence":
                    # run buf as a whole flow.
                    # this may be very wrong if seq has internal state,
                    # e.g. contains a Cache
                    for res in seq.run(buf):
                        yield res
                # this is not needed, because can't be tested.
                # else:
                #     raise exceptions.LenaRuntimeError(
                #         "unknown sequence type {}".format(seq_type)
                #     )

                ind += 1
                # end internal while on sequences
            # end while on flow

        # yield computed data
        for seq, seq_type in zip(active_seqs, active_seq_types):
            if seq_type == "source":
                # otherwise it is a logic error
                assert flow_was_empty
                for val in seq():
                    yield val
            elif seq_type == "fill_compute":
                for val in seq.compute():
                    yield val
            elif seq_type == "fill_request":
                # otherwise FillRequest yielded after each buffer
                if flow_was_empty:
                    for val in seq.request():
                        yield val
            elif seq_type == "sequence":
                if flow_was_empty:
                    for val in seq.run([]):
                        yield val
