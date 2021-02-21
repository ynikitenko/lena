"""PDF to PNG converter."""
from __future__ import print_function

import sys
import subprocess
import os

import lena.context
import lena.flow


def _run_command(command, verbose=True, timeoutsec=60):
    """Run system shell command via *subprocess* module.

    *command* is a list of strings.
    """
    command_name = " ".join(command)
    if verbose:
        print(command_name)
    # todo: if verbose is False, prohibit output
    popen = subprocess.Popen(command)
    # popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkwargs = {}
    if sys.version_info.major > 2:
        pkwargs.update({"timeout": timeoutsec})
    (stdoutdata, stderrdata) = popen.communicate(pkwargs)
    returncode = popen.returncode
    if returncode:
        # todo: think about a warning here
        print("stdoutdata: ", stdoutdata)
        print("stderrdata: ", stderrdata)
        print("returncode: ", returncode)


class PDFToPNG(object):
    """Convert PDF to image format (by default PNG)."""

    def __init__(self, format="png", overwrite=False, verbose=True,
                 timeoutsec=60):
        """Set output *format* (by default *png*).

        If the resulting file already exists and the *pdf* is unchanged
        (which is checked through *context.output.changed*), conversion
        is not repeated.
        To convert all pdfs to images, set *overwrite* to ``True``
        (by default it is ``False``).

        To disable printing messages during :meth:`run`,
        set *verbose* to ``False``.

        *timeoutsec* is time (in seconds) for *subprocess* timeout
        (used only in Python 3). If the timeout expires,
        the child process will be killed and waited for.
        The :exc:`TimeoutExpired` exception will be re-raised
        after the child process has terminated. 

        This element uses ``pdftoppm`` binary internally.
        ``pdftoppm`` can use other output formats,
        for example *jpeg* or *tiff*.
        See ``pdftoppm`` manual for more details.
        """
        self._format = format
        self._timeoutsec = timeoutsec
        self._overwrite = overwrite
        self._verbose = verbose

    def run(self, flow):
        """Convert PDF files to *format*.

        PDF files are recognized via *context.output.filetype*.
        Their paths are assumed to be the data part of the value.

        Data yielded is the resulting file name.
        Context is updated with *output.filetype* set to *format*.

        Other values are passed unchanged.
        """
        def is_pdf(context):
            """May be passed as a parameter to the class."""
            filetype = lena.context.get_recursively(context,
                                                    "output.filetype", "")
            return filetype == "pdf"

        for val in flow:
            data, context = lena.flow.get_data_context(val)
            if is_pdf(context):
                outputc = context["output"]
                outputc["filetype"] = "png"
                pdf_name = data
                data = pdf_name.replace(".pdf", "")
                if not os.path.exists(data + "." + self._format)\
                    or self._overwrite or outputc.get("changed", False):
                    # pdftopng adds -00001 suffix, no way to disable that.
                    command = ["pdftoppm", pdf_name, data,
                               "-" + self._format, "-singlefile"]
                    _run_command(command, verbose=self._verbose,
                                 timeoutsec=self._timeoutsec)
                    outputc["changed"] = True
                else:
                    if self._verbose:
                        print("# file unchanged, PDFToPNG skips {}"\
                              .format(pdf_name))
                    outputc["changed"] = False
                data += "." + self._format
                yield (data, context)
            else:
                yield val
