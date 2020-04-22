from __future__ import print_function

import copy

import lena.core
import lena.flow


class UpdateContext():
    """Update context of passing values."""

    def __init__(self, subcontext, update, recursively=True):
        """*subcontext* is a string representing the part of context
        to be updated (for example, *output.plot*).
        *subcontext* must be non-empty.

        *update* will become the value of *subcontext*.
        If it is a string, *update* can contain arguments
        to be got from context (for example: "{variable.name}").
        In this case the result is always a string.
        For formatting details see :func:`.format_context`.

        If *recursively* is ``True`` (default), not overwritten
        existing values of *subcontext* are preserved.
        Otherwise, all existing values of *subcontext* (at its lowest level)
        are removed.
        See also :func:`.update_recursively`.

        Example:

        >>> from lena.context import UpdateContext
        >>> make_scatter = UpdateContext("output.plot", {"scatter": True})
        >>> # use it in a sequence

        The "Context" in the class name means any general context
        (not only :class:`.Context`).

        If *subcontext* is not a string, :exc:`.LenaTypeError` is raised.
        If it is empty, :exc:`.LenaValueError` is raised.
        """
        # subcontext is a string, because it must have at most one value
        # at each nesting level.
        # todo. subcontext might be also created as a format string
        # "{variable.name}", (think about it in the future).
        if not isinstance(subcontext, str):
            raise lena.core.LenaTypeError(
                "subcontext must be a string, {} provided".format(subcontext)
            )
        if not subcontext:
            raise lena.core.LenaValueError(
                "subcontext must be non-empty"
            )
        self._subcontext = lena.context.str_to_list(subcontext)
        if isinstance(update, str):
            self._update = lena.context.format_context(update)
        else:
            self._update = update
        self._recursively = bool(recursively)

    def __call__(self, value):
        """Update context of the *value*.

        If *value*'s context doesn't contain *subcontext*, it is created.
        If the *value* contains no context, it is also created.
        """
        data, context = lena.flow.get_data_context(value)
        if callable(self._update):
            # it is always a string, which is immutable
            update = self._update(context)
        else:
            update = copy.deepcopy(self._update)
        # now empty context is prohibited.
        # May be skipped in runtime in the future.
        assert self._subcontext
        keys = self._subcontext
        subdict = context
        for key in keys[:-1]:
            if key not in subdict or not isinstance(subdict[key], dict):
                subdict[key] = {}
            subdict = subdict[key]
        if self._recursively:
            lena.context.update_recursively(subdict, {keys[-1]: update})
        else:
            subdict[keys[-1]] = update
        return (data, context)
