# needs ROOT installed
import copy
import inspect
import sys

import lena
from lena.core import LenaKeyError, LenaTypeError


class ReadROOTFile():
    """Read ROOT files from flow."""

    def __init__(self, keys=None, raise_on_missing=False):
        """*keys* specify which objects should be read from ROOT files.
        They can be a list of allowed objects' names or a single name.
        By default, all keys are read. ROOT files can store several
        versions of the key (cycles). Only the last cycle is yielded.
        Regular expressions are not supported.

        If an explicitly given key was not found, a :exc:`.LenaKeyError`
        is raised if *raise_on_missing* is ``True``.
        By default missing keys are ignored.
        """
        import ROOT

        if keys is not None:
            if isinstance(keys, str):
                keys = [keys]

            key_error = LenaTypeError(
                "keys must contain only strings"
            )
            if not hasattr(keys, "__iter__"):
                raise LenaTypeError("keys must be iterable")

            if sys.version_info.major >= 3:
                if any((not isinstance(key, str) for key in keys)):
                    raise key_error
            else:
                # ROOT keys can have unicode names
                if any((not isinstance(key, basestring) for key in keys)):
                    raise key_error

        self._keys = keys
        self._raise_on_missing = raise_on_missing
        # maybe todo: allow regular expressions,
        # allow ROOT object versions.
        # ROOT files can store several keys with the same name
        # but different cycles, see TDirectoryFile::GetKey at
        # https://root.cern.ch/doc/master/classTDirectoryFile.html#a38ec87c7afc0158ec9da694db3f7a6e6

    def run(self, flow):
        """Read ROOT files from *flow* and yield their contained objects
        corresponding to the initialization keys.
        data parts of values from *flow* must be paths to ROOT files.
        After reading the files are closed.

        *context.input.root_file_path* is updated
        with the path to the ROOT file.
        *input.root_file_key* is updated with the key
        of the yielded object.

        Warning
        =======
            After a ROOT file is closed,
            all its contained objects are destroyed.
            Make all processing within one flow:
            don't save yielded values to a list,
            or save copies of them.
        """
        import ROOT
        from ROOT import TFile
        from lena.context import get_recursively, update_recursively
        from lena.flow import get_data_context
        from copy import deepcopy

        for val in flow:
            data, context = get_data_context(val)

            # can raise an OSError
            root_file = TFile(data, "read")
            # This could be done before this element,
            # but update it here for better default tracking.
            # todo: should it be simply filepath for uniformity?
            # However, we don't have other readers at the moment.
            update_recursively(
                context, {"input": {"root_file_path": data}}
            )

            def get_key_names(fil):
                return [key.GetName() for key in fil.GetListOfKeys()]

            if self._keys is None:
                # read all keys by default
                keys = get_key_names(root_file)
            else:
                keys = self._keys

            for key in keys:
                # Result of TFile.Get is a proper type.
                # Get() returns the last cycle of the key.
                obj = root_file.Get(key)
                # does not work in PyROOT.
                # if obj == ROOT.nullptr:
                if ROOT.addressof(obj) == 0:
                    if self._raise_on_missing:
                        raise LenaKeyError(
                            "key {} not found in {}".format(key, data)
                        )
                    continue

                new_context = deepcopy(context)
                update_recursively(
                    new_context, {"input": {"root_file_key": key}}
                )
                yield (obj, new_context)

            root_file.Close()
