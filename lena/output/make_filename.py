from __future__ import print_function

import lena.core
import lena.context
import lena.flow


class MakeFilename(object):
    """Make file name, file extension and directory name."""

    def __init__(self, filename=None, dirname=None, fileext=None,
                 overwrite=False):
        """A single argument can be a string, which will be
        used as a file name without extension
        (but it can contain a relative path).
        The string can contain arguments enclosed in double braces.
        These arguments will be filled from context
        during :meth:`__call__`. Example:

            MakeFilename("{{variable.type}}/{{variable.name}}")

        By default, values with *context.output* already containing
        *filename* are not updated (returned unchanged).
        This can be changed using a keyword argument *overwrite*.
        If context doesn't contain all necessary keys for formatting,
        it will not be updated.
        For more options, use :class:`.lena.context.UpdateContext`.

        Other allowed keywords are *filename*, *dirname*,
        *fileext*. Their value must be a string,
        otherwise :exc:`.LenaTypeError` is raised.
        At least one of the must be present,
        or :exc:`.LenaTypeError` will be raised.
        If a simple check finds unbalanced
        or single braces instead of double,
        :exc:`.LenaValueError` is raised.
        """
        self._overwrite = bool(overwrite)

        args_supplied = (
            filename is not None or dirname is not None
            or fileext is not None)
        if not args_supplied:
            # for wrong initialization there must be a TypeError,
            # not a ValueError. As if it was an obligatory argument.
            raise lena.core.LenaTypeError(
                "MakeFilename must be initialized with at least "
                "one of filename, dirname, fileext"
            )

        self._filename = None
        self._dirname = None
        self._fileext = None

        # todo: rename to filename etc?
        arg_error = "{} must be a string, {} provided"
        if filename is not None:
            if not isinstance(filename, str):
                raise lena.core.LenaTypeError(
                    arg_error.format("filename", filename)
                )
            self._filename = lena.context.format_context(filename)
        if dirname is not None:
            if not isinstance(dirname, str):
                raise lena.core.LenaTypeError(
                    arg_error.format("dirname", dirname)
                )
            self._dirname = lena.context.format_context(dirname)
        if fileext is not None:
            if not isinstance(fileext, str):
                raise lena.core.LenaTypeError(
                    arg_error.format("fileext", fileext)
                )
            self._fileext = lena.context.format_context(fileext)

    def __call__(self, value):
        """Add *output* keys to the *value*'s context.

        *filename*, *dirname*, *fileext*, if initialized,
        set respectively *context.output.{filename,dirname,fileext}*.
        Only those values are transformed
        that have no corresponding keys
        (*filename*, *fileext* or *dirname*) in *context.output*
        and for which the current context can be formatted
        (contains all necessary keys for any of the format strings).
        """
        context = lena.flow.get_context(value)
        modified = False

        for key in ["filename", "fileext", "dirname"]:
            if "output" in context and key in context["output"]:
                if not self._overwrite:
                    continue
            meth = getattr(self, "_" + key, None)
            if meth is not None:
                try:
                    res = meth(context)
                except lena.core.LenaKeyError:
                    continue
                else:
                    update = {"output": {key: res}}
                    lena.context.update_recursively(context, update)
                    modified = True

        if modified:
            # or created
            data = lena.flow.get_data(value)
            return (data, context)
        else:
            return value
