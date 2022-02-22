"""Adapters allow to use existing objects as Lena core elements.

Adapters can be used for several purposes:

    - provide an unusual name for a method (*Run(my_obj, run="my_run")*).
    - hide unused methods to prevent ambiguity.
    - automatically convert objects of one type to another in sequences (*FillCompute* to *Run*).
    - explicitly cast object of one type to another (*FillRequest* to *FillCompute*).

Example:

>>> class MyEl(object):
...     def my_run(self, flow):
...         for val in flow:
...             yield val
...
>>> my_run = Run(MyEl(), run="my_run")
>>> list(my_run.run([1, 2, 3]))
[1, 2, 3]
"""
import itertools

from . import exceptions
from . import check_sequence_type as ct # it is a module, no need to hide

# pylint: disable=method-hidden
# We leave method stubs in the adapters,
# because they will appear in their documentation,
# even though the actual code will be overwritten.

# class _MISSING_TYPE:
#     pass
# _SENTINEL = _MISSING_TYPE()
# This looks better in automatic documentation:
_SENTINEL = object()
# Sentinel is used when it is important to know
# whether it was passed as a keyword argument, for example,
# when an element can be used without this method (type cast).
# Otherwise use just the method's name.


def _init_callable(self, el, call):
    """Common initializer for Call and SourceEl."""
    if call is _SENTINEL:
        # try to find call in el
        if callable(el):
            self._call = el # pylint: disable=protected-access
        else:
            raise exceptions.LenaTypeError(
                "provide a callable method or a callable element, "
                "{} given".format(el)
            )
    else:
        # get call by its name
        el_call = getattr(el, call, None)
        if callable(el_call):
            self._call = el_call # pylint: disable=protected-access
        else:
            raise exceptions.LenaTypeError(
                "call method {} of {} must exist and be callable"
                .format(call, el)
            )
    self._el = el


class Call(object):
    """Adapter to provide *__call__(value)* method.

    Name of the actually called method
    can be customized during the initialization.

    The method *__call__(value)* is a simple (preferably pure) function,
    which accepts a *value* and returns its transformation.
    """

    def __init__(self, el, call=_SENTINEL):
        """Element *el* must contain a callable method *call*
        or be callable itself.

        If *call* method name is not provided,
        it is checked whether *el* is callable itself.

        If :class:`Call` failed to instantiate with *el* and *call*,
        :exc:`.LenaTypeError` is raised.
        """
        _init_callable(self, el, call)

    def __call__(self, value):
        """Transform the *value* and return."""
        # This fix is needed only for a special method,
        # https://docs.python.org/3/reference/datamodel.html#special-lookup
        # Methods with other names will be monkey-patched correctly.
        return self._call(value) # pylint: disable=no-member


class FillCompute(object):
    """Adapter for a *FillCompute* element.

    A *FillCompute* element has methods *fill(value)* and *compute()*.
    """

    def __init__(self, el, fill="fill", compute="compute"):
        """Method names can be customized through *fill* and *compute*
        keyword arguments during the initialization.

        *FillCompute* can be explicitly cast from *FillRequest*.
        In this case *compute* is *request*.

        If callable methods *fill* and *compute* or *request*
        were not found, :exc:`.LenaTypeError` is raised.
        """
        fill_method = getattr(el, fill, None)
        compute_method = getattr(el, compute, None)

        if callable(fill_method):
            self.fill = fill_method
        else:
            raise exceptions.LenaTypeError(
                "fill method {} must exist and be callable".format(fill)
            )
        if callable(compute_method):
            self.compute = compute_method
        else:
            # derive from FillRequest
            request = getattr(el, "request", None)
            if not callable(request):
                raise exceptions.LenaTypeError(
                    "compute method {} or request must exist and be callable"\
                    .format(compute)
                )
            self.compute = request
        self._el = el

    def fill(self, value): # pylint: disable=no-self-use,unused-argument
        """Fill *self* with *value*."""
        raise exceptions.LenaNotImplementedError

    def compute(self): # pylint: disable=no-self-use
        """Yield computed values."""
        raise exceptions.LenaNotImplementedError


class FillInto(object):
    """Adapter for a FillInto element."""

    def __init__(self, el, fill_into=_SENTINEL, explicit=True):
        """Element *el* must implement *fill_into* method,
        be callable or be a Run element.

        If no *fill_into* argument is provided,
        then *fill_into* method is searched, then *__call__*,
        then *run*.
        If none of them is found and callable,
        :exc:`.LenaTypeError` is raised.

        Note that callable elements and elements with *fill_into* method
        have different interface.
        If the *el* is callable, it is assumed to be a simple function,
        which accepts a single value and transforms that,
        and the result is filled into the element by this adapter.
        *fill_into* method, on the contrary, takes two arguments
        (element and value) and fills the element itself.
        This allows to use lambdas directly in *FillInto*.

        A *Run* element is converted to *FillInto* this way:
        for each value the *el* runs a flow
        consisting of this one value
        and fills the results into the output element.
        This can be done only if *explicit* is True.
        """
        if fill_into is _SENTINEL:
            fill_into_m = getattr(el, "fill_into", None)
            if callable(fill_into_m):
                self.fill_into = fill_into_m
            # try to make possible convertions
            elif callable(el):
                # use default implementation
                pass
            elif ct.is_run_el(el) and explicit:
                self.fill_into = self._run_fill_into
            else:
                raise exceptions.LenaTypeError(
                    "element {} ".format(el)
                    + "must implement 'fill_into' method, "
                    "or be callable or a Run element"
                )
        elif callable(getattr(el, fill_into, None)):
            self.fill_into = getattr(el, fill_into)
        else:
            raise exceptions.LenaTypeError(
                "method {} of {} must exist and be callable".
                format(fill_into, el)
            )
        self._el = el

    def fill_into(self, element, value):
        """Fill *value* into an *element*.

        *Value* is transformed by the initialization element
        before filling *el*.

        *Element* must provide a *fill* method.
        """
        element.fill(self._el(value))

    def _run_fill_into(self, element, value):
        """Convert *value* into a flow of one element,
        run this flow and fill the *element* with the results.
        """
        for result in self._el.run([value]):
            element.fill(result)


class FillRequest(object):
    """Adapter for a *FillRequest* element.

    A *FillRequest* element slices the flow during *fill*
    and yields results for each chunk during *request*.
    It can also call a method *reset* after each *request*.
    """
    # FillRequest is not deprecated, but changing its meaning.
    # # They seem redundant, because mostly they are used
    # # as FillCompute (and a lot of code is duplicated).
    # # Memory warnings should be indicated elsewhere
    # # (like special fields).
    # # Moreover, FillCompute elements
    # # sometimes need to be more versatile,
    # # and FillRequest is of no help for that.

    def __init__(self, el,
                 fill="fill", request="request", reset_name="reset",
                 reset=None, bufsize=1, yield_on_remainder=False,
                 buffer_input=None, buffer_output=None):
        """Names for actual *fill*, *request* and *reset*
        can be provided during initialization (the latter is set
        through *reset_name*).

        *FillRequest* can be initialized from a *FillCompute* element.
        If a callable *request* method was not found,
        *el* must have a callable *compute* method.
        *request* in this case is *compute*.

        *FillRequest* can also be initialized from a *Run* element.
        In that case *el* is not required to have *fill*, *compute*
        or *reset* methods
        (and *FillRequest* will not have such missing methods).
        *FillRequest* implements *run* method
        that splits the flow into subslices of *bufsize* values
        and feeds them to the *run* method of *el*.
        Since we require no less than *bufsize* values
        (except *yield_on_remainder* is ``True``),
        we need to store either *bufsize* values of the incoming flow
        or all values produced by *el.run* for each slice.
        This is set by *buffer_input* or *buffer_output*.
        One and only one of them must be ``True``.
        For example, if the element receives file names and produces
        data from them, it would be wise to buffer input. If the element
        receives much data and produces a histogram,
        one should buffer output.

        If a keyword argument *reset* is ``True``,
        *el* must have a method *reset_name*, and in this case
        :meth:`reset` is called after each :meth:`request`
        (including those during :meth:`run`).
        In general, *Run* elements have no *reset* methods,
        but for *FillCompute* elements *reset* must be set explicitly.

        If *yield_on_remainder* is ``True``,
        then the output will be yielded
        even if the element was filled less than *bufsize* times
        (but at least once).
        In that case no internal buffers are used during :meth:`run`
        and corresponding attributes are not checked.

        **Attributes**

        :attr:`bufsize` is the maximum size of subslices during *run*.

        *bufsize* must be a natural number,
        otherwise :exc:`.LenaValueError` is raised.
        If callable *fill* and *request* methods were not found,
        or *FillRequest* could not be derived from *FillCompute*,
        or if *reset* is ``True``, but *el* has no method *reset*,
        :exc:`.LenaTypeError` is raised.

        .. versionchanged:: 0.5
           add keyword arguments *yield_on_remainder*, *buffer_input*,
           *buffer_output*, *reset_name*.
           Require explicit *reset* for *FillCompute* elements.
        """
        # todo: rename bufsize to size or something cleverer

        el_reset = getattr(el, reset_name, None)
        if callable(el_reset):
            # we set this method even if *reset* is False,
            # because reset() may be called manually
            self._el_reset = el_reset
        elif reset:
            raise exceptions.LenaTypeError(
                "{} method must exist and be callable".format(reset_name)
            )
        else:
            # disable the missing method.
            self.reset = None
        self._reset = bool(reset)

        run = getattr(el, "run", None)
        if run and callable(run):
            bi = bool(buffer_input)
            bo = bool(buffer_output)
            # if yield_on_remainder is True, buffers are not used.
            if not yield_on_remainder and int(bi) + int(bo) != 1:
                raise exceptions.LenaValueError(
                    "one and only one of buffer_input or buffer_output "
                    "must be set"
                )
            self._buffer_input = bi
            self.run = self._run_run
            has_run = True
        else:
            # This method won't work in case of no fill/compute/request,
            # but it will raise during initialization if so.
            self.run = self._run_fill_compute
            has_run = False

        el_fill = getattr(el, fill, None)
        if callable(el_fill):
            self._el_fill = el_fill
            if reset is None:
                raise exceptions.LenaTypeError(
                    "reset must be set explicitly "
                    "if {} method is present".format(fill)
                )
        elif not has_run:
            raise exceptions.LenaTypeError(
                "fill method {} must exist and be callable".format(fill)
            )
        else:
            self.fill = None

        el_request = getattr(el, request, None)
        if callable(el_request):
            # we don't check whether it has fill method here.
            self._el_request = el_request
        else:
            # derive from compute
            compute = getattr(el, "compute", None)
            if callable(compute):
                self._el_request = compute
            elif not has_run:
                raise exceptions.LenaTypeError(
                    "element must have callable methods request, compute or run"
                )
            else:
                self.request = None

        if(bufsize != int(bufsize) or bufsize < 1):
            raise exceptions.LenaValueError(
                "bufsize must be a natural number, not {}".format(bufsize)
            )
        self.bufsize = int(bufsize)
        self._yield_on_remainder = bool(yield_on_remainder)

        self._el = el

    def fill(self, value):  # pylint: disable=no-self-use,unused-argument
        """Fill *el* with *value*."""
        self._el_fill(value)

    def request(self):
        """Yield computed values."""
        for val in self._el_request():
            yield val
        if self._reset:
            self._el_reset()

    def reset(self):
        """Reset *el*."""
        self._el_reset()

    def run(self, flow):
        """Process the *flow* slice by slice.

        *fill* each value from a subslice of *flow*
        of *bufsize* length, then yield results from *request*.
        Repeat until the *flow* is exhausted.

        If *fill* was not called even once (*flow* was empty),
        nothing is yielded, because *bufsize* values were not obtained
        (in contrast to *FillCompute*, for which output for an empty
        flow is reasonable).
        The last slice may contain less than *bufsize* values.
        If there were any and if *yield_on_remainder* is ``True``,
        *request* will be called for that.
        """
        raise exceptions.LenaNotImplementedError

    def _run_fill_compute(self, flow):
        while True:
            # A slice is a non-materialized list, which means
            # that it will not take place of *bufsize* in memory.
            slice_ = itertools.islice(flow, self.bufsize)
            # Reset the counter; what if it grows too large?
            # Maybe it will allow faster nfills % bufsize?
            # May be irrelevant though.
            nfills = 0

            # there is no other way to check
            # whether the flow contains at least one element
            try:
                val = next(slice_)
            except StopIteration:
                # Unlike FillCompute, we don't yield anything
                # if the flow was smaller than the required bufsize
                break
            else:
                self.fill(val)
                nfills += 1

            for val in slice_:
                self.fill(val)
                nfills += 1

            # Flow finished too early.
            # Normally nfills would be equal to self.bufsize
            if nfills % self.bufsize:
                if self._yield_on_remainder:
                    # can't return smth in Python 2 generator.
                    # return self.request()
                    for result in self.request():
                        yield result
                return

            for result in self.request():
                yield result

    def _run_run(self, flow):
        # todo: to improve performance, one might create
        # a separate run method for bufsize = 1.
        from itertools import islice, chain
        el_run = self._el.run
        bufsize = self.bufsize

        # we can yield results one by one
        if self._yield_on_remainder:
            # it is important that flow is an iterable, not a sequence,
            # so we can use islice repeatedly
            while True:
                try:
                    val = next(flow)
                except StopIteration:
                    # empty flow gives empty results
                    return
                else:
                    # at least one event present
                    # this would give bad performance for bufsize=1
                    for val in el_run(chain([val],
                                            islice(flow, bufsize-1))):
                        yield val
                    # usually Run elements have no reset, but...
                    if self._reset:
                        self.reset()

        # we can't yield results one by one,
        # because we need to be sure
        # that *bufsize* values were encountered

        class slice_iterated_with_count():

            def __init__(self, size, seq): 
                self.count = 0
                self._size = size
                self._seq = seq

            def __iter__(self):
                count = 0
                for val in islice(self._seq, self._size):
                    count += 1
                    yield val
                self.count = count

        if self._buffer_input:
            while True:
                buffer = list(islice(flow, bufsize))

                # incomplete buffer, yield nothing.
                if len(buffer) < bufsize:
                    # _yield_on_remainder is False
                    return

                # full buffer received, process.
                for val in el_run(iter(buffer)):
                    yield val
                # probably False for Run element.
                if self._reset:
                    self._el_reset()
        else:
            # buffer output
            # slice_ can be iterated multiple times
            slice_ = slice_iterated_with_count(bufsize, flow)
            while True:
                results = list(el_run(slice_))
                if slice_.count < bufsize:
                    return
                for val in results:
                    yield val

                # probably False for Run element.
                if self._reset:
                    self._el_reset()


class Run(object):
    """Adapter for a *Run* element."""

    def __init__(self, el, run=_SENTINEL):
        """Name of the method *run* can be customized during initialization.

        If *run* argument is supplied, *el* must be None
        or it must have a callable method with name given by *run*.

        If *run* keyword argument is missing,
        then *el* is searched for a method *run*.
        If that is not found, a type cast is attempted.

        A *Run* element can be initialized from a *Call*
        or a *FillCompute* element.

        A callable element is run as a transformation function,
        which accepts single values from the flow
        and *returns* their transformations for each value.

        A *FillCompute* element is run the following way:
        first, *el.fill(value)* is called for the whole flow.
        After the flow is exhausted, *el.compute()* is called.

        It is possible to initialize :class:`Run`
        using a generator function without an element.
        To do that, set the element to ``None``:
        *Run(None, run=<my_function>)*.

        If the initialization failed,
        :exc:`.LenaTypeError` is raised.

        :class:`Run` is used implicitly during the initialization
        of :class:`.Sequence`.
        """
        if run is _SENTINEL:
            # no explicit method name given
            run_ = getattr(el, "run", None)
            if callable(run_):
                # callable method "run" found
                self.run = run_
            # convert el to Run
            elif callable(el):
                # Call to Run
                self.run = self._call_run
            elif ct.is_fill_compute_el(el):
                # FillCompute to Run
                self.run = self._fc_run
            else:
                raise exceptions.LenaTypeError(
                    "element {} must implement run method ".format(el) +
                    "be callable, or be a FillCompute element"
                )
        else:
            # explicit method name given
            if el is None:
                self.run = run
            # may raise if run is not a string
            elif callable(getattr(el, run, None)):
                self.run = getattr(el, run)
            else:
                raise exceptions.LenaTypeError(
                    "no callable method {} of {} found".format(run, el)
                )
        self._el = el

    def _call_run(self, flow):
        """Implement *run* method for *Call* element."""
        for val in flow:
            yield self._el(val)

    def run(self, flow):
        """Yield transformed values from the incoming *flow*."""
        # will be redefined in __init__
        # for val in flow:
        #     yield self._el(val)

    def _fc_run(self, flow):
        """Implement *run* method for *FillCompute* element.

        First, *fill* is called for the whole flow,
        after the *flow* is exhausted, *compute* is called.
        """
        for arg in flow:
            self._el.fill(arg)
        results = self._el.compute()
        return results


class SourceEl(object):
    """Adapter to provide *__call__()* method.
    Name of the actually called method
    can be customized during the initialization.

    The :meth:`__call__()` method is a generator, which yields values.
    It doesn't accept any input flow.
    """

    def __init__(self, el, call=_SENTINEL):
        """Element *el* must contain a callable method *__call__*
        or be callable itself.

        If *call* function or method name is not provided,
        it is checked whether *el* is callable itself.

        If :class:`SourceEl` failed to instantiate with *el* and *call*,
        :exc:`.LenaTypeError` is raised.
        """
        _init_callable(self, el, call)

    def __call__(self):
        """Yield generated values."""
        # This fix is needed only for a special method,
        # https://docs.python.org/3/reference/datamodel.html#special-lookup
        # Methods with other names will be monkey-patched correctly.
        return self._call() # pylint: disable=no-member
