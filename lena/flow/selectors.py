"""Select specific items."""
import inspect

import lena.context
import lena.core
import lena.flow
from lena.flow import get_context
from lena.context import get_recursively


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
                # todo: add a test where that can happen.
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
                self._selector = Or(selector, raise_on_error)
            except lena.core.LenaTypeError as err:
                raise err
        elif isinstance(selector, tuple):
            try:
                self._selector = And(selector, raise_on_error)
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


class SelectContext(Selector):
    """Selector based on a subcontext."""

    def __init__(self, key, predicate, raise_on_error=True):
        # type: (str | list | dict, Callable, bool) -> None
        # for this to work properly, put
        # from typing import Callable
        # This has downsides of:
        # - importing another module,
        # - problems with other imports (MyPy will complain
        # that they are not annotated).
        # Those are not problems if a) importing is quick,
        # b) we add annotations to other Lena modules.
        # However, in Lena type hints are mostly unneeded, because
        # 1) types are not checked runtime. Most users won't benefit
        # from them: scientists simply run code, not check types.
        # It's hard to think about developers yet.
        # 2) tests might be a more powerful and flexible tool.
        # 3) documentation may be sufficient for many users. See also
        # Python standard library docs: they mostly use no type hints.
        # 4) Lena sequences are rather general. Types won't help much.
        # 5) type comments are better than stub files (for they keep
        # types together with their code), but they might be dropped in
        # future Python version. https://github.com/python/mypy/issues/12947
        # So in the long run, if we ever decide to use type comments,
        # we shall probably use stubs. See a nice article on the topic,
        # https://realpython.com/python-type-checking/#pros-and-cons
        #
        # For example, the assertions below are better than type hints,
        # because they will help users who didn't run type hints.
        # So unfortunately they are necessary.
        assert isinstance(key, (str, list, dict))
        assert callable(predicate)
        self._key = key
        self._predicate = predicate
        self._raise_on_error = bool(raise_on_error)

    def __call__(self, value):
        context = get_context(value)
        try:
            subcontext = get_recursively(context, self._key)
        except LenaKeyError:
            # we don't specify a special behaviour here
            # (like raise_on_key_error),
            # because the result may be more complicated:
            # a dict instead of a string, etc.
            # A general context check would be more detailed.
            return False

        # copied from Selector
        try:
            res = self._predicate(subcontext)
        except Exception as err:  # pylint: disable=broad-except
            if self._raise_on_error:
                raise err
            return False
        else:
            return res


class And(Selector):
    """And-test of multiple selectors."""

    def __init__(self, selectors, raise_on_error=True):
        """*selectors* is a tuple of items, each of which
        is a :class:`Selector` or will be converted to that.

        *raise_on_error* has the same meaning as in :class:`Selector`,
        and will be applied to each newly initialized subselector.
        """
        self._selectors = []
        for sel in selectors:
            if isinstance(sel, Selector):
                self._selectors.append(sel)
            else:
                # may raise
                self._selectors.append(
                    Selector(sel, raise_on_error=raise_on_error)
                )
        super(And, self).__init__(self, raise_on_error)

    def __call__(self, val):
        return all((f(val) for f in self._selectors))

    def __eq__(self, other):
        if not isinstance(other, And):
            return NotImplemented
        return self._selectors == other._selectors

    def __repr__(self):
        args_repr = "{}".format(", ".join([repr(s) for s in self._selectors]))
        if not self._raise_on_error:
            return "And(({}), raise_on_error=False)".format(args_repr)
        return "And(({}))".format(args_repr)


class Or(Selector):
    """Or-test of multiple selectors."""

    def __init__(self, selectors, raise_on_error=True):
        """*selectors* is a list of items, each of which
        is a :class:`Selector` or will be converted to that.
        Evaluation is short-circuit, that is if a selector was
        true, further ones are not applied.

        *raise_on_error* has the same meaning as in :class:`Selector`,
        and will be applied to each newly initialized subselector.
        """
        self._selectors = []
        for sel in selectors:
            if isinstance(sel, Selector):
                self._selectors.append(sel)
            else:
                # may raise
                self._selectors.append(
                    Selector(sel, raise_on_error=raise_on_error)
                )
        # Or will be a callable in the super class
        super(Or, self).__init__(self, raise_on_error)

    def __call__(self, val):
        return any((f(val) for f in self._selectors))

    def __eq__(self, other):
        # we compare classes.
        # Note that selection results of Or with one element
        # will be the same as for And or a Selector.
        # todo: could optimise.
        if not isinstance(other, Or):
            return NotImplemented
        return self._selectors == other._selectors

    def __repr__(self):
        args_repr = "{}".format(", ".join([repr(s) for s in self._selectors]))
        if not self._raise_on_error:
            return "Or([{}], raise_on_error=False)".format(args_repr)
        return "Or([{}])".format(args_repr)


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
        # todo: is it dangerous that self.__call__
        # and super.__call__ give different results?
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
