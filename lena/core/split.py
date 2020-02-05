"""Split data flow and run analysis in parallel."""
# Split and helper functions.
from __future__ import print_function

import itertools

from . import fill_compute_seq
from . import check_sequence_type as ct
from . import fill_request_seq
from . import sequence
from . import exceptions
from . import source
from . import meta


class Split(object):
    """Split data flow and run analysis in parallel."""

    def __init__(self, seqs, bufsize=1000):
        """*seqs* must be a list of Sequence, Source, FillComputeSeq
        or FillRequestSeq sequences
        (any other container will raise :exc:`~lena.core.LenaTypeError`).
        If *seqs* is empty, *Split* acts as an empty *Sequence* and
        yields all values it receives.

        *bufsize* is the size of the buffer for the input flow.
        If *bufsize* is ``None``,
        whole input flow is materialized in the buffer.
        *bufsized* must be a natural number or ``None``,
        otherwise :exc:`~lena.core.LenaValueError` is raised.

        Common type:
            If each sequence from *seqs* has a common type,
            *Split* obtains this type and creates corresponding methods.
            For example, if each sequence is *FillCompute*,
            *Split* creates methods *fill* and *compute*
            and can be used as a *FillCompute* sequence.
        """
        if not isinstance(seqs, list):
            raise exceptions.LenaTypeError(
                "seqs must be a list of sequences, "
                "{} provided".format(seqs)
            )
        seqs = [meta.alter_sequence(seq) for seq in seqs]
        self._sequences = []
        self._seq_types = []

        for seq in seqs:
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

            self._sequences.append(seq)
            self._seq_types.append(seq_type)

        different_seq_types = set(self._seq_types)
        self._n_seq_types = len(different_seq_types)
        if self._n_seq_types == 1:
            seq_type = different_seq_types.pop()
            if seq_type == "fill_compute":
                self.fill = self._fill
                self.compute = self._compute
            elif seq_type == "fill_request":
                self.fill = self._fill
                self.request = self._request
            elif seq_type == "source":
                pass
        elif self._n_seq_types == 0:
            self.run = self._run

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
        :class:`~lena.core.Source`,
        otherwise :exc:`~lena.core.LenaAttributeError` is raised during the execution.
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
        for seq in self._sequences:
            seq.fill(val)

    def _compute(self):
        for seq in self._sequences:
            for val in seq.compute():
                yield val

    def _request(self):
        for seq in self._sequences:
            for val in seq.request():
                yield val

    def _run(self, flow):
        """If self sequence is empty, yield all flow unchanged."""
        for val in flow:
            yield val

    def run(self, flow):
        """Iterate input *flow* and yield results from self sequences."""
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
            buf = list(itertools.islice(flow, self._bufsize))
            if buf:
                flow_was_empty = False
            else:
                break

            # iterate on active sequences
            ind = 0
            while ind < n_of_active_seqs:
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
                else:
                    raise exceptions.LenaRuntimeError(
                        "unknown sequence type {}".format(seq_type)
                    )

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
