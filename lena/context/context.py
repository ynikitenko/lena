"""Make better output for context. Example:

>>> from lena.context import Context
>>> c = Context({"1": 1, "2": {"3": 4}})
>>> print(c) # doctest: +NORMALIZE_WHITESPACE
{
    "1": 1,
    "2": {
        "3": 4
    }
}
"""
from __future__ import print_function

import json

import lena.core
import lena.flow


class Context(dict):
    """Dictionary with easy-to-read formatting."""

    def __init__(self, d={}, formatter=None):
        """Initialize from a dictionary *d*.

        Representation is defined by the *formatter*.
        That must be a callable,
        which should accept a dictionary and return a string.
        The default is ``json.dumps``.

        Tip
        ---
            JSON and Python representations are different.
            In particular, JSON *True* is written lowercase *true*.
            To convert JSON back to Python, use ``json.loads(string)``.

        If *formatter* is given but is not callable,
        :exc:`~lena.core.LenaTypeError` is raised.
        """
        super(Context, self).__init__(d)
        if formatter is not None:
            if not callable(formatter):
                raise lena.core.LenaTypeError(
                    "formatter must be callable, "
                    "{} given".format(formatter)
                )
            self.formatter = formatter
        else:
            self.formatter = lambda s: json.dumps(s, sort_keys=True, indent=4)
        # self.formatter = pprint.PrettyPrinter(indent=1)

    def __repr__(self):
        return self.formatter(self)

    def __call__(self, value):
        """Convert *value*'s context to :class:`Context` on the fly.

        If the *value* is a *(data, context)* pair,
        convert its context part to :class:`Context`.
        If the *value* doesn't contain a context,
        it is created as an empty :class:`Context`.
        """
        data, context = (lena.flow.get_data(value),
                         lena.flow.get_context(value))
        return (data, Context(context))
