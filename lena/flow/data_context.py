"""Context managers allow application of functions
only to data or context parts of the flow. Example:

.. code-block:: python

    s = Source(
        # read data ...
        # add context
        UpdateContext(...),
        Context(
            # apply functions only to the context
            copy.deepcopy,  # makes more sense in Split
            other_function,
        ),
        # transform only data part of the value
        Data(lambda val: {"sum": val}),
        # the same could be achieved with
        # lambda val: ({"sum": val[0]}, val[1]),
        # but Data makes it more explicit and structured.
        # ...
        # other elements again use both data and context
    )
"""

from .compose import compose
from .functions import get_data_context


class Data():
    """Apply transformation only to the data part of the flow."""

    def __init__(self, *seq):
        """*seq* is a sequence of callables (one-to-one elements),
        which will be applied to the data part of the value.

        The advantage of this element is its simplicity
        and flexibility (can also be used in a *Fill* sequence).

        .. seealso:: :class:`.DropContext` to use not only callables,
            but also any-to-any (*Run*) elements.

        .. versionadded:: 0.6
        """
        self._seq = compose(*seq)

    def __call__(self, value):
        """Apply self to the data part of the *value*."""
        data, context = get_data_context(value)
        return (self._seq(data), context)


class Context():
    """Apply transformation only to the context part of the flow."""

    def __init__(self, *seq):
        """*seq* is a sequence of callables, which will be applied to
        the context part of the value.

        .. versionadded:: 0.6
        """
        self._seq = compose(*seq)

    def __call__(self, value):
        """Apply self to the context part of the *value*."""
        data, context = get_data_context(value)
        return (data, self._seq(context))
