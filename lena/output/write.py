"""Write data to filesystem."""
import os
import sys
import warnings

import lena.context
import lena.core
import lena.flow


def Writer(*args, **kwargs):
    """
    .. deprecated:: 0.4
       use :class:`Write`.
    """
    warnings.warn("Writer is deprecated since Lena 0.4. Use Write. In:",
                  DeprecationWarning, stacklevel=2)
    return Write(*args, **kwargs)


class Write(object):
    """Write text data to filesystem."""

    def __init__(self, output_directory="", output_filename="output",
                 verbose=True,
                 existing_unchanged=False, overwrite=False):
        """*output_directory* is the base output directory.
        It can be further appended by the incoming data.
        Non-existing directories are created.

        *output_filename* is the name for unnamed data.
        Use it to write only one file.

        If no arguments are given, the default is
        to write to "output.txt" in the current directory
        (rewritten for every new value)
        (unless different extensions are provided through the context).
        It is recommended to create filename explicitly using
        :class:`.MakeFilename`.
        The default writer's output file is useful in case of errors,
        when explicit file name didn't work.

        *verbose* sets whether additional information
        should be printed on the screen.
        *verbose* set to ``False`` disables runtime messages.

        *existing_unchanged* and *overwrite* are used during :meth:`run`
        to change the handling of existing files.
        They are mutually exclusive:
        simultaneous use raises :exc:`.LenaValueError`.
        """
        self.output_directory = output_directory
        self._output_filename = output_filename
        if (not isinstance(output_directory, str)
            or not isinstance(output_filename, str)):
            raise lena.core.LenaTypeError(
                "output_directory and output_filename must be strings, "
                "{} and {} given".format(output_directory, output_filename)
            )

        # verbose is boolean, because for more detailed information
        # one can use a Print element.
        self._verbose = verbose

        if existing_unchanged and overwrite:
            raise lena.core.LenaValueError(
                "existing_unchanged and overwrite are mutually exclusive"
            )
        self._existing_unchanged = existing_unchanged
        self._overwrite = overwrite

    def _make_filename(self, outputc):
        dirname = outputc.get("dirname", "")
        # dirname is always relative to self.output_directory
        # get file extension
        if "filetype" in outputc and "fileext" not in outputc:
            fileext = outputc["filetype"]
        else:
            fileext = outputc.get("fileext", "txt")
        if "filename" in outputc:
            # get file name
            filename = outputc["filename"]
            if not filename:
                raise lena.core.LenaRuntimeError(
                    "empty filename in context.output"
                )
        else:
            filename = self._output_filename
            # if filename is None:
            #     raise (,)

        # filepath is created
        if fileext:
            filepath = filename + "." + fileext
        else:
            filepath = filename
        def normalize_path(path_name, path):
            if os.path.isabs(path):
                warnings.warn(
                    "{} should not be an absolute path, {} given"
                    .format(path_name, path),
                    RuntimeWarning
                )
                if path.startswith(os.sep):
                    # there can be also os.altsep for some fancy systems
                    path = path[len(os.sep):]
                    assert not os.path.isabs(path)
            return path
        dirname = normalize_path("dirname", dirname)
        filepath = normalize_path("filename", filepath)
        filepath = os.path.join(self.output_directory, dirname, filepath)

        return (dirname, filename, fileext, filepath)

    def run(self, flow):
        """Only strings (and unicode in Python 2) and objects with a
        method *write* are written. Method *write* must accept a string
        with output file path as an argument.
        To be written, *context["output"]["write"]* must not be
        set to ``False``. Not written values pass unchanged.

        Full name of the file to be written (*filepath*)
        has the form *self.output_directory/dirname/filename.fileext*,
        where *dirname*, *filename* and file extension *fileext*
        are searched in *context["output"]*.
        If *filename* is missing, Write's default filename is used.
        If *fileext* is missing, then *filetype* is used; if it is
        also absent, the default file extension is "txt".
        It is usually enough to provide *fileext*.

        If the resulting file exists
        and its content is the same as the incoming data,
        file is not overwritten (unless it was produced
        with an object's method *write*, which doesn't allow
        to learn whether the file has changed).
        If *existing_unchanged* is ``True``, existing file contents are
        not checked (they are assumed to be not changed).
        If *overwrite* is ``True``, file contents are not checked,
        and all data is assumed to be changed.
        If a file was written, then *output.changed* is set to ``True``,
        otherwise, if it was not set before, it is set to ``False``.
        If in that case *output.changed* existed,
        it retains its previous value.

        Example: suppose you have a sequence
        *(Histogram, ToCSV, Write, RenderLaTeX, Write, LaTeXToPDF)*.
        If both histogram representation and LaTeX template
        exist and are unchanged,
        the second *Write* signals *context.output.changed=False*,
        and LaTeXToPDF doesn't regenerate the plot.
        If LaTeX template was unchanged, but the previous context
        from the first *Write* signals *context.output.changed=True*,
        then in the second *Write* template is not rewritten,
        but *context.output.changed* remains ``True``.
        On the second run, even if we check file contents,
        the program will run faster for unchanged files
        even for :class:`Write`,
        because read speed is typically higher than write speed.

        File name with full path is yielded as data.
        *Context.output* is updated with *fileext* and *filename*
        (in case they were not present),
        and *filepath*, where *filename* is its base part
        (without output directory and extension)
        and *filepath* is the complete path.

        If *context.output.filename* is present but empty,
        :exc:`.LenaRuntimeError` is raised.
        """
        def is_writable(data, context):
            # context doesn't forbid writing
            if not lena.context.get_recursively(context, "output.write", True):
                return False
            # data allows writing
            if hasattr(data, "write") and callable(data.write):
                return True
            # check strings
            if not isinstance(data, str):
                if sys.version_info.major == 3:
                    return False
                elif not isinstance(data, basestring):
                # elif not isinstance(data, unicode):
                    return False
            return True

        for val in flow:
            data, context = lena.flow.get_data_context(val)
            if not is_writable(data, context):
                yield val
                continue

            # write output
            if "output" not in context:
                context["output"] = {}
            outputc = context["output"]
            try:
                dirname, filename, fileext, filepath = self._make_filename(outputc)
            except lena.core.LenaRuntimeError:
                raise lena.core.LenaRuntimeError(
                    "could not make output file name from {}".format(val)
                )
            # dirname is not changed, no need to update it
            outputc["filename"] = filename
            outputc["fileext"] = fileext
            outputc["filepath"] = filepath
            # if nothing explicitly stated changes, data is unchanged
            changed = outputc.get("changed", False)

            if hasattr(data, "write") and callable(data.write):
                # todo: allow to check for method has_changed
                # - allow to use write options
                # from context.output.write_args
                # and context.output.write_kwargs
                # - allow existing_unchanged.
                data.write(filepath)
                outputc["changed"] = True
                yield (filepath, context)
                continue

            if os.path.exists(filepath):
                if self._existing_unchanged:
                    outputc["changed"] = changed
                    if self._verbose:
                        print("# file unchanged, Write skips {}"\
                              .format(filepath))
                    yield (filepath, context)
                    continue
                if self._overwrite:
                    self._write_data(filepath, data)
                    outputc["changed"] = True
                    yield (filepath, context)
                    continue

                # write if existing data differs with written
                with open(filepath) as fil:
                    # read has an optional argument
                    # size = maximum size (bytes) to read
                    # negative or omitted means whole content
                    size = -1
                    # security warning: say an adversary creates
                    # a huge file and adds its path to context (!).
                    # Then the program will crash
                    # trying to read that in memory.
                    existing_data = fil.read(size)
                if data != existing_data:
                    self._write_data(filepath, data)
                    outputc["changed"] = True
                else:
                    # False, unless explicitly set to True
                    if self._verbose:
                        print("# file unchanged, Write skips {}"\
                              .format(filepath))
                    outputc["changed"] = changed
            else:
                # create containing directory
                curdir = os.path.dirname(filepath)
                if not os.path.exists(curdir):
                    # race condition is possible if the directory is created
                    # after it was checked for existence. Ignore now.
                    os.makedirs(curdir)
                self._write_data(filepath, data)

            yield (filepath, context)

    def _write_data(self, filepath, data):
        # write output to filesystem
        # todo: allow binary files
        with open(filepath, "w") as fil:
            fil.write(data)
            # we write only strings, so no TypeError is expected.
            # If one occurs, the user will note that.
            # except TypeError:
            #     raise lena.core.LenaTypeError(
            #         "can't write data {} to file {}"
            #         .format(data, filepath)
            #     )
