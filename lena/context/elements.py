from lena.core import LenaKeyError
from .functions import str_to_list, get_recursively
# todo: fix imports.
# import lena.flow.functions
# from lena.flow import get_data_context


class DeleteContext():

    def __init__(self, key):
        """Delete a given *key* from context.

        *key* can be a dot-separated string or a list
        of nested string keys.

        .. versionadded:: 0.6
        """
        # todo: think about general requirements, do we use only
        # lists, only tuples, or can we mix them?
        if isinstance(key, tuple):
            key = list(key)
        if not isinstance(key, list):
            keyl = str_to_list(key)
        else:
            keyl = key
        # empty key removes the entire context.
        # Therefore it is not default.
        self._keyl = keyl
        # todo (if needed): add a kwarg raise_on_missing
        # (for now skipped).

    def __call__(self, value):
        """Remove *key* from the context part of *value*.

        If the *value* contains no such key, it is ignored.
        """
        # todo: improve imports. Remove circular ones.
        from lena.flow import get_data_context
        data, context = get_data_context(value)
        subcont_key, key = self._keyl[:-1], self._keyl[-1]
        try:
            subcont = get_recursively(context, subcont_key)
        except LenaKeyError:
            return value

        try:
            del subcont[key]
        except KeyError:
            pass
        return value
