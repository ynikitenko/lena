# needs ROOT installed
import collections
import copy
import sys

import lena


class ReadROOTTree():
    """Read ROOT trees from flow."""

    def __init__(self, branches=None, get_entries=None):
        """Trees can be read in two ways.

        In the first variant, *branches* is a list of strings
        that enables to read the specified tree branches,
        and only them (thus to speed up data reading).
        Tree entries are yielded as named tuples
        with fields named after *branches*.

        In the second variant, *get_entries*
        is a function that accepts a ROOT tree
        and yields its entries.

        Exactly one of *branches* or *get_entries* (not both)
        must be provided, otherwise :exc:`.LenaTypeError` is raised.

        Note
        ====
            To collect the resulting values
            (not use them on the fly), make copies of them
            in *get_entries* (e.g. use *copy.deepcopy*).
            Otherwise all items will be the last value read.
        """
        # This loads other classes faster,
        # and if ROOT is not installed,
        # still enables "from lena.flow import ReadROOTTree",
        # instead of "from lena.flow.read_root_tree import ReadROOTTree"
        import ROOT

        if branches is not None:
            err_msg = ""
            if not isinstance(branches, list):
                err_msg = "branches must be a list of strings"
            if sys.version_info.major == 2:
                if any((not isinstance(br, basestring) for br in branches)):
                    # ROOT allows unicode names.
                    err_msg = "branches must be a list of strings"
            else:
                if any((not isinstance(br, str) for br in branches)):
                    err_msg = "branches must be a list of strings"
            if err_msg:
                raise lena.core.LenaTypeError(err_msg)
            # todo: maybe allow regexps in the future.
            if any(('*' in br for br in branches)):
                raise lena.core.LenaValueError(
                    "branches must be strings without regular expressions"
                )
            if get_entries is not None:
                raise lena.core.LenaTypeError(
                    "either branches or get_entries should be supplied, "
                    "not both"
                )
        else:
            if get_entries is None:
                raise lena.core.LenaTypeError(
                    "initialize branches or get_entries"
                )
        # todo: allow empty branches to signify all branches.
        # Use TTree:GetListOfBranches()
        # This would be not a particularly good design,
        # because it's suboptimal to read all data instead of needed,
        # but that would decouple data from code.

        if get_entries is not None and not callable(get_entries):
            raise lena.core.LenaTypeError("get_entries must be callable")

        self._branches = branches
        self._get_entries = get_entries

    def _read_branches(self, tree):
        branches = self._branches
        # disable all branches
        tree.SetBranchStatus("*", 0)
        # enable allowed branches
        for br in branches:
            tree.SetBranchStatus(br, 1)
        # create output type
        tree_name = tree.GetName()
        tup_name = tree_name + "_entry" if tree_name else "tree_entry"
        entry_tuple = collections.namedtuple(tup_name, branches)
        # yield entries
        for entry in tree:
            yield entry_tuple(*(getattr(entry, br) for br in branches))

    def run(self, flow):
        """Read ROOT trees from *flow* and yield their contents.

        *context.input.root_tree_name* is updated with the name
        of the current tree.
        """
        import ROOT
        get_data_context = lena.flow.get_data_context
        update_recursively = lena.context.update_recursively
        deepcopy = copy.deepcopy

        for val in flow:
            # get tree
            tree, context = get_data_context(val)
            if not isinstance(tree, ROOT.TTree):
                # todo: should not other values be forbidden?
                yield val
                continue

            # add context.data
            input_c = {}
            # if a ROOT file was opened in a Sequence,
            # its path will be already in the context.
            ## a tree can exist outside of a file, in memory.
            # tree_dir = tree.GetDirectory()
            # if tree_dir:
            #     file_name = tree_dir.GetName()
            #     data_c["root_file_path"] = file_name
            input_c["root_tree_name"] = tree.GetName()
            update_recursively(context, {"input": input_c})

            # get entries
            if self._branches:
                for data in self._read_branches(tree):
                    yield (data, deepcopy(context))
            elif self._get_entries:
                for entry in self._get_entries(tree):
                    yield (entry, deepcopy(context))
