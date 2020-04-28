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
    def __init__(self, *args):
        self._selectors = []
        for arg in args:
            if isinstance(arg, Selector):
                self._selectors.append(arg)
            else:
                # may raise
                self._selectors.append(Selector(arg))

    def __call__(self, val):
        return any((f(val) for f in self._selectors))


class _SelectorAnd(object):
    def __init__(self, *args):
        self._selectors = []
        for arg in args:
            if isinstance(arg, Selector):
                self._selectors.append(arg)
            else:
                # may raise
                self._selectors.append(Selector(arg))

    def __call__(self, val):
        return all((f(val) for f in self._selectors))


class Selector(object):
    """Determine whether an item should be selected.

    Generally, *selected* means the result is convertible to ``True``,
    but other values can be used as well.
    """

    def __init__(self, selector):
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
                self._selector = _SelectorOr(*selector)
            except lena.core.LenaTypeError as err:
                raise err
        elif isinstance(selector, tuple):
            try:
                self._selector = _SelectorAnd(*selector)
            except lena.core.LenaTypeError as err:
                raise err
        else:
            raise lena.core.LenaTypeError(
                "Selector must be initialized with a callable, list or tuple, "
                "{} provided".format(selector)
            )

    def __call__(self, value):
        """Check whether *value* is selected.

        If an exception occurs, the result is ``False``.
        Thus it is safe to use non-existing attributes
        or arbitrary contexts.
        """
        try:
            sel = self._selector(value)
        except Exception:  # pylint: disable=broad-except
            # it can be really any exception: AttributeError, etc.
            return False
        else:
            return sel


class Not(Selector):
    """Negate a selector."""

    def __init__(self, selector):
        """*selector* will initialize a :class:`.Selector`."""
        self._selector = Selector(selector)
        super(Not, self).__init__(self._selector)

    def __call__(self, value):
        """Negate the result of the initialized *selector*.

        This is a complete negation (including the case of an error
        encountered in the *selector*).
        For example, if the *selector* is *variable.name*,
        and *value*'s context contains no *"variable"*,
        *Not("variable.name")(value)* will be ``True``.
        """
        return not self._selector(value)
