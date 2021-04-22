"""Select specific items."""
from __future__ import print_function

import inspect

import lena.context
import lena.core
import lena.flow


# may be made public if there appears a reason
# to prohibit nested ()s and []s and force user
# to define type explicitly.
class _SelectorOr(object):
    def __init__(self, args, raise_on_error=False):
        self._selectors = []
        for arg in args:
            if isinstance(arg, Selector):
                self._selectors.append(arg)
            else:
                # may raise
                self._selectors.append(
                    Selector(arg, raise_on_error=raise_on_error)
                )

    def __call__(self, val):
        return any((f(val) for f in self._selectors))


class _SelectorAnd(object):
    def __init__(self, args, raise_on_error=False):
        self._selectors = []
        for arg in args:
            if isinstance(arg, Selector):
                self._selectors.append(arg)
            else:
                # may raise
                self._selectors.append(
                    Selector(arg, raise_on_error=raise_on_error)
                )

    def __call__(self, val):
        return all((f(val) for f in self._selectors))


class Selector(object):
    """Determine whether an item should be selected.

    Generally, *selected* means the result is convertible to ``True``,
    but other values can be used as well.
    """

    def __init__(self, selector, raise_on_error=False):
        """The usage of *selector* depends on its type.

        If *selector* is a class,
        :meth:`__call__` checks that data part of the value
        is subclassed from that.

        A callable is used as is.

        A string means that value's context must conform to that
        (as in :func:`context.contains <.contains>`).

        *selector* can be a container. In this case its items
        are converted to selectors.
        If *selector* is a *list*, the result is *or* applied to
        results of each item.
        If it is a *tuple*, boolean *and* is applied to the results.

        *raise_on_error* is a boolean that sets
        whether in case of an exception
        the selector raises that exception
        or returns ``False``.
        If *selector* is a container, *raise_on_error*
        will be used during its items initialization (recursively).

        If incorrect arguments are provided,
        :exc:`.LenaTypeError` is raised.
        """
        # Callable classes are treated as classes, not callables
        if inspect.isclass(selector):
            self._selector = lambda val: isinstance(
                lena.flow.get_data(val), selector
            )
        elif callable(selector):
            self._selector = selector
        elif isinstance(selector, str):
            self._selector = lambda val: lena.context.contains(
                lena.flow.get_context(val), selector
            )
        elif isinstance(selector, list):
            try:
                self._selector = _SelectorOr(selector, raise_on_error)
            except lena.core.LenaTypeError as err:
                raise err
        elif isinstance(selector, tuple):
            try:
                self._selector = _SelectorAnd(selector, raise_on_error)
            except lena.core.LenaTypeError as err:
                raise err
        else:
            raise lena.core.LenaTypeError(
                "Selector must be initialized with a callable, list or tuple, "
                "{} provided".format(selector)
            )
        self._raise_on_error = bool(raise_on_error)

    def __call__(self, value):
        """Check whether *value* is selected.

        By default, if an exception occurs, the result is ``False``.
        Thus it is safe to use non-existing attributes
        or arbitrary contexts.
        However, if *raise_on_error* was set to ``True``,
        the exception will be raised.
        Use it if you are confident in the data
        and want to see any error.
        """
        try:
            sel = self._selector(value)
        except Exception as err:  # pylint: disable=broad-except
            # it can be really any exception: AttributeError, etc.
            if self._raise_on_error:
                raise err
            return False
        else:
            return sel


class Not(Selector):
    """Negate a selector."""

    def __init__(self, selector, raise_on_error=False):
        """*selector* is an instance of :class:`.Selector`
        or will be used to initialize that.

        *raise_on_error* is used during the initialization of
        *selector* and has the same meaning as in :class:`.Selector`.
        It has no effect if *selector* is already initialized.
        """
        if not isinstance(selector, Selector):
            selector = Selector(selector, raise_on_error)
        self._selector = selector
        super(Not, self).__init__(self._selector)

    def __call__(self, value):
        """Negate the result of the initialized *selector*.

        If *raise_on_error* is ``False``, then this
        is a complete negation (including the case of an error
        encountered in the *selector*).
        For example, if the *selector* is *variable.name*,
        and *value*'s context contains no *"variable"*,
        *Not("variable.name")(value)* will be ``True``.
        If *raise_on_error* is ``True``,
        then any occurred exception will be raised here.
        """
        return not self._selector(value)
