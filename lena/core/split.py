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
        """Split the flow into parallel sequences.

        *seqs* must be a list of sequences
        (any other container will raise :exc:`~lena.core.LenaTypeError`).

        *bufsize* is the size of the buffer for the input flow
        (not used with *FillCompute* elements).
        If *bufsize* is None, all input is materialized in the buffer.
        *bufsized* must be a natural number or None,
        otherwise :exc:`~lena.core.LenaValueError` is raised.
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
                        "unknown argument type. Could not initialize Sequence "
                        + "from {}".format(seq)
                    )
                    # todo: add more error message
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
        """Generate flow.

        This method is available only if all self sequences are Sources.
        Otherwise AttributeError is raised during the execution.
        """
        if self._n_seq_types != 1 or not ct.is_source(self._sequences[0]):
            raise exceptions.LenaAttributeError("Split has no method '__call__'. "
                                     + "It should contain only Source "
                                     + "sequences to be callable")
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
        while True:
            # iterate on flow
            buf = list(itertools.islice(flow, self._bufsize))
            if not buf:
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
                    if buf:
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
                            # so we break double cycle like this.
                            del active_seqs[ind]
                            del active_seq_types[ind]
                            n_of_active_seqs -= 1
                            continue
                    else:
                        for result in seq.compute():
                            yield result
                elif seq_type == "fill_request":
                    if buf:
                        stopped = False
                        for val in buf:
                            try:
                                seq.fill(val)
                            except exceptions.LenaStopFill:
                                stopped = True
                                break
                            else:
                                # Test whether it will be faster to yield
                                # when having fed all buffer.
                                # This implementation is better for memory
                                # (results don't have to be stored in FillRequest).
                                for result in seq.request():
                                    yield result
                        if stopped:
                            for result in seq.request():
                                yield result
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

                ind += 1
                # end internal while on sequences
            # end while on flow

        # yield computed data
        for seq, seq_type in zip(active_seqs, active_seq_types):
            if seq_type == "source":
                for val in seq():
                    yield val
            elif seq_type == "fill_compute":
                for val in seq.compute():
                    yield val
