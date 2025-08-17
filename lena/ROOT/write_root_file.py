import ROOT
import lena
from lena.core import LenaEnvironmentError, LenaTypeError
from lena.flow import get_data_context
from lena.context import get_recursively

_sentinel = object()


class WriteROOTFile():
    """Write data from flow to a ROOT file."""

    def __init__(self, filename, mode="recreate", title="", compress=_sentinel):
        """*filename* is the name of the ROOT file (possibly with path).

        The *mode* can be one of
        "new", "create", "update" and "recreate".
        *Recreate* (default) means that file
        will be completely overwritten.
        *New/create* creates a new file,
        but refuses to open existing ones.
        *Update* adds data to files if they exist,
        otherwise they are created.
        Note that in such case an updated object can be written
        to the same file several times.

        *compress* is a number from 0 (no compression) to 9 (maximal
        compression level).
        A higher compression level is slower and might use more memory.
        The default compression level
        uses the compile-time default setting.

        If the file could not be opened,
        :exc:`.LenaEnvironmentError` is raised.
        """
        assert mode.lower() in ("new", "create", "update", "recreate")
        if compress is _sentinel:
            compress = ROOT.RCompressionSetting.EDefaults.kUseCompiledDefault
        # note that the default compression in ROOT.TFile constructor
        # can change, but we set it here explicitly.

        try:
            # kwargs are not allowed
            self._file = ROOT.TFile(filename, mode, title, compress)
        # In case of errors the sequence will fail in the very beginning
        except OSError as err:
            raise LenaEnvironmentError(*err.args)
        self._filename = filename

    def run(self, flow):
        """Write data from *flow* to the ROOT file
        and yield *(ROOT file name, context)*.

        *flow* consists of values, which have ROOT objects as data parts
        and context. Context must contain *output.root_key*,
        otherwise the value is skipped (yielded unchanged).
        The value of *context.output.root_key* is used
        as the resulting object key in the ROOT file.

        *context.output* is updated with *filepath*.
        The ROOT file is closed after processing.

        If a data type could not be written,
        :exc:`.LenaTypeError` is raised.
        """
        root_file = self._file
        context = {}

        # Problem: this does not always work.
        # See tests for writing. If fails, write only once.
        if not root_file.IsOpen():
            # using same element in several passes.
            # We decide to reopen instead of not closing opened ones
            # (which would take more memory and lead to more errors
            #  in files).
            root_file.ReOpen("update")
            # raise lena.core.LenaRuntimeError(
            #     "ROOT file {} could not be opened for writing"\
            #     .format(self._filename)
            # )

        for val in flow:
            obj, context = get_data_context(val)
            key = get_recursively(context, "output.root_key", None)
            # ROOT Objects to be written
            # should have a corresponding key in context
            if not key:
                yield val
                continue

            # write object with key to the file
            try:
                root_file.WriteObject(obj, key)
            except TypeError as err:
                print("could not write key {} to file {}"\
                      .format(key, self._filename))
                root_file.Close()
                raise LenaTypeError(*err.args)
            # there could be other errors

            del context["output"]["root_key"]

        lena.context.update_recursively(
            context, "output.filepath", self._filename
        )

        root_file.Close()
        yield (self._filename, context)
