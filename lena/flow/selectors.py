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
    """Determine whether an item should be selected.

    Generally, *selected* means the result is convertible to ``True``,
    but other values can be used as well.
    """

    def __init__(self, selector, raise_on_error=True):
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
        self._selector_repr = ""
        if inspect.isclass(selector):
            self._selector = lambda val: isinstance(
                lena.flow.get_data(val), selector
            )
            try:
                # warning: this will give a false positive
                # for different classes with the same name
                # todo, bug: string and class initialization
                # may give false positives.
                # Shall be fixed after I skip context
                # and use builtins instead of lambdas.
                self._selector_repr = selector.__name__
            except AttributeError:
                pass
        elif callable(selector):
            self._selector = selector
            try:
                # __name__ works better for builtin functions
                self._selector_repr = selector.__name__
            except AttributeError:
                pass  # will use __repr__
        elif isinstance(selector, str):
            self._selector = lambda val: lena.context.contains(
                lena.flow.get_context(val), selector
            )
            self._selector_repr = "\"{}\"".format(selector)
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

        if not self._selector_repr:
            # we set it here, because
            # _selector is not initialized in the beginning
            self._selector_repr = repr(self._selector)

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

    def __eq__(self, other):
        if not isinstance(other, Selector):
            return NotImplemented
        # if the functions are at different addresses,
        # then we have same representation (good for creation),
        # but unequal objects. It is against false positives.
        if self._selector_repr:
            # since we use lambdas for types and strings,
            # their initial representations
            # will provide a better comparison.
            return self._selector_repr == other._selector_repr
        return self._selector == other._selector

    def __repr__(self):
        # this representation does not include the address,
        # but can be used for initialization, see
        # https://stackoverflow.com/a/1436756/952234
        return "Selector({})".format(self._selector_repr)


class Not(Selector):
    """Negate a selector."""

    def __init__(self, selector, raise_on_error=True):
        """*selector* is an instance of :class:`.Selector`
        or will be used to initialize that.

        *raise_on_error* is used during the initialization of
        *selector* and has the same meaning as in :class:`.Selector`.
        It has no effect if *selector* is already initialized.
        """
        super(Not, self).__init__(selector, raise_on_error)

    def __call__(self, value):
        """Negate the result of the initialized *selector*.

        If *raise_on_error* is ``False``, then this
        is a complete negation (including the case of an error
        encountered in the *selector*).
        If *raise_on_error* is ``True``,
        then any occurred exception will be raised here.
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
