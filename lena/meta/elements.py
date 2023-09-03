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
        self._context = lena.context.str_to_dict(key, value)
        self._has_no_data = True

    def _get_context(self):
        return deepcopy(self._context)

    def __repr__(self):
        val = self._value
        if isinstance(val, str):
            val = '"' + val + '"'
        return 'SetContext("{}", {})'.format(self._key, val)


class UpdateContextFromStatic(object):
    """Update runtime context with the static one.

    Note that for runtime context later elements
    update previous values, but for static context
    it is the opposite (external and previous elements
    take precedence).
    """

    def __init__(self):
        self._context = {}

    def _set_context(self, context):
        self._context = context

    def run(self, flow):
        for val in flow:
            data, context = val
            # no template substitutions are done,
            # that would be too complicated, fragile and wrong
            update_recursively(context, deepcopy(self._context))
            yield (data, context)
