from __future__ import print_function

import re

import lena.core
import lena.context
import lena.flow


def format_context(format_str, *args, **kwargs):
    """Create a function, which formats a given string using a context.

    *format_str* is an ordinary Python format string.
    *args* are positional and *kwargs* are keyword arguments.

    When calling *format_context*, arguments are bound and
    a new function is returned. When called with a context,
    its keys are extracted and formatted in *format_str*.

    Positional arguments in the *format_str* correspond to 
    *args*, which must be keys in the context. 
    Keys used as positional arguments may be nested
    (e.g. format_context("{}", "x.y")).

    Keyword arguments *kwargs* connect
    arguments between *format_str* and context.
    Example:

    >>> f = format_context("{y}", y="x.y")
    >>> f({"x": {"y": 10}})
    '10'

    All keywords in the *format_str* must have corresponding *kwargs*. 

    Keyword and positional arguments can be mixed. Example:

    >>> f = format_context("{}_{x}_{y}", "x", x="x", y="y")
    >>> f({"x": 1, "y": 2})
    '1_1_2'
    >>>

    If no *args* or *kwargs* are given, *kwargs* are extracted 
    from *format_str*. It must contain all non-empty replacement fields,
    and only simplest formatting without attribute lookup.
    Example:

    >>> f = format_context("{x}")
    >>> f({"x": 10})
    '10'

    If *format_str* is not a string, :exc:`LenaTypeError` is raised.
    All other errors are raised only during formatting.
    If context doesn't contain the needed key,
    :exc:`LenaKeyError` is raised.
    Note that string formatting can also raise
    a :exc:`KeyError` or an :exc:`IndexError`,
    so it is recommended to test your formatters before using them.
    """
    if not isinstance(format_str, str):
        raise lena.core.LenaTypeError(
            "format_str must be a string, {} given".format(format_str)
        )
    if not args and not kwargs:
        new_str = []
        new_args = []
        prev_char = ''
        ind = 0
        within_field = False
        while ind < len(format_str):
            c = format_str[ind]
            if c != '{' and not within_field:
                prev_char = c
                new_str.append(c)
                ind += 1
                continue
            while c == '{' and ind < len(format_str):
                new_str.append(c)
                if prev_char == '{':
                    prev_char = ''
                    within_field = False
                else:
                    prev_char = c
                    within_field = True
                ind += 1
                c = format_str[ind]
            if within_field:
                new_arg = []
                while ind < len(format_str):
                    if c in '}!:':
                        prev_char = c
                        within_field = False
                        new_args.append(''.join(new_arg))
                        break
                    new_arg.append(c)
                    ind += 1
                    c = format_str[ind]
        format_str = ''.join(new_str)
        args = new_args
    def _format_context(context):
        new_args = []
        for arg in args:
            new_args.append(lena.context.get_recursively(context, arg))
        new_kwargs = {}
        for key in kwargs:
            new_kwargs[key] = lena.context.get_recursively(context, kwargs[key])
        try:
            s = format_str.format(*new_args, **new_kwargs)
        except KeyError:
            raise lena.core.LenaKeyError(
                "keyword arguments of {} not found in kwargs {}".format(
                    format_str, new_kwargs
                )
            )
        else:
            return s
    return _format_context


class MakeFilename(object):
    """Make file names for data from the flow."""

    def __init__(self, *args, **kwargs):
        """:class:`MakeFilename` can be initialized
        using a single string, a Sequence or from keyword arguments.

        A single string is a file name without extension
        (but it can contain a relative path).

        Otherwise, all positional arguments will make a Sequence.

        By default, values with *context.output* already containing
        *filename* are skipped. This can be changed using a keyword
        argument *overwrite*.

        Other allowed keywords are *make_filename*, *make_dirname*,
        *make_fileext*.
        Their values must be a tuple,
        which will initialize a context formatter,
        or a callable (as returned by format_context).
        The first item of the tuple is format string,
        the rest are positional and keyword arguments taken from context
        during *run* (see :func:`format_context`).
        """
        overwrite = kwargs.pop("overwrite", None)
        self._overwrite = overwrite

        if args and kwargs:
            raise lena.core.LenaTypeError(
                "MakeFilename must be initialized either from args"
                "or kwargs, not both"
            )
        elif not args and not kwargs:
            raise lena.core.LenaTypeError(
                "MakeFilename can't be initialized without "
                "positional or keyword arguments"
            )

        if len(args) == 1 and isinstance(args[0], str):
            self._make_filename = format_context(args[0])
            self._sequence = None
        elif args:
            self._sequence = lena.core.Sequence(*args)
        else:
            self._sequence = None

        if args:
            return

        #### only special kwargs initialized here ####

        allowed_kwargs = ["make_filename", "make_dirname", "make_fileext"]
        # used_kwargs = {}
        for kwarg in allowed_kwargs:
            if kwarg in kwargs:
                arg = kwargs.pop(kwarg)
                arg_error = lena.core.LenaTypeError(
                        "initialization arguments must be a tuple "
                        "(format_str, *args, **kwargs), "
                        "{} provided".format(arg)
                    )
                if callable(arg):
                    setattr(self, "_" + kwarg, arg)
                    continue
                elif not isinstance(arg, tuple):
                    raise arg_error
                try:
                    newarg = format_context(*arg)
                except TypeError:
                    raise arg_error
                else:
                    setattr(self, "_" + kwarg, newarg)

        # make_filename = kwargs.pop("make_filename", None)
        # make_dirname = kwargs.pop("make_dirname", None)
        # make_fileext = kwargs.pop("make_fileext", None)

        if kwargs:
            raise lena.core.LenaTypeError(
                "unknown keyword arguments {}".format(kwargs)
            )

    def run(self, flow):
        """Add output parameters to context from the *flow*.

        If :class:`MakeFilename` works as a Sequence,
        it transforms all *flow*.
        In general it should only add values for
        filename, fileext or dirname in context.output.
        It is recommended that if context
        already contains the field, that is not changed.
        Place more specific formatters first in the sequence.

        If :class:`MakeFilename` was initialized with keyword arguments,
        then only those values are transformed,
        which have no corresponding fields
        (*filename*, *fileext* and *dirname*) in *context.output*
        and for which the current context from *flow* could be formatted
        (contains all necessary keys for the format string).

        Note that Sequence takes values with data, while keyword methods
        take and update only context.
        """
        if self._sequence:
            for val in self._sequence.run(flow):
                yield val
        else:
            for val in flow:
                context = lena.flow.get_context(val)
                modified = False

                for kw in ["filename", "fileext", "dirname"]:
                    context_key = lena.context.str_to_context("output." + kw)
                    if self._overwrite or not lena.context.get_recursively(
                        context, context_key, default=""
                    ):
                        meth = getattr(self, "_make_" + kw, None)
                        if meth:
                            try:
                                res = meth(context)
                            except lena.core.LenaKeyError:
                                continue
                            else:
                                context_key["output"] = {kw: res}
                                lena.context.update_recursively(context,
                                                                context_key)
                                modified = True

                if modified:
                    data = lena.flow.get_data(val)
                    yield (data, context)
                else:
                    yield val
