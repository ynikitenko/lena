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
from __future__ import print_function

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
        :exc:`~lena.core.LenaTypeError` is raised.
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

        If callable methods *fill* and *compute* were not found,
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        fill_method = getattr(el, fill, None)
        compute_method = getattr(el, compute, None)

        if callable(fill_method):
            self.fill = fill_method
        else:
            raise exceptions.LenaTypeError(
                "fill method {} must be callable".format(fill)
            )
        if callable(compute_method):
            self.compute = compute_method
        else:
            raise exceptions.LenaTypeError(
                "compute method {} must be callable".format(compute)
            )
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
        :exc:`~lena.core.LenaTypeError` is raised.

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

    A *FillRequest* element has methods *fill(value)* and *request()*.
    """

    def __init__(self, el, fill="fill", request="request", bufsize=1):
        """Names for *fill* and *request* can be customized
        during initialization.

        *FillRequest* can be initialized from a *FillCompute* element.
        If a callable *request* method was not found,
        *el* must have callable *compute* and *reset* methods.
        *request* in this case is *compute* followed by *reset*.

        By default, *FillRequest* implements *run* method
        that splits the flow into subslices of *bufsize* elements.
        If *el* has a callable *run* method,
        it is used instead of the default one.

        **Attributes**

        :attr:`bufsize` is the maximum size of subslices during *run*.

        *bufsize* must be a natural number,
        otherwise :exc:`~lena.core.LenaValueError` is raised.
        If callable *fill* and *request* methods were not found,
        or *FillRequest* could not be derived from *FillCompute*,
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        fill = getattr(el, fill, None)
        request = getattr(el, request, None)
        if not callable(fill):
            raise exceptions.LenaTypeError(
                "fill must be callable"
            )
        self.fill = fill
        if callable(request):
            self.request = request
        else:
            # derive from compute and reset
            compute = getattr(el, "compute", None)
            reset = getattr(el, "reset", None)
            if not callable(compute) or not callable(reset):
                raise exceptions.LenaTypeError(
                    "request must be callable"
                )
            self.request = self._compute_reset

        if(bufsize != int(bufsize) or bufsize < 1):
            raise exceptions.LenaValueError(
                "bufsize must be a natural number, {} provided".format(bufsize)
            )
        self.bufsize = int(bufsize)

        run = getattr(el, "run", None)
        if run and callable(run):
            self.run = run
        self._el = el

    def _compute_reset(self):
        for val in self._el.compute():
            yield val
        self._el.reset()

    def fill(self, value): # pylint: disable=no-self-use,unused-argument
        """Fill *self* with *value*.
        """
        raise exceptions.LenaNotImplementedError

    def request(self): # pylint: disable=no-self-use
        """Yield computed values.

        May be called at any time,
        the flow may still contain zero or more items.
        """
        raise exceptions.LenaNotImplementedError

    def run(self, flow):
        """Implement *run* method.

        First, *fill* is called for each value in a subslice of *flow*
        of *self.bufsize* size.
        After that, results are yielded from *self.request()*.
        This repeats until the *flow* is exhausted.

        If *fill* was not called even once (*flow* is empty),
        the results are undefined
        (for example, it can run *request* or raise an exception).
        If the last slice is empty, *request* is not run for that.
        Note that the last slice may contain less than *bufsize* values.
        If that is important, implement your own method.

        A slice is a non-materialized list,
        which means that it will not take place of *bufsize* in memory.
        """
        filled_once = False
        while True:
            buf = itertools.islice(flow, self.bufsize)
            # check whether the flow contains at least one element
            try:
                arg = next(buf)
            except StopIteration:
                if filled_once:
                    # if nothing was filled this time,
                    # don't yield anything
                    break
                else:
                    # *request* is run nevertheless.
                    for result in self.request():
                        yield result
                    break
            else:
                self.fill(arg)
                filled_once = True

            for arg in buf:
                self.fill(arg)
            for result in self.request():
                yield result


class Run(object):
    """Adapter for a *Run* element."""

    def __init__(self, el, run=_SENTINEL):
        """Name of the method *run* can be customized during initialization.

        If *run* argument is supplied, *el* must be None
        or it must have a callable method with name given by *run*.

        If *run* keyword argument is missing,
        then *el* is searched for a method *run*.
        If that is not found, a type cast is tried.

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
        :exc:`~lena.core.LenaTypeError` is raised.

        :class:`Run` is used implicitly during the initialization
        of :class:`~lena.core.Sequence`.
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
        """Yield transformed elements from the incoming *flow*."""
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
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        _init_callable(self, el, call)

    def __call__(self):
        """Yield generated values."""
        # This fix is needed only for a special method,
        # https://docs.python.org/3/reference/datamodel.html#special-lookup
        # Methods with other names will be monkey-patched correctly.
        return self._call() # pylint: disable=no-member
