"""Elements for mathematical calculations."""
import copy
import decimal
import sys
from decimal import getcontext, Decimal, Inexact

if sys.version[0] == 2:
    from itertools import izip_longest as _zip_longest
else:
    from itertools import zip_longest as _zip_longest

import lena.context
import lena.core
import lena.flow


class Mean(object):
    """Calculate mean (average) of input values."""

    def __init__(self, sum_=None, pass_on_empty=False):
        """*sum_* is the algorithm to calculate the sum.
        It must be a *FillCompute* element.
        If it is not provided, ordinary Python summation is used.

        If *pass_on_empty* is True, then if nothing was filled,
        don't yield anything.
        By default it raises an error (see :meth:`compute`)."""
        # sum *start* similar to Python's builtin *sum* star
        # is meaningless for this object, because we don't set
        # starting count (todo).
        self._sum_el = sum_
        if sum_:
            if not hasattr(sum_, "reset") or not callable(sum_.reset):
                self.reset = self._reset_missing
                # can't do it, because reset seems to not be present
                # del self.reset
        # will be used only without a summation element
        self._sum = 0
        self._pass_on_empty = pass_on_empty
        self._count = 0
        self._cur_context = {}

    def fill(self, value):
        """Fill *self* with *value*.

        The *value* can be a *(data, context)* pair.
        The last *context* value (if missing, it is considered empty)
        is saved for output.
        """
        data, context = lena.flow.get_data_context(value)
        # could skip this check having two methods,
        # but all the other code looks too large to copy.
        if self._sum_el:
            self._sum_el.fill(data)
        else:
            self._sum += data
        self._count += 1
        self._cur_context = context

    def compute(self):
        """Calculate mean and yield.

        If the current context is not empty, yield *(mean, context)*.
        Otherwise yield only *mean*.

        If no values were filled (count is zero),
        mean can't be calculated and
        :exc:`.LenaZeroDivisionError` is raised.
        This can be changed to yielding nothing
        if *pass_on_empty* was initialized to True.
        """
        if not self._count:
            if self._pass_on_empty:
                return
            raise lena.core.LenaZeroDivisionError(
                "can't calculate average. No values were filled"
            )
        if self._sum_el:
            sums = list(self._sum_el.compute())
            assert sums
            # in principle, we allow for other values to be yielded
            sum_, scont = lena.flow.get_data_context(sums[0])
        else:
            sum_ = self._sum
            sums = []

        mean = sum_ / float(self._count)

        def maybe_with_context(data, context):
            if not context:
                return data
            else:
                return (data, context)

        context = copy.deepcopy(self._cur_context)
        if sums:
            lena.context.update_recursively(context, scont)
            yield maybe_with_context(mean, context)
            for sval in sums[1:]:
                context = copy.deepcopy(self._cur_context)
                sdata, scont = lena.flow.get_data_context(sval)
                lena.context.update_recursively(context, scont)
                yield maybe_with_context(data, context)
        else:
            yield maybe_with_context(mean, context)

    def reset(self):
        """Reset sum, count and context.

        Sum is reset zero (or the *reset* method of *sum_* is called),
        count to zero and context to {}.
        """
        if self._sum_el is not None:
            self._sum_el.reset()
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
        """*total* is the initial value of the sum."""
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
            yield float(self._total)
        else:
            yield (float(self._total), copy.deepcopy(self._cur_context))

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
        return float(self._total)

    def __eq__(self, other):
        if not isinstance(other, DSum):
            return False
        return (self._cur_context == other._cur_context
                and self._total == other._total)

    def __repr__(self):
        return "DSum({})".format(repr(self._total))


class Sum(object):
    """Calculate sum of input values."""

    def __init__(self, total=0):
        """*total* is the initial value of the sum."""
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

        total is reset to 0 (not *start*) and context to {}.
        """
        self._total = 0
        self._cur_context = {}


class Vectorize(object):
    """Apply a scalar algorithm to a vector component-wise."""

    def __init__(self, seq, construct=None, dim=0):
        """*seq* will be converted to a :class:`.FillComputeSeq`.

        Return type during :meth:`compute` will be know from the first
        filled element.
        *construct* is needed in case the flow was empty.
        It will provide the needed dimension and data type.
        However, often an object constructor can allow
        an arbitrary dimension (like ``tuple``).
        In that case, provide *dim*.
        """
        # todo: if needed, a list *seq* could mean
        # a list of sequences of the needed dimension.
        try:
            self._seq = FillComputeSeq(seq)
        except TypeError:
            raise LenaTypeError("seq must be convertible to FillComputeSeq")

        if dim == 0 and construct is not None:
            try:
                _tmp = construct()
                dim = len(_tmp)
            except TypeError:
                # we have a chance to get data dimension from flow
                pass

        if dim:
            if not construct:
                raise LenaTypeError(
                    "non-zero dim requires construct"
                )
            self._seqs = [self._seq]
            self._seqs.extend([copy.deepcopy(self._seq) for _ in range(dim)])
            self.fill = self._fill_others
        else:
            self.fill = self._fill_first

        self._construct = construct
        self._dim = dim
    
    def fill(self, val):
        """Fill sequences for each component of the data vector."""
        raise NotImplementedError

    def _fill_first(self, val):
        # fill the first element. Will learn data type from that,
        # dimension and organise sequences.
        data, context = lena.flow.get_data_context(val)
        try:
            dim = len(data)
        except TypeError:
            raise LenaValueError(
                "no way to find out data dimension. "
                "type of the data does not support len"
            )

        if not self._construct:
            self._construct = type(data)
            # will be used like _construct(*result),
            # that is data.__init__ must support such arguments.

        self._seqs = [self._seq]
        self._seqs.extend([copy.deepcopy(self._seq) for _ in range(dim)])
        self.fill = self._fill_others
        self._cur_context = context

    def _fill_others(self, val):
        data, context = lena.flow.get_data_context(val)
        for ind, seq in enumerate(self._seqs):
            # can raise if data is not of a sufficient length
            # or of a not sufficient type for filling into *seq*
            seq.fill(data[ind])
        self._cur_context = context

    def compute(self):
        # we allow for not equal length of results in the output;
        # the user could deal with that themselves
        it = _zip_longest((seq.compute() for seq in self._seqs))
        while True:
            try:
                data = next(it)
            except StopIteration:
                # can also be any exception raised in seq.compute()
                break
            context = copy.deepcopy(self._cur_context)
            try:
                yield (self._construct(*data), context)
            except TypeError:
                # we allow for special (not convertible to the needed type)
                # dataues in the output (e.g. those containing context);
                # we use standard tuples for them.
                yield (data, context)
