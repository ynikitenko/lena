from .selectors import Selector as _Selector


class Filter():
    """Filter values from flow."""

    def __init__(self, selector):
        """*selector* is a boolean function.
        If it returns ``True``, the value passes :class:`Filter`.
        If *selector* is not callable, it is converted to
        a :class:`.Selector`.
        If the conversion could not be done,
        :exc:`.LenaTypeError` is raised.

        Note
        ----
            :class:`Filter` appeared in Lena only in version 0.4.
            There may be better alternatives to using this element:

            - don't produce values that you will discard later.
              If you want to select data from a specific file,
              read only that file.
            - use a custom class. *SelectPosition("border")* is more
              readable and maintainable than a :class:`Filter`
              with many conditions, and it is also more *cohesive*
              if you group several options
              like "center" or "top" in a single place.
              If you make a selection, it can be useful
              to add information about that to the *context*
              (and :class:`Filter` does not do that).
        
            This doesn't mean that we recommend against this class:
            sometimes it can be quick and explicit, and if one's
            class name provides absolutely no clue what it does,
            a general :class:`Filter` would be more readable.

        .. versionadded:: 0.4
        """
        if not callable(selector):
            selector = _Selector(selector)
        self._selector = selector

    def fill_into(self, element, value):
        """Fill *value* into an *element* if
        *selector(value)* is ``True``.

        *Element* must have a *fill(value)* method.
        """
        if self._selector(value):
            element.fill(value)

    def run(self, flow):
        """Yield values from the *flow* for which
        the *selector* is ``True``.
        """
        return (val for val in flow if self._selector(val))
        # or
        # for val in flow:
        #     if self._selector(val):
        #         yield event
