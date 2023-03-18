import lena.core
import lena.context
import lena.flow


class MakeFilename(object):
    """Make file name, file extension and directory name."""
    # We don't treat groups of plots specially, because
    # one would have to create file name for them from the start.

    def __init__(self, filename=None, dirname=None, fileext=None,
                 prefix=None, suffix=None, overwrite=False):
        """*filename* is a string, which will be
        used as a file name without extension
        (but it can contain a relative path).
        The string can contain formatting arguments
        enclosed in double braces.
        These arguments will be filled from context
        during :meth:`__call__`. Example:

            MakeFilename("{{variable.type}}/{{variable.name}}")

        *dirname* and *fileext* set directory name and file extension.
        They are treated similarly to *filename* in most aspects.

        It is possible to "postpone" file name creation, but to provide
        a part of a future file name through *prefix* or *suffix*.
        They will be appended to file name during its creation.
        Existing file names are not affected.
        It is not allowed to use *prefix* or *suffix* if *filename*
        argument is given.

        For example, if one creates logarithmic plots, but complete
        file names will be made later,
        one may use *MakeFilename(suffix="_log")*.

        All these arguments must be strings,
        otherwise :exc:`.LenaTypeError` is raised.
        They may all contain formatting arguments.

        By default, values with *context.output*
        already containing *filename*, *dirname* or *fileext*
        are not updated (pass unaltered).
        This can be changed using a keyword argument *overwrite*.
        For more options, use :class:`.lena.context.UpdateContext`.

        At least one argument must be present,
        or :exc:`.LenaTypeError` will be raised.
        """
        self._overwrite = bool(overwrite)

        args = [filename, dirname, fileext, prefix, suffix]
        args_names = "filename, dirname, fileext, prefix, suffix"

        for arg in args:
            # we don't check Python 2 basestrings from here.
            if arg is not None and not isinstance(arg, str):
                raise lena.core.LenaTypeError(
                    "arguments must be strings, {} "
                    "provided".format(arg)
                )

        if filename is not None:
            if prefix is not None or suffix is not None:
                raise lena.core.LenaTypeError(
                    "filename is incompatible with "
                    "prefix and suffix. Provide them separately"
                )

        # since the ordering of options is not important,
        # methods could be a dict.
        methods = []
        if prefix is not None:
            methods.append(("prefix", lena.context.format_context(prefix)))
        if suffix is not None:
            methods.append(("suffix", lena.context.format_context(suffix)))

        if filename is not None:
            methods.append(("filename", lena.context.format_context(filename)))
        if dirname is not None:
            methods.append(("dirname", lena.context.format_context(dirname)))
        if fileext is not None:
            methods.append(("fileext", lena.context.format_context(fileext)))

        if not methods:
            # for wrong initialization it must be a TypeError,
            # as if it was an obligatory argument.
            raise lena.core.LenaTypeError(
                "MakeFilename must be initialized with at least "
                "one of {}".format(args_names)
            )

        self._methods = methods

    def __call__(self, value):
        """Add *output* keys to the *value*'s context.

        *filename*, *dirname*, *fileext*, if initialized,
        set respectively *context.output.{filename,dirname,fileext}*
        (if they didn't exist).

        If this elements sets file name
        and if context contains *output.prefix* or *output.suffix*,
        they are prepended to or appended after the file name.
        After that they are removed from *context.output*.

        If this element adds a prefix or a suffix
        and they exist in the context,
        then *prefix* is prepended before the existing prefix,
        and *suffix* is appended after the existing suffix,
        unless *overwrite* is set to ``True``:
        in that case they are overwritten.
        *prefix* and *suffix* always update their existing keys
        in the context if they could be formatted
        (which is different for attributes like *filename*).

        If current context can't be formatted
        (doesn't contain all necessary keys for the format string),
        a key is not updated.
        """
        context = lena.flow.get_context(value)
        modified = False

        for key, meth in self._methods:
            if key in ["filename", "fileext", "dirname"]:
                if "output" in context and key in context["output"]:
                    if not self._overwrite:
                        continue
            try:
                res = meth(context)
            except lena.core.LenaKeyError:
                continue
            else:
                if key in ["prefix", "suffix"]:
                    existing = lena.context.get_recursively(
                        context, "output." + key, None
                    )
                    if existing and not self._overwrite:
                        # prefix is prepended to existing,
                        # suffix is appended after existing
                        if key == "prefix":
                            res = res + existing
                        else:
                            res = existing + res
                elif key == "filename":
                    # append existing prefixes and suffixes to filename
                    prefix = lena.context.get_recursively(
                        context, "output.prefix", ""
                    )
                    suffix = lena.context.get_recursively(
                        context, "output.suffix", ""
                    )
                    res = prefix + res + suffix
                    # todo: do I need an option *remove_used*?
                    # I think not. This deletion is natural,
                    # used parts are conserved in created filename.
                    # If filename was not created,
                    # they remain in the context.
                    if prefix:
                        del context["output"]["prefix"]
                    if suffix:
                        del context["output"]["suffix"]
                update = {"output": {key: res}}
                lena.context.update_recursively(context, update)
                modified = True

        # todo: probably write somewhere how good it was and delete.
        # just get_data_context in the beginning
        # and don't check for modifications.
        if modified:
            # or created
            data = lena.flow.get_data(value)
            return (data, context)
        else:
            return value
