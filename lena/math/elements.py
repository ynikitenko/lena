"""Elements for mathematical calculations."""
import copy
import decimal
import sys
from collections import namedtuple
from decimal import getcontext, Decimal, Inexact

if sys.version_info.major == 2:
    from itertools import izip_longest as _zip_longest
else:
    from itertools import zip_longest as _zip_longest

import lena.context
import lena.core
from lena.core import (
    LenaTypeError, LenaRuntimeError, LenaZeroDivisionError, LenaValueError,
    is_fill_compute_el
)
import lena.flow

VarMeanCount = namedtuple("VarMeanCount", "var,mean,count")


# a helper class, shall be removed in 0.7
def _maybe_with_context(data, context):
    if context:
        return (data, context)
    return data


class Mean(object):
    """Calculate the arithmetic mean (average) of input values."""

    def __init__(self, sum_seq=None, pass_on_empty=False):
        """*sum_seq* is the algorithm to calculate the sum.
        If it is not provided, ordinary Python summation is used.
        Otherwise it is converted to a *FillCompute* sequence.

        If *pass_on_empty* is ``True``, then if nothing was filled,
        don't yield anything.
        By default an error is raised (see :meth:`compute`)."""
        # todo: add eq, repr and maybe starting values.
        self._sum_seq = sum_seq
        if sum_seq:
            if not hasattr(sum_seq, "reset") or not callable(sum_seq.reset):
                self.reset = self._reset_missing
                # can't do it, because reset seems to not be present
                # del self.reset
        # will be used only if sum_seq is not set
        self._sum = 0
        self._pass_on_empty = bool(pass_on_empty)
        self._count = 0
        self._cur_context = {}

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (considered empty if missing)
        is yielded in the output.
        """
        data, context = lena.flow.get_data_context(value)
        # could skip this check having two methods,
        # but all the other code looks too large to copy.
        if self._sum_seq:
            self._sum_seq.fill(data)
        else:
            self._sum += data
        self._count += 1
        self._cur_context = context

    def compute(self):
        """Calculate the mean and yield.

        If the current context is not empty, yield *(mean, context)*.
        Otherwise yield only *mean*.
        If the *sum_seq* yields several values,
        they are all yielded, but only the first is divided
        by number of events (considered the mean value).

        If no values were filled (count is zero),
        the mean can't be calculated and
        :exc:`.LenaZeroDivisionError` is raised.
        This can be changed to yielding nothing
        if *pass_on_empty* was initialized to ``True``.
        """
        if not self._count:
            if self._pass_on_empty:
                return
            raise LenaZeroDivisionError(
                "can't calculate average. No values were filled"
            )
        if self._sum_seq:
            sums = list(self._sum_seq.compute())
            assert sums
            # in principle, we allow for other values to be yielded
            sum_, scont = lena.flow.get_data_context(sums[0])
        else:
            sum_ = self._sum
            sums = []

        # sum_ needs to become float, otherwise
        # one can't divide Decimal by a float (in DSum)
        mean = float(sum_) / float(self._count)

        context = copy.deepcopy(self._cur_context)
        if sums:
            lena.context.update_recursively(context, scont)
            yield _maybe_with_context(mean, context)
            for sval in sums[1:]:
                context = copy.deepcopy(self._cur_context)
                sdata, scont = lena.flow.get_data_context(sval)
                lena.context.update_recursively(context, scont)
                yield _maybe_with_context(data, context)
        else:
            yield _maybe_with_context(mean, context)

    def reset(self):
        """Reset sum, count and context.

        Sum is reset zero (or the *reset* method of *sum_seq* is called),
        count to zero and context to {}.
        """
        if self._sum_seq is not None:
            self._sum_seq.reset()
        else:
            self._sum = 0
        self._count = 0
        self._cur_context = {}

    def _reset_missing(self):
        raise lena.core.LenaAttributeError(
            "the sum element has no reset method"
        )


class DSum(object):
    """Calculate an accurate floating point sum using decimals."""

    def __init__(self, total=0):
        """*total* is the initial value of the sum.

        .. seealso::

            Use :class:`.Sum` for quick and precise sums
            of integer numbers.
        """
        self._total = Decimal(total)
        self._dcontext = decimal.Context(traps=[Inexact])
        self._cur_context = {}

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (considered empty if missing)
        sets the current context.
        """
        data, context = lena.flow.get_data_context(value)
        self._cur_context = context
        # based on https://code.activestate.com/recipes/393090/
        # mant, exp = frexp(data)
        # mant, exp = int(mant * 2.0 ** 53), exp-53
        # These lines above showed no difference in tests.
        # Todo: check performance with them and with my simplification.
        while True:
            try:
                self._total = self._dcontext.add(self._total, Decimal(data))
                # total += mant * Decimal(2) ** exp
                break
            except Inexact:
                self._dcontext.prec += 1

    def compute(self):
        """Yield the calculated sum as *float*.

        If the current context is not empty, yield *(sum, context)*.
        Otherwise yield only the *sum*.
        """
        if not self._cur_context:
            yield self._total
        else:
            yield (self._total, copy.deepcopy(self._cur_context))

    def reset(self):
        """Reset the sum to 0.

        Context is reset to {}.
        """
        # we set it to zero, because the total in the initialization
        # is for creation of a copy of an existing object
        # (not for some magic constant to be added to the result).
        self._total = Decimal(0)
        self._cur_context = {}

    @property
    def total(self):
        return self._total

    def __eq__(self, other):
        if not isinstance(other, DSum):
            return False
        return (self._cur_context == other._cur_context
                and self._total == other._total)

    def __repr__(self):
        return "DSum({})".format(repr(self._total))


class Sum(object):
    """Calculate the sum of input values."""

    def __init__(self, total=0):
        """*total* is the initial value of the sum.

        .. seealso::

            Use :class:`.DSum` for exact floating summation.
        """
        # total is similar to Python's builtin *sum* start.
        self._total = total
        self._cur_context = {}

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (considered empty if missing)
        sets the current context.
        """
        data, context = lena.flow.get_data_context(value)
        self._total += data
        self._cur_context = context

    def compute(self):
        """Calculate the sum and yield.

        If the current context is not empty, yield *(sum, context)*.
        Otherwise yield only *sum*.
        """
        if not self._cur_context:
            yield self._total
        else:
            yield (self._total, copy.deepcopy(self._cur_context))

    @property
    def total(self):
        return self._total

    def reset(self):
        """Reset total and context.

        total is reset to 0 (not the starting number) and context to {}.
        """
        self._total = 0
        self._cur_context = {}


class Var(object):
    """Calculate the sample variance of input values."""

    def __init__(self, sum_sq=None, sum_=None, corrected=True,
                 pass_on_empty=False):
        """*sum_sq* and *sum_* are FillCompute elements
        calculating the sums of squares and of values
        of the input sample (:class:`Sum` by default).

        If *corrected* is ``True`` (default), the final variance
        is multiplied by n/(n-1), where n is the count of filled values.

        If *pass_on_empty* is ``True``, then if nothing was filled,
        nothing is yielded.
        By default an error is raised (see :meth:`compute`).
        """
        # todo: add population logic, that is
        # allow the mean to be provided.
        if sum_sq is None:
            sum_sq = Sum()
        else:
            assert hasattr(sum_sq, "fill") and hasattr(sum_sq, "compute")
            if not hasattr(sum_seq, "reset"):
                self.reset = self._reset_missing
        self._sum_sq = sum_sq

        # copy of that for sum_sq
        if sum_ is None:
            sum_ = Sum()
        else:
            assert hasattr(sum_, "fill") and hasattr(sum_, "compute")
            if not hasattr(sum_, "reset"):
                # any of resets missing leads to no reset
                self.reset = self._reset_missing
        self._sum = sum_

        # will be used only if sum_seq is not set
        self._pass_on_empty = bool(pass_on_empty)
        self._corrected = bool(corrected)
        self._count = 0
        self._cur_context = {}

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (considered empty if missing)
        is yielded in the output.
        """
        data, context = lena.flow.get_data_context(value)
        # todo: optimise these fill-s out
        self._sum_sq.fill(data**2)
        self._sum.fill(data)
        self._count += 1
        self._cur_context = context

    def compute(self):
        """Calculate the mean, variance and yield.

        A named tuple :class:`VarMeanCount` is yielded.
        If the current context is not empty, it is added as its context.

        If no values were filled (count is zero),
        the mean can't be calculated and
        :exc:`.LenaZeroDivisionError` is raised.
        This can be changed to yielding nothing
        if *pass_on_empty* was initialized to ``True``.
        If the sample contained only one element
        and *corrected* is ``True``,
        :exc:`.LenaZeroDivisionError` is always raised.
        """
        if not self._count:
            if self._pass_on_empty:
                return
            raise LenaZeroDivisionError(
                "can't calculate average. No values were filled"
            )
        count = self._count

        sum_sql = list(self._sum_sq.compute())
        assert len(sum_sql) == 1
        sum_sq = sum_sql[0]
        if isinstance(sum_sq, int):
            # if s.o. needs integers in the answer,
            # they may convert that themselves.
            # To avoid 3/2 = 1 from Python2.
            mean_sq = sum_sq / float(count)
        else:
            # should work for floats, Decimals, etc.
            mean_sq = sum_sq / count

        # todo: write get_one(list).
        suml = list(self._sum.compute())
        assert len(suml) == 1
        sum_ = suml[0]
        if isinstance(sum_, int):
            mean = sum_ / float(count)
        else:
            mean = sum_ / count

        var = mean_sq - mean**2
        if self._corrected:
            if count == 1:
                raise LenaZeroDivisionError(
                    "can not get corrected variance from a sample "
                    "with one element"
                )
            var *= count/float(count - 1)

        res = VarMeanCount(var, mean, count)

        yield _maybe_with_context(res, self._cur_context)

    def reset(self):
        r"""Reset sum_sq, sum\_, count and context."""
        self._sum_sq.reset()
        self._sum.reset()
        self._count = 0
        self._cur_context = {}

    def _reset_missing(self):
        raise lena.core.LenaAttributeError(
            "one of sum elements has no reset method"
        )


class Vectorize(object):
    """Apply an algorithm to a vector component-wise."""

    def __init__(self, seq, dim=-1, construct=None):
        """*seq* must be a *FillCompute* element or sequence.

        *dim* is the dimension of the input data
        (and of the constructed structure).
        *seq* may also be a list of sequences, in that case
        *dim* may be omitted.

        *construct* allows one to create an arbitrary object
        (by default the resulting values are tuples of dimension *dim*).
        """
        # Vectorize should be a rigid element
        # (we don't change its dimension easily),
        # therefore its dimension is set during initialisation.
        # if isinstance(seq, list):
        if isinstance(seq, list):
            if dim != -1:
                raise LenaTypeError(
                    "no dimension should be provided with a list"
                )
            self._seqs = seq
        else:
            if dim == -1:
                raise LenaTypeError(
                    "dim must be provided with a sequence"
                )
            if not is_fill_compute_el(seq):
                raise lena.core.LenaTypeError(
                    "seq must be a FillCompute element or sequence"
                )
            self._seqs = [seq]
            self._seqs.extend([copy.deepcopy(seq) for _ in range(dim-1)])

        # check what FillCompute elements have reset() method
        nresets = 0
        fc_els = []
        for _seq in self._seqs:
            try:
                # real FillComputeSeq
                fcel = _seq._fill_compute
            except AttributeError:
                # a FillCompute element
                fcel = _seq
            if hasattr(fcel, "reset") and callable(fcel.reset):
                nresets += 1
            fc_els.append(fcel)

        if nresets == len(self._seqs):
            self._fc_els = fc_els
        else:
            del self.reset

        # todo: get rid of construct,
        # a separate Lena element may be better.
        self._construct = construct
        self._dim = len(self._seqs)
        self._cur_context = {}
        self._filled_once = False
    
    def fill(self, val):
        """Fill sequences for each component of the data vector."""
        data, context = lena.flow.get_data_context(val)
        for ind, seq in enumerate(self._seqs):
            # can raise if data is not of a sufficient length
            # or of a not sufficient type for filling into *seq*
            seq.fill(data[ind])
        self._cur_context = context

    def compute(self):
        """Yield results from *compute()* for each component grouped
        together.

        If *compute* for different components yield different number
        of results, the longest output is yielded
        (the others are padded with ``None``).

        If the resulting value can't be converted to the type of
        the first value (or *construct* couldn't be used),
        a ``tuple`` is yielded.
        """
        # we allow for not equal length of results in the output;
        # the user could deal with that themselves
        if not hasattr(self, "_seqs"):
            raise LenaRuntimeError(
                "data dimension is unknown and no values were filled"
            )
        it = _zip_longest(*(seq.compute() for seq in self._seqs))
        while True:
            try:
                data = next(it)
            except StopIteration:
                # can also be any exception raised in seq.compute()
                break
            try:
                res = self._construct(*data)
            except TypeError:
                # we allow for special (not convertible to the needed type)
                # data values in the output (e.g. those containing context);
                # we use standard tuples for them.
                res = data
            yield _maybe_with_context(res, copy.deepcopy(self._cur_context))

    def reset(self):
        """If every sequence has a *reset()* method, this class
        is reset by resetting each *FillCompute* element.
        """
        # reset every sequence
        for fcel in self._fc_els:
            fcel.reset()
        self._cur_context = {}
