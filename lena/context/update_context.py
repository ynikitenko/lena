from __future__ import print_function

import copy

import lena.core
import lena.flow


class UpdateContext():
    """Update context of passing values."""

    def __init__(self, subcontext, update, recursively=True):
        """*subcontext* is a string representing the part of context
        to be updated (for example, *output.plot*).
        If *subcontext* is an empty string,
        all context will be overwritten.

        *update* is a dictionary that will become
        the value of *subcontext*.

        If *recursively* is ``True`` (default), not overwritten
        existing values of *subcontext* are preserved.
        Otherwise, all existing values of *subcontext* (at its lowest level)
        are removed.
        See also :func:`.update_recursively`.

        Example:

        >>> from lena.context import UpdateContext
        >>> make_scatter = UpdateContext("output.plot", {"scatter": True})
        >>> # use it in a sequence

        The context in the class name means any general context
        (not only :class:`.Context`).

        In case of wrong types of *subcontext* or *update*
        :exc:`.LenaTypeError` is raised.
        """
        # subcontext is a string, because it must have at most one value
        # at each nesting level.
        # todo. update may be made a string in the future.
        # todo. also, subcontext may be done a format string "{variable.name}",
        # but this is not implemented (think about it in the future).
        if not isinstance(subcontext, str):
            raise lena.core.LenaTypeError(
                "subcontext must be a string, {} provided".format(subcontext)
            )
        if not isinstance(update, dict):
            raise lena.core.LenaTypeError(
                "update must be a dict, {} provided".format(update)
            )
        self._subcontext = lena.context.str_to_list(subcontext)
        self._update = update
        self._recursively = bool(recursively)

    def __call__(self, value):
        """Update context of the *value*.

        If *value*'s context doesn't contain *subcontext*, it is created.
        If the *value* contains no context, it is also created.
        """
        data, context = lena.flow.get_data_context(value)
        if self._subcontext == []:
            # overwrite all context. This may be undesirable,
            # but better than throwing an error
            # in the middle of calculations.
            # Context is not so much important.
            # Overwrite all context, for uniformity with other cases.
            if self._recursively:
                lena.context.update_recursively(context, self._update)
            else:
                context.clear()
                context.update(copy.deepcopy(self._update))
            return (data, context)
        keys = self._subcontext
        subdict = context
        for key in keys[:-1]:
            if key not in subdict or not isinstance(subdict[key], dict):
                subdict[key] = {}
            subdict = subdict[key]
        if self._recursively:
            lena.context.update_recursively(subdict, {keys[-1]: self._update})
        else:
            subdict[keys[-1]] = self._update
        return (data, context)
