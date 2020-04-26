"""PDF to PNG converter."""
from __future__ import print_function

import sys
import subprocess

import lena.context
import lena.flow


def _run_command(command, verbose=True, timeoutsec=60):
    """Run system shell command via *subprocess* module.

    *command* is a list of strings.
    """
    # *command* can be a string or a list of strings.
    # not used, probably not needed.
    # if isinstance(command, str):
    #     command_name = command
    # else:
    command_name = " ".join(command)
    if verbose:
        print(command_name)
    popen = subprocess.Popen(command)
    # popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkwargs = {}
    if sys.version_info.major > 2:
        pkwargs.update({"timeout": timeoutsec})
    (stdoutdata, stderrdata) = popen.communicate(pkwargs)
    returncode = popen.returncode
    if returncode:
        # todo: rethink about a warning here
        print("stdoutdata: ", stdoutdata)
        print("stderrdata: ", stderrdata)
        print("returncode: ", returncode)


class PDFToPNG(object):
    """Convert PDF to image format (by default PNG)."""

    def __init__(self, format="png", timeoutsec=60):
        """Initialize output *format*.

        *timeoutsec* is time (in seconds) for subprocess timeout
        (used only in Python 3). If the timeout expires,
        the child process will be killed and waited for.
        The :exc:`TimeoutExpired` exception will be re-raised
        after the child process has terminated. 

        This class uses ``pdftoppm`` binary internally.
        ``pdftoppm`` can be given other output formats as an option
        (see ``man pdftoppm``), for example *jpeg* or *tiff*.
        """
        self._format = format
        self._timeoutsec = timeoutsec

    def run(self, flow):
        """Convert PDF files to *format*.

        PDF files are recognized via *context.output.filetype*.
        Their paths are assumed to be data part of the value
        (may contain trailing *".pdf"*).

        Data yielded is the resulting file name.
        Context is updated with *filetype = format*.

        Other values are passed unchanged.
        """
        def is_pdf(context):
            """May be passed as a parameter to the class."""
            filetype = lena.context.get_recursively(context, "output.filetype", None)
            return filetype == "pdf"

        for val in flow:
            data, context = lena.flow.get_data_context(val)
            if is_pdf(context):
                lena.context.update_recursively(context, "output.filetype.png")
                pdf_name = data
                data = pdf_name.replace(".pdf", "")
                # pdftopng adds -00001 suffix, no way to disable that.
                command = ["pdftoppm",
                           pdf_name,
                           data,
                           "-" + self._format,
                           "-singlefile",
                          ]
                _run_command(command, timeoutsec=self._timeoutsec)
                data += "." + self._format
                yield (data, context)
            else:
                yield (data, context)
