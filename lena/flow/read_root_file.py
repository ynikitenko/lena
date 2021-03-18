# needs ROOT installed
import copy
import inspect
import sys

import ROOT

import lena


class ReadROOTFile():
    """Read ROOT files from flow."""

    def __init__(self, types=None, keys=None, selector=None):
        """Keyword arguments specify which objects should be read
        from ROOT files.

        *types* sets the list of possible objects types.

        *keys* specifies a list of allowed objects' names.
        Only simple keys are currently allowed (no regular expressions).

        If both *types* and *keys* are provided, then
        objects that satisfy any of *types* *or* *keys*
        are read.

        *selector* is a general function, which accepts
        an object from a ROOT file and returns a boolean.
        If *selector* is given, both *types* and *keys* must
        be omitted, or :exc:`.LenaValueError` is raised.
        """
        if selector is not None:
            if keys or types:
                raise lena.core.LenaValueError(
                    "if selector is provided, keys and types "
                    "must not be passed"
                )
            if not callable(selector):
                raise lena.core.LenaTypeError(
                    "selector must be callable"
                )
            self._selector = selector
            return

        if keys is not None:
            if not isinstance(keys, list):
                raise lena.core.LenaTypeError(
                    "keys must be a list of strings"
                )
            # ROOT keys can have unicode names
            if (sys.version[0] == 2 and
                any((not isinstance(key, basestring) for key in keys))) or \
               (sys.version[0] > 2 and
                any((not isinstance(key, str) for key in keys))):
                raise lena.core.LenaValueError(
                    "keys must contain only strings"
                )
                # todo: allow regular expressions
                # todo: allow ROOT object versions
                keys_selector = [lambda obj: obj.GetName() == key
                                 for key in keys]

        if types is not None:
            if not isinstance(types, list):
                raise lena.core.LenaTypeError(
                    "types must be a list of types"
                )
            # maybe inspect is needed only for Python 2 types
            # not derived from object. Otherwise use isinstance(_, type)
            if any((not inspect.isclass(tp) for tp in types)):
                raise lena.core.LenaTypeError(
                    "types must must contain only types"
                )
            # in Lena "and" means a list, while "or" means a tuple.
            # In Python isinstance requires a tuple.
            types = tuple(types)
            types_selector = lambda obj: isinstance(obj, types)

        if types is None and keys is None:
            self._selector = None
        elif keys:
            if types:
                self._selector = lena.flow.Selector(
                    [types_selector, keys_selector]
                )
            else:
                self._selector = lena.flow.Selector(keys_selector)

    def run(self, flow):
        """Read ROOT files from *flow* and yield objects they contain.

        For file to be read,
        data part of the value must be a string and
        *context.data.read_root_file* must not be `False`.

        *context.data.root_file_path* is updated
        with the path to the ROOT file.

        Warning
        =======
        After a ROOT file is closed,
        all its contained objects are destroyed.
        Make all processing within one flow:
        don't save yielded values to a list,
        or make proper copies of them in advance.
        """
        for val in flow:
            data, context = lena.flow.get_data_context(val)

            # skip not ROOT files
            if sys.version[0] == 2:
                str_type = basestring
            else:
                str_type = str
            if not isinstance(data, str_type) or not \
                lena.context.get_recursively(context, "data.read_root_file",
                                             True):
                yield val
                continue

            root_file = ROOT.TFile(data, "read")
            # context of separate keys shall be updated
            # when they are transformed to other types
            # in other elements
            lena.context.update_recursively(
                context, {"data": {"root_file_path": data}}
            )

            def get_key_names(fil):
                return [key.GetName() for key in fil.GetListOfKeys()]
            key_names = get_key_names(root_file)

            for key_name in key_names:
                # result of TFile.Get is not a TKey, but a proper type
                obj = root_file.Get(key_name)
                if self._selector:
                    if not self._selector(obj):
                        continue
                yield (obj, copy.deepcopy(context))

            # will be closed after
            # following elements used its data
            root_file.Close()
