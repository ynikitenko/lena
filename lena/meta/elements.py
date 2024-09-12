from copy import deepcopy

from lena.core import LenaAttributeError, LenaKeyError
from lena.context import format_update_with, update_recursively


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

        *value* can be a formatting string.
        See :func:`.format_context` for details.
        """

        # todo: key could be an entire dictionary
        # self._subcontext = lena.context.str_to_list(key)
        # self._value = value
        self._key = key
        self._value = value
        self._has_no_data = True
        try:
            self._set_context({})
            # may also raise formatting errors, checking early here.
        except LenaKeyError:
            # formatting keys missing
            pass

    def _get_context(self):
        try:
            sc = self._static_context
        except AttributeError:
            # one does not expect el._get_context() to raise
            # AttributeError, but this is the meaning of that exception
            # (a class field was not initialised).
            raise LenaAttributeError(
                "static context missing. Run _set_context to set that."
            )
        # we want to keep our context safe, therefore deepcopy.
        # It makes little difference to optimise in a Sequence.
        return deepcopy(sc)

    def _set_context(self, context):
        # we assume that context was already deeply copied if needed
        try:
            format_update_with(self._key, self._value, context)
        except LenaKeyError as exc:
            raise exc
        else:
            self._static_context = context

    def __eq__(self, other):
        if not isinstance(other, SetContext):
            return NotImplemented
        # we compare key and value, not the formatted value,
        # because we are comparing elements, not their environment.
        return (self._key == other._key and self._value == other._value)

    def __repr__(self):
        val = self._value
        if isinstance(val, str):
            val = '"' + val + '"'
        # representation like it was during the initialisation,
        # not with the set context.
        return 'SetContext("{}", {})'.format(self._key, val)


class StoreContext():
    """Store static context. Use for debugging."""

    def __init__(self):
        # todo: make context a read-only property.
        # todo: add to docstring.
        self.context = {}
        # no need to print during setting context.
        # Patch this code manually if needed.
        # self._verbose = verbose
        self._has_no_data = True

    def _set_context(self, context):
        # since there is no _get_context, we need to make
        # a deep copy here, otherwise further elements
        # might influence our context.
        self.context = deepcopy(context)

    def __eq__(self, other):
        if not isinstance(other, StoreContext):
            return NotImplemented
        return (
            # will be set in the sequence, not during the initialisation
            self.context == other.context
        )

    def __repr__(self):
        # we want our element to be able to be initialised
        # by copying its representation,
        # and Python has no inline commentaries
        return 'StoreContext() or "{}"'.format(repr(self.context))


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
