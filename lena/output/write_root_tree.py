# needs ROOT installed
import array
import collections
import copy
import sys

import lena


class WriteROOTTree():
    """Write data to a ROOT tree."""

    def __init__(self, name, root_file):
        """*name* is the name of the tree.

        Only tuples produced by lena :ref:`module_variables`
        or namedtuples can be written to tree.
        They can contain only int and float Python types.
        For more general options, use a ROOT tree directly.

        *root_file* is the ROOT file where the tree will be written.
        It can be an actual ROOT.TFile
        or a tuple of initialization options,
        e.g. ("myfile.root", "recreate"), or a string.
        In the latter case it is the name
        (equivalent to its path) of a ROOT file (rewritten every time).

        Option to open a file for writing can be one of
        "new", "create", "update" and "recreate".
        *New/create* refuses to open existing files.
        *Update* adds data to files if they exist.
        Note that in such case an updated object can be written
        to the same file several times.
        *Recreate* (default) means that file
        will be completely overwritten.

        Note
        ----
            To use this class, `ROOT <https://root.cern/>`__ must be installed.
        """
        import ROOT
        # todo: name -> tree, so that a tree could be passed?
        # First check that data will be
        # appended to that, not overwritten.

        # better move this to a separate topic about ROOT.
        # TFile::TFile(
        #     const char* fname, const char* option = "",
        #     const char* ftitle = "", int compress = \
        #     ROOT::RCompressionSetting::EDefaults::kUseCompiledDefault
        # )
        # where the default option is "read".
        # File can be a remote, a part of an archive, or not a root file.

        self._file_opened_here = True
        if isinstance(root_file, ROOT.TFile):
            self._root_file_name = root_file.GetName()
            self._file_opened_here = False
        elif isinstance(root_file, tuple):
            if not root_file:
                raise lena.core.LenaValueError(
                    "root_file must be non-empty tuple"
                )
            # could check here, but the error would be obvious
            self._root_file_name = str(root_file[0])
            if len(root_file) >= 2:
                create_option = root_file[1]
                file_options = ["new", "create", "recreate", "update"]
                if lower(create_option) not in file_options:
                    raise lena.core.LenaValueError(
                        "creation option must be one of {}, {} provided"\
                        .format(file_options, create_option)
                    )
        elif isinstance(root_file, str):
            self._root_file_name = root_file
        elif sys.version[0] == 2 and isinstance(root_file, unicode):
            self._root_file_name = root_file
        else:
            raise lena.core.LenaValueError(
                "root_file should be one of {}"\
                .format((ROOT.TFile, str, tuple))
            )

        if not self._root_file_name:
            # ROOT file will output (not raise!)
            # an error if TFile's name is empty.
            raise lena.core.LenaValueError(
                "ROOT file name must be non-empty"
            )

        self._data_c = {
            # redundant, "root_file_name": root_file_name,
            # don't know when name is not equal to path
            "root_file_path": self._root_file_name,
            "root_tree_name": name,
        }

        self._root_file = root_file
        self._name = name

    # created as a separate method for easier testing
    def _val_to_type_fields(self, val):
        py_root_tuple = collections.namedtuple("py_root_types", ["python", "root"])
        data, context = lena.flow.get_data_context(val)

        def type_to_chars(obj):
            # don't use isinstance, because
            # a complicated daughter class could be written incorrectly.
            typ = type(obj)
            typ_to_char = {
                # in ROOT L is 64 bits, in Python l is > 32 bits.
                int:   py_root_tuple('l', 'L'),
                float: py_root_tuple('d', 'D')
            }
            # there is no switch in Python, see
            # PEP 275 https://www.python.org/dev/peps/pep-0275
            # or https://docs.python.org/3/faq/design.html#why-isn-t-there-a-switch-or-case-statement-in-python
            #
            # there is no character type in Python 3 array!
            # And unicode character is deprecated,
            # https://docs.python.org/3/library/array.html#module-array
            # https://docs.python.org/2.7/library/array.html#module-array
            # signed long (4 bytes) and double, 8 bytes
            # when and if we abandon Python 2, we might use
            # 'q', signed long long (8 bytes)

            try:
                return typ_to_char[typ]
            except KeyError:
                raise lena.core.LenaTypeError(
                    "unknown value type, can't create an array with {}"\
                    .format(obj)
                )

        if hasattr(data, "__iter__"):
            # we check iter instead of type
            # for uniformity with enumerate_data.
            # if isinstance(data, tuple):
            # named tuples are subtypes of tuples.

            # fill names
            if hasattr(data, '_fields'):
                # namedtuple gets names from its fields.
                names = data._fields
            else:
                # tuple gets names from context.variable.combine.
                names = []
                for ind, dt in enumerate(data):
                    try:
                        # todo docs: can it be got recursively using a list?
                        combine = lena.context.get_recursively(context,
                                                               "variable.combine")
                        name = combine[ind]["name"]
                    except KeyError:
                        raise lena.core.LenaValueError(
                            "context.variable.combine[{}].name not found"\
                            .format(ind)
                        )
                    if not name:
                        raise lena.core.LenaValueError(
                            "context.variable.combine[{}].name must non-empty"\
                            .format(ind)
                        )
                    names.append(name)

            results = []
            for ind, dt in enumerate(data):
                type_ = type_to_chars(dt)
                results.append((names[ind], type_))
            return results
        else:
            # single value gets its name from variable.name
            name = lena.context.get_recursively(context, "variable.name", None)
            if not name:
                raise lena.core.LenaValueError(
                    "Non-empty context.variable.name must be provided"
                )
            return [(name, type_to_chars(data))]

    def _fill_tree(self, root_file, flow):
        """Fill the tree from *flow* and return (tree, context)."""
        import ROOT
        # TTree(const char *name, const char *title,
		#       Int_t splitlevel=99, TDirectory *dir=gDirectory)
        # See no reason for its separate title
        tree = ROOT.TTree(self._name, self._name)
        # we add it to a file in case
        # if it grows large and needs to write to file
        tree.SetDirectory(root_file)

        try:
            val = next(flow)
        except StopIteration:
            # Empty flow results in an empty tree.
            # Unfortunately it has no branches.
            # todo: probably add an init option raise_on_empty?
            return (tree, {})

        data, context = lena.flow.get_data_context(val)
        py_root_chars = self._val_to_type_fields(val)

        def enumerate_data(data):
            # all iterables are complex types
            # and should be written split.
            # though in fact only tuples and named tuples are allowed.
            if not hasattr(data, '__iter__'):
                yield (0, data)
            else:
                for item in enumerate(data):
                    yield item

        arrays = []
        for ind, dat in enumerate_data(data):
            name, (arr_type, branch_type) = py_root_chars[ind]
            arrays.append(array.array(arr_type, [0]))
            arrays[ind][0] = data[ind]
            # Example: tree.Branch("x", x, "x/F")
            tree.Branch(name, arrays[ind], "{}/{}".format(name, branch_type))
            # https://root.cern/doc/master/classTTree.html
        # fill with the 0th value
        tree.Fill()

        for val in flow:
            data, context = lena.flow.get_data_context(val)
            # fill arrays
            for ind, dat in enumerate_data(data):
                arrays[ind][0] = dat
            # fill the tree
            tree.Fill()

        return (tree, context)

    def run(self, flow):
        """Fill the tree from *flow*
        and yield *(ROOT file name, context)*.

        Tree branches are set from the first value in *flow*.
        If the *data* part of the value
        is a namedtuple, branch names are its fields names.
        Otherwise it is assumed that the value was produced by
        Lena variables, and names are searched in *context.variable*
        (*name* for a single variable and *combine* for
        :class:`.Combine`).
        If a wrong data type was encountered (not int or float)
        in the first value, :exc:`.LenaTypeError` is raised.
        If name could not be determined from *context*,
        :exc:`.LenaValueError` is raised.
        Note that for correct results the *flow* must be uniform,
        that is names and types of all values must be the same.

        If the *flow* is empty, an empty tree is written.

        If the ROOT file was opened in this element,
        it is closed after filling the tree
        (even if errors occured during flow generation).
        If an opened ROOT file was provided during the initialization,
        it is the user's responsibility to close that.

        *Context.output* is updated with *root_file_path*
        and *root_tree_name*.
        """
        # otherwise the function won't know its name
        import ROOT
        # open ROOT file before further (possibly large) processing.
        # We open it now, not in init, because in case of errors
        # it's more important to help those users who encounter an error
        # in other elements than those who initialize a TFile wrongly.
        if isinstance(self._root_file, ROOT.TFile):
            root_file = self._root_file
        elif isinstance(self._root_file, str):
            root_file = ROOT.TFile(self._root_file, "recreate")
        elif isinstance(self._root_file, tuple):
            root_file = ROOT.TFile(*self._root_file)

        if not root_file.IsOpen():
            raise lena.core.LenaEnvironmentError(
                "could not open ROOT file {} for writing"\
                .format(root_file)
            )

        # _root_file is private, because write-opened file
        # should be better properly closed than used further.

        try:
            tree, context = self._fill_tree(root_file, flow)
            # todo: try TBufferJSON to write Python's dict context
            # to TFile. However, if the file contained several objects,
            # what their context would be?
            # Store context in separate files produced from Python
            # or use a Cache for that.
            root_file.WriteTObject(tree)
        finally:
            #  If an exception occurs in any of the clauses
            # and is not handled, the exception is temporarily saved.
            # The finally clause is executed.
            # If there is a saved exception, it is re-raised
            # at the end of the finally clause.
            # If the finally clause raises another exception
            # or executes a return or break statement,
            # the saved exception is discarded.
            # https://docs.python.org/3/reference/compound_stmts.html#the-try-statement
            # executed whether there was or wasn't any exception
            if self._file_opened_here:
                root_file.Close()

        lena.context.update_recursively(
            context, {"output": copy.deepcopy(self._data_c)}
        )

        yield (self._root_file_name, context)
