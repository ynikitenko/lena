from __future__ import print_function

import lena.context
from lena.core import exceptions
from lena.core import split
from . import functions


class Zip(object):
    """Like :class:`Split`, but zip output values into tuples."""

    def __init__(self, sequences, **kwargs):
        """Initialize a list of *sequences* to work in parallel.
        *Sequences* must be of one common type.
        """
        # create_data=None, create_value=None
        if not sequences:
            raise exceptions.LenaTypeError(
                "at least one sequence must be given"
            )

        self._sequences = []
        seq_types_list = []

        for sequence in sequences:
            try:
                seq, seq_type = split._get_seq_with_type(sequence)
            except exceptions.LenaTypeError:
                raise exceptions.LenaTypeError(
                    "unknown argument type. Must be one of "
                    "FillComputeSeq, FillRequestSeq or Source, "
                    "{} provided".format(sequence)
                )
            self._sequences.append(seq)
            seq_types_list.append(seq_type)

        seq_types = set(seq_types_list)
        if len(seq_types) != 1:
            raise exceptions.LenaTypeError(
                "only one sequence type is allowed"
            )

        seq_type = seq_types.pop()
        if seq_type == "fill_compute":
            self.fill = self._fill
            self.compute = self._compute
        elif seq_type == "fill_request":
            self.fill = self._fill
            self.request = self._request
        else:
            raise exceptions.LenaNotImplementedError

    def _create_context(self, values):
        common_context = lena.context.intersection(*values, level=1)
        diff_context = tuple((
            lena.context.difference(val, common_context) for val in values
        ))
        if any(diff_context):
            # in normal circumstances zip can never contain same values
            # unless one zips completely same analyses
            lena.context.update_nested(common_context, {"zip": diff_context})
        return common_context

    def _create_data(self, values):
        return tuple(values)

    def _fill(self, val):
        for seq in self._sequences:
            seq.fill(val)

    def _compute(self):
        results = []
        for seq in self._sequences:
            results.append(seq.compute())
        for val in self._yield(results):
            yield val

    def _request(self):
        results = []
        for seq in self._sequences:
            results.append(seq.request())
        for val in self._yield(results):
            yield val

    def _yield(self, results):
        # general yield from various sequences
        while True:
            value = []
            break_while = False
            # stop on shortest sequence
            for res in results:
                try:
                    val = next(res)
                except StopIteration:
                    break_while = True
                    break
                else:
                    value.append(val)
            if break_while:
                break
            # combine data and context for output value
            dc = [functions.get_data_context(val) for val in value]
            data = self._create_data([val[0] for val in dc])
            context = self._create_context([val[1] for val in dc])
            if context:
                yield (data, context)
            else:
                yield data
