from __future__ import print_function

import re

import lena.core
import lena.context
import lena.flow


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
        during *run* (see :func:`.format_context`).
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
            self._make_filename = lena.context.format_context(args[0])
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
                    newarg = lena.context.format_context(*arg)
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
                    context_key = lena.context.str_to_dict("output." + kw)
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
