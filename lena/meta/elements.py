from copy import deepcopy

import lena.context
from lena.context import update_recursively


class SetContext(object):
    """Set static context for this sequence.

    Static context does not automatically update runtime context.
    Use :class:`UpdateContextFromStatic` for that.

    Static context can be used during the initialisation phase
    to set output directories, :class:`.Cache` names, etc.
    There is no way to update static context from runtime one.
    """

    def __init__(self, key, value):
        """*key* is a string representing a
        (possibly nested) dictionary key. *value* is its value.
        See :func:`.str_to_dict` for details.
        """

        # todo: key could be a complete dictionary
        # self._subcontext = lena.context.str_to_list(key)
        # self._value = value
        self._key = key
        self._value = value
        context = lena.context.str_to_dict(key, value)
        if isinstance(value, str) and '{{' in value:
            # need to know other context to render this one
            self._unknown_contexts = [(key, value)]
            self._context = {}
        else:
            self._context = context
        self._has_no_data = True

    def _get_context(self):
        return deepcopy(self._context)

    def __eq__(self, other):
        if not isinstance(other, SetContext):
            return NotImplemented
        return (self._key == other._key and self._value == other._value)

    def __repr__(self):
        val = self._value
        if isinstance(val, str):
            val = '"' + val + '"'
        return 'SetContext("{}", {})'.format(self._key, val)


class StoreContext():
    """Store static context. Use for debugging."""

    def __init__(self, name="", verbose=False):
        """*name* and *verbose* affect output and representation."""
        self._name = name
        self._context = {}
        self._verbose = verbose
        self._has_no_data = True

    def _set_context(self, context):
        if self._verbose:
            print("StoreContext({}): storing {}".format(self._name, context))
        self._context = context

    def __eq__(self, other):
        if not isinstance(other, StoreContext):
            return NotImplemented
        # todo: maybe _verbose should not be checked.
        # It does not affect any logic.
        # But this element is also only for debugging.
        return (
            self._name == other._name and
            self._verbose == other._verbose and
            # will be set in the sequence, not during the initialisation
            self._context == other._context
        )

    def __repr__(self):
        return "StoreContext({})".format(repr(self._context))


class UpdateContextFromStatic(object):
    """Update runtime context with the static one.

    Note that for runtime context later elements
    update previous values, but for static context
    it is the opposite (external and previous elements
    take precedence).
    """

    def __init__(self):
        self._context = {}

    def __eq__(self, other):
        if not isinstance(other, UpdateContextFromStatic):
            return NotImplemented
        return self._context == other._context

    def _set_context(self, context):
        self._context = context

    def run(self, flow):
        for val in flow:
            data, context = val
            # no template substitutions are done,
            # that would be too complicated, fragile and wrong
            update_recursively(context, deepcopy(self._context))
            yield (data, context)
