"""Select specific items."""
import inspect

import lena.context
import lena.core
import lena.flow


# see no reason to make them public.
# This is more like an internal implementation of Selector.
class _SelectorOr(object):

    def __init__(self, args, raise_on_error=True):
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

    def __eq__(self, other):
        # this is a strict comparison,
        # because _SelectorOr with one element will give same results
        # as _SelectorAnd or a Selector.
        if not isinstance(other, _SelectorOr):
            return NotImplemented
        return self._selectors == other._selectors

    def __repr__(self):
        return "[{}]".format(", ".join([repr(s) for s in self._selectors]))


class _SelectorAnd(object):

    def __init__(self, args, raise_on_error=True):
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

    def __eq__(self, other):
        if not isinstance(other, _SelectorAnd):
            return NotImplemented
        return self._selectors == other._selectors

    def __repr__(self):
        return "({})".format(", ".join([repr(s) for s in self._selectors]))


class Selector(object):
    """A boolean function on values."""

    def __init__(self, selector, raise_on_error=True):
        """The usage of *selector* depends on its type.

        If *selector* is a class,
        :meth:`__call__` checks that data part of the value
        is subclassed from that.

        A callable is used as it is.

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
        will be used recursively during the initialization of its items.
        """
        # Callable classes are treated as classes, not callables
        self._selector_repr = ""
        # callables should be compared as they are
        self._from_callable = False
        # to avoid false positives
        # for different classes with the same name
        self._orig_class = None
        self._orig_str = None

        if inspect.isclass(selector):
            self._selector = lambda val: isinstance(
                lena.flow.get_data(val), selector
            )
            try:
                self._selector_repr = selector.__name__
            except AttributeError:
                pass
            self._orig_class = selector
        elif callable(selector):
            self._selector = selector
            try:
                # __name__ works better for builtin functions
                self._selector_repr = selector.__name__
            except AttributeError:
                pass  # will use __repr__
            self._from_callable = True
        elif isinstance(selector, str):
            self._selector = lambda val: lena.context.contains(
                lena.flow.get_context(val), selector
            )
            self._selector_repr = "\"{}\"".format(selector)
            self._orig_str = selector
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
                "Selector must be initialized from a callable, "
                "list, tuple or string; {} provided".format(selector)
            )
        self._raise_on_error = bool(raise_on_error)

        if not self._selector_repr:
            self._selector_repr = repr(self._selector)

    def __call__(self, value):
        """Check whether *value* is selected.

        If an exception occurs and *raise_on_error* is ``False``,
        the result is ``False``.
        This could be used while testing potentially
        non-existing attributes or arbitrary contexts.
        However, this is not recommended,
        since it covers too many errors and some of them should be
        raised explicitly.
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

    def __eq__(self, other):
        if not isinstance(other, Selector):
            return NotImplemented
        if self._raise_on_error != other._raise_on_error:
            return False

        if self._orig_class is not None:
            return self._orig_class == other._orig_class
        if self._orig_str is not None:
            return self._orig_str == other._orig_str
        if self._from_callable:
            return self._selector == other._selector
        # for And and Or
        return self._selector == other._selector

    def __repr__(self):
        # see basics of repr at
        # https://stackoverflow.com/a/1436756/952234
        if self._raise_on_error is False:
            return "Selector({}, raise_on_error=False)".format(self._selector_repr)
        return "Selector({})".format(self._selector_repr)


class Not(Selector):
    """Negate a selector."""

    def __init__(self, selector, raise_on_error=True):
        """*selector* is converted to :class:`.Selector`.

        *raise_on_error* has the same meaning as in :class:`.Selector`.
        """
        # note: if selector is a Selector with raise_on_error=False,
        # this raise_on_error will have no effect.
        super(Not, self).__init__(selector, raise_on_error)

    def __call__(self, value):
        """Negate the result of the *selector*.

        If *raise_on_error* is ``False``, then this
        is a full negation (including the case of an error
        encountered in the *selector*).
        If *raise_on_error* is ``True``,
        then any occurred exception will be re-raised here.
        """
        return not super(Not, self).__call__(value)

    def __eq__(self, other):
        if not isinstance(other, Not):
            if isinstance(other, Selector):
                # otherwise will falsely compare them
                return False
            return NotImplemented
        return super(Not, self).__eq__(other)

    def __repr__(self):
        if self._raise_on_error is False:
            return "Not({}, raise_on_error=False)".format(self._selector_repr)
        return "Not({})".format(self._selector_repr)
