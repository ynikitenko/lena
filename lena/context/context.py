""":class:`Context` provides a better representation for context."""
import functools
import json

import lena.core
# import lena.flow


class Context(dict):
    """Dictionary with easy-to-read formatting.

    :class:`Context` provides a better representation for context. Example:

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

    def __init__(self, d=None, formatter=None):
        """Initialize from a dictionary *d* (empty by default).

        Representation is defined by the *formatter*.
        That must be a callable accepting a dictionary
        and returning a string. The default is ``json.dumps``.

        All public attributes of a :class:`Context`
        can be retrieved or set using dot notation
        (for example, *context["data_path"]*
        is equal to *context.data_path*).
        Multiple levels of nesting using dot notation are allowed.

        Tip
        ---
            `JSON <https://docs.python.org/3/library/json.html>`_
            and Python representations are different.
            In particular, JSON *True* is written as lowercase *true*.
            To convert JSON back to Python, use ``json.loads(string)``.

        If the attribute to be retrieved is missing,
        :exc:`.LenaAttributeError` is raised.
        An attempt to access a private attribute raises
        :exc:`AttributeError`.
        """
        # This class does three different simple things:
        # - pretty formatting for a dict.
        # - element for pretty formatting of a dict.
        # - object with attribute access through dot notation.
        # A better alternative for the latter could be
        # `types.SimpleNamespace <https://docs.python.org/3/library/types.html#types.SimpleNamespace>`_
        # (since Python 3.3) or third-party libraries.
        if d is None:
            d = {}
        super(Context, self).__init__(d)
        if formatter is not None:
            if not callable(formatter):
                raise lena.core.LenaTypeError(
                    "formatter must be callable, "
                    "{} given".format(formatter)
                )
            self._formatter = formatter
        else:
            self._formatter = functools.partial(json.dumps,
                                                sort_keys=True, indent=4)
            # same, but doesn't allow pickling
            # lambda s: json.dumps(s, sort_keys=True, indent=4)
        # formatter should be private,
        # otherwise it'll mess with other attributes
        # self._formatter = pprint.PrettyPrinter(indent=1)

    def __call__(self, value):
        """Convert *value*'s context to :class:`Context` on the fly.

        If the *value* is a *(data, context)* pair,
        convert its context part to :class:`Context`.
        If the *value* doesn't contain a context,
        it is created as an empty :class:`Context`.

        When a :class:`Context` is used as a sequence element,
        its initialization argument *d*
        has no effect on the produced values.
        """
        data, context = value
        # data, context = lena.flow.get_data_context(value)
        return (data, Context(context))

    def __getattr__(self, name):
        # we don't implement getting nested attributes,
        # because that would require creating proxy objects.
        # Use more sophisticated libraries for that.
        
        if name.startswith('_'):
            # this is not LenaAttributeError,
            # as it wouldn't be so for other Lena classes
            # that don't implement __getattr__ .
            # Same is done for Variable.
            raise AttributeError(name)
        try:
            val = self[name]
        except KeyError:
            # todo: should LenaAttributeError be used here at all?
            raise lena.core.LenaAttributeError(
                "{} missing".format(name)
            )
        else:
            if isinstance(val, dict):
                # transform subdictionaries on the fly
                if not isinstance(val, Context):
                    val = self[name] = Context(val)
                return val
            return val

    def _repr_nested(self, base_indent="", indent=" "*4, el_separ=",\n"):
        # representation within a Lena Sequence.
        # Initialization arguments are not printed,
        # for they are not needed there, and the formatter is callable.
        return base_indent + "Context()"

    def __repr__(self):
        return self._formatter(self)

    def __setattr__(self, attr, value):
        if attr in ["_formatter"]:
            # from https://stackoverflow.com/a/17020163/952234,
            # "How to use __setattr__ correctly,
            # avoiding infinite recursion"
            super(Context, self).__setattr__(attr, value)
        elif attr.startswith('_'):
            raise AttributeError(attr)
        else:
            self[attr] = value
