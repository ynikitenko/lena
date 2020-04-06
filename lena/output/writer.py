"""Write data to filesystem."""
from __future__ import print_function

import os
import sys

import lena.core
import lena.flow


class Writer(object):
    """Write text data to filesystem."""

    def __init__(self, output_directory="", output_filename="output"):
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
        :class:`~lena.output.MakeFilename`.
        The default writer's output file can be useful in case of errors,
        when explicit file name didn't work.
        """
        self.output_directory = output_directory
        self._output_filename = output_filename
        if (not isinstance(output_directory, str)
            or not isinstance(output_filename, str)):
            raise lena.core.LenaTypeError(
                "output_directory and output_filename must be strings, "
                "{} and {} given".format(output_directory, output_filename)
            )

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
        filepath = os.path.join(self.output_directory, dirname, filepath)

        return (dirname, filename, fileext, filepath)

    def run(self, flow):
        """Write incoming data to file system.

        Only strings (and unicode in Python 2) are written.
        To be written, data must have "output" dictionary in context
        and *context["output"]["writer"]* not set to ``False``.
        Other values pass unchanged.

        Full name of the file to be written (*filepath*)
        has the form self.output_directory/dirname/filename.fileext,
        where dirname, filename and file extension
        are searched in *context["output"]*.
        If *filename* is missing, Writer's default filename is used.
        If *fileext* is missing, then *filetype* is used; if it is
        also absent, the default file extension is "txt".
        It is recommended to provide only *fileext* in context,
        unless it differs with *filetype*.

        File name with full path is yielded as data.
        Context.output is updated with *fileext* and *filename*
        (in case they were not present),
        and *filepath*, where *filename* is its base part
        (without output directory and extension)
        and *filepath* is the complete path.

        If context.output.filename is present, but empty,
        :exc:`~lena.core.LenaRuntimeError` is raised.
        """
        def should_be_written(data, context):
            if ("output" not in context
                or not isinstance(context["output"], dict)
                or not context["output"].get("writer", True)
               ):
                return False
            if not isinstance(data, str):
                if sys.version_info.major == 3:
                    return False
                elif not isinstance(data, basestring):
                # elif not isinstance(data, unicode):
                    return False
            return True
        for val in flow:
            data, context = lena.flow.get_data_context(val)
            if not should_be_written(data, context):
                yield val
                continue

            # write output
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

            curdir = os.path.dirname(filepath)
            if not os.path.exists(curdir):
                # race condition is possible if the directory is created
                # after it was checked for existence. Ignore now.
                os.makedirs(curdir)

            # write output to filesystem
            # todo: allow binary files
            with open(filepath, "w") as fil:
                try:
                    fil.write(data)
                except TypeError:
                    raise lena.core.LenaTypeError(
                        "can't write data {} to file {}"
                        .format(data, filepath)
                    )

            yield (filepath, context)
