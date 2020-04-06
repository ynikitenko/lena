"""Convert LaTeX to PDF."""
from __future__ import print_function

import os
import collections 
import subprocess

import lena.core 
import lena.context


class LaTeXToPDF(object):
    """Run pdflatex binary for LaTeX files.

    It runs in parallel (separate process is spawned for each job)
    and non-interactively.
    """
    def __init__(self, verbose=1, create_command=None):
        """Initialize object.

        verbose = 0 means no output messages.
        1 prints pdflatex error messages.
        More than 1 prints pdflatex stdout.

        If you need to run pdflatex (or other executable)
        with different parameters, provide its command.

        *create_command* is a function which accepts
        texfile_name, outfilename, output_directory, context
        (in this order) and returns a list
        made of the command and its arguments.

        Default command is:
            ["pdflatex", "-halt-on-error", "-interaction", "batchmode",
                    "-output-directory", output_directory,
                    texfile_name]
        """
        self.verbose = verbose
        if create_command and not callable(create_command):
            raise lena.core.LenaTypeError(
                "create_command must be callable, "
                "{} provided.".format(create_command)
            )
        self.create_command = create_command
        # OrderedDict was chosen,
        # because it faster to remove elements from that than from a list,
        # and because it is natural to iterate processes in FIFO order
        self.processes = collections.OrderedDict()

    def run(self, flow):
        """Convert all incoming LaTeX files to pdf.
        """
        def is_tex_file(context):
            """May be transformed by this class."""
            filetype = lena.context.get_recursively(
                context, "output.filetype", None
            )
            if filetype == "tex":
                # if not context["output"].get("latex_to_pdf", True):
                return True
            return False

        def pop_returned_processes(processes, verbose=True):
            """Remove returned processes from pool."""
            for filename in list(processes.keys()):
                proc, context = processes[filename]
                returncode = proc.poll()
                if returncode != None:
                    # process terminated
                    # if verbose:
                    #     print(stdoutdata, end='')
                    #     print(stderrdata, end='')
                    if returncode:
                        # an error occurred
                        del processes[filename]
                        continue
                    else:
                        # terminated well
                        del processes[filename]
                        yield (filename, context)

        def launch(texfile_name, outfilename, output_directory, context, pool):
            """Add process to pool."""
            if self.create_command:
                command = self.create_command(texfile_name, outfilename, output_directory, context)
            else:
                command = ["pdflatex", "-halt-on-error", "-interaction", "batchmode",
                           "-output-directory", output_directory,
                           texfile_name]
            command_str = " ".join(command)
            if self.verbose:
                print(command_str)
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            pool[outfilename] = (process, context)

        val = None # if flow is empty
        for val in flow:
            # check for finished pdfs on each iteration
            for out_val in pop_returned_processes(self.processes):
                yield out_val
            if isinstance(val, tuple) and len(val) == 2:
                data, context = lena.flow.get_data_context(val)
                if not is_tex_file(context):
                    yield val
                    continue
                # no deepcopy, because it's a Run element
                context.update({"output": {"filetype": "pdf"}})
                texfile_name = data
                data = texfile_name.replace(".tex", ".pdf")
                output_directory = os.path.dirname(texfile_name)
                launch(texfile_name, data, output_directory, context, self.processes)
            else:
                yield val

        # this data mustn't be reused
        del val

        for filename in list(self.processes.keys()):
            process, context = self.processes[filename]
            val = (filename, context)
            try:
                stdoutdata, stderrdata = process.communicate()
            except KeyboardInterrupt:
                print("Interrupting pdflatex...")
                if self.verbose:
                    print("Could not finish", val)
                    print("Collecting finished pdfs...")
                for val in pop_returned_processes(self.processes,
                                                  verbose=self.verbose):
                    yield val
                # kill not finished processes
                for key in self.processes:
                    process, _ = self.processes[key]
                    process.terminate()
                self.processes.clear()
                raise StopIteration
            else:
                if self.verbose > 1:
                    print("LaTeXToPDF stdout:", stdoutdata, end='')
                if self.verbose:
                    if stderrdata:
                        print("LaTeXToPDF stderror:", stderrdata, end='')
                returncode = process.poll()
                if not returncode:
                    yield val

        self.processes.clear()
