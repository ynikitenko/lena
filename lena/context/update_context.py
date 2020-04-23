from __future__ import print_function

import copy

import lena.core
import lena.context
import lena.flow


_sentinel = object()


class UpdateContext():
    """Update context of passing values."""

    def __init__(self, subcontext, update, default=_sentinel, recursively=True):
        """*subcontext* is a string representing the part of context
        to be updated (for example, *output.plot*).
        *subcontext* must be non-empty.

        *update* will become the value of *subcontext*.
        If it is a string enclosed in braces,
        *update* will get its value from context during :meth:`__call__`
        (example: "{variable.name}").
        If the string is missing in the context, :exc:`.LenaKeyError`
        will be raised unless a *default* is set.
        In this case *default* will be used for update.
        If *update* is a string containing no curly braces,
        it will be used for update itself.

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
        Braces can be only the first and the last symbols
        of *update*, otherwise :exc:`.LenaValueError` is raised.
        """
        # subcontext is a string, because it must have at most one value
        # at each nesting level.
        if not isinstance(subcontext, str):
            raise lena.core.LenaTypeError(
                "subcontext must be a string, {} provided".format(subcontext)
            )
        if not subcontext:
            raise lena.core.LenaValueError(
                "subcontext must be non-empty"
            )
        self._subcontext = lena.context.str_to_list(subcontext)
        if not isinstance(update, str):
            self._update = update
        elif '{' in update or '}' in update:
            braceless_str = update[1:-1]
            if (update[0] != '{' or update[-1] != '}'
                or '{' in braceless_str or '}' in braceless_str):
                raise lena.core.LenaValueError(
                    "update can contain braces only as its first "
                    "and last symbols, {} provided".format(update)
                )
            self._get_value = True
            self._update = braceless_str
            self._default = default
        else:
            self._get_value = False
            self._update = update
        self._recursively = bool(recursively)

    def __call__(self, value):
        """Update context of the *value*.

        If *value*'s context doesn't contain *subcontext*, it is created.
        If the *value* contains no context, it is also created.
        """
        data, context = lena.flow.get_data_context(value)
        if isinstance(self._update, str):
            if self._get_value:
                # formatting braces are present
                if self._default is _sentinel:
                    # no default is provided
                    update = lena.context.get_recursively(context,
                                                          self._update)
                else:
                    update = lena.context.get_recursively(
                        context, self._update, self._default
                    )
                update = copy.deepcopy(update)
            else:
                update = self._update
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
