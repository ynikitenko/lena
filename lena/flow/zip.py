import collections
import copy

import lena.context
from lena.core import exceptions
from lena.core import split
from . import functions


class Zip(object):
    """Like :class:`Split`, but zip output values into tuples."""
    # """Like :class:`Split`, but zip output values into user-defined objects."""

    def __init__(self, sequences, name="zip", fields=[]):
    # shall be changed to this:
    # def __init__(self, seqs, construct=tuple, with_context=False):
    #    *Construct* is a callable which accepts a
        """Initialize a list of sequences to work in parallel.
        Sequences *seqs* must be of one common type.

        If *fields* are provided, the resulting values will be
        *namedtuples* (both data and context.zip parts)
        with these fields and *name* (by default "zip").
        *Fields* in this case must have same length as *sequences*
        (unless they are a string),
        or :exc:`.LenaTypeError` is raised.
        """
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
            self.reset = self._reset
        else:
            raise exceptions.LenaNotImplementedError

        self._name = name
        if fields:
            if len(fields) != len(sequences) and not isinstance(fields, str):
                raise exceptions.LenaTypeError(
                    "fields, if provided, must have same length as sequences, "
                    "{} and {} given".format(fields, sequences)
                )
            self._fields = fields
            self._namedtuple = collections.namedtuple(name, fields)
            # needed to be able to pickle and unpickle these namedtuples
            globals()[name] = self._namedtuple
        else:
            self._namedtuple = None

    def _create_context(self, values):
        common_context = lena.context.intersection(*values, level=1)
        diff_context = tuple((
            # level was 1 originally.
            lena.context.difference(val, common_context, level=1)
                for val in values
        ))
        if any(diff_context):
            # in normal circumstances zip can never contain same values
            # unless one zips completely same analyses
            if self._namedtuple:
                diff_context = self._namedtuple(*diff_context)
            lena.context.update_nested("zip", common_context, diff_context)
        return common_context

    def _create_data(self, values):
        if self._namedtuple:
            return self._namedtuple(*values)
        else:
            return tuple(values)

    def _fill(self, val):
        for seq in self._sequences:
            seq.fill(copy.deepcopy(val))

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

    def _reset(self):
        for seq in self._sequences:
            seq.reset()

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
