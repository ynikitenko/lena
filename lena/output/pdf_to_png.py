"""PDF to PNG converter."""
from __future__ import print_function

import sys
import subprocess

from lena.context import get_recursively


def _run_command(command, verbose=True, timeoutsec=60):
    """Run system shell command via *subprocess* module.

    *command* can be a string or a list of strings.
    """
    if isinstance(command, str):
        command_name = command
    else:
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
        print("stdoutdata: ", stdoutdata)
        print("stderrdata: ", stderrdata)
        print("returncode: ", returncode)


class PDFToPNG(object):
    """Convert PDF to image format (by default PNG)."""

    def __init__(self, format="png"):
        """Initialize output *format*.

        This class uses pdftoppm binary internally.
        Pdftoppm can be given other output formats as an option (see man pdftoppm),
        for example: png (default), jpeg, tiff.
        """
        self.format = format

    def run(self, flow):
        """Convert pdf files to png.

        pdf files are recognized via context.output.filetype.
        Their paths are assumed to be data part of the value.

        Data yielded is the resulting file name.
        Context is updated with filetype = png.

        Other values are yielded unchanged.
        """
        def is_pdf(context):
            """May be passed as a parameter to the class."""
            filetype = get_recursively(context, "output.filetype", None)
            return filetype == "pdf"

        for data, context in flow:
            if is_pdf(context):
                context.update({"output": {"filetype": "png"}})
                pdf_name = data
                data = pdf_name.replace(".pdf", "")
                # pdftopng adds -00001 suffix, no way to disable that.
                command = ["pdftoppm",
                           pdf_name,
                           data,
                           "-" + self.format,
                           "-singlefile",
                          ]
                _run_command(command)
                data += "." + self.format
                yield (data, context)
            else:
                yield (data, context)
