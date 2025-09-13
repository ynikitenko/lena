"""Context managers allow application of functions
only to data or context parts of the flow. Example:

.. code-block:: python

    s = Source(
        # read data ...
        # add context
        UpdateContext(...),
        Context(
            # apply functions only to context
            deepcopy,
            other_function,
        ),
        # other elements again use data and context
    )

.. seealso:: :class:`.DropContext` to transform only data parts.
"""

from .compose import compose
from .functions import get_data_context


class Context():
    """Apply transformation only to the context part of the flow."""

    def __init__(self, *seq):
        """*seq* is a sequence of callables, which will be applied to
        the context part of the value.

        .. versionadded:: 0.6
        """
        self._seq = compose(*seq)

    def __call__(self, val):
        data, context = get_data_context(val)
        return (data, self._seq(context))
