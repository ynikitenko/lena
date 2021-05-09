# needs ROOT installed
import collections
import copy
import sys

import lena


class ReadROOTTree():
    """Read ROOT trees from flow."""

    def __init__(self, leaves=None, get_entries=None):
        """Trees can be read in two ways.

        In the first variant, *leaves* is a list of strings
        that enables to read the specified tree leaves.
        Only branches containing the leaves are read.
        To get a leaf from a specific branch, add it to
        the leaf's name with a slash, e.g. *"my_branch/my_leaf"*.
        Tree entries are yielded as named tuples
        with fields named after *leaves*.

        A leaf can contain a branch name prepended

        In the second variant, *get_entries*
        is a function that accepts a ROOT tree
        and yields its entries.

        Exactly one of *leaves* or *get_entries* (not both)
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

        if leaves is not None:
            err_msg = ""
            if not isinstance(leaves, list):
                err_msg = "leaves must be a list of strings"
            if sys.version_info.major == 2:
                if any((not isinstance(br, basestring) for br in leaves)):
                    # ROOT allows unicode names.
                    err_msg = "leaves must be a list of strings"
            else:
                if any((not isinstance(br, str) for br in leaves)):
                    err_msg = "leaves must be a list of strings"
            if err_msg:
                raise lena.core.LenaTypeError(err_msg)
            # todo: maybe allow regexps in the future.
            if any(('*' in br for br in leaves)):
                raise lena.core.LenaValueError(
                    "leaves must be strings without regular expressions"
                )
            if get_entries is not None:
                raise lena.core.LenaTypeError(
                    "either leaves or get_entries should be supplied, "
                    "not both"
                )
        else:
            if get_entries is None:
                raise lena.core.LenaTypeError(
                    "initialize leaves or get_entries"
                )
        # todo: allow empty leaves to signify all leaves.
        # Use TTree:GetListOfBranches()
        # This would be not a particularly good design,
        # because it's suboptimal to read all data instead of needed,
        # but that would decouple data from code.

        if get_entries is not None and not callable(get_entries):
            raise lena.core.LenaTypeError("get_entries must be callable")

        self._leaves = leaves
        self._get_entries = get_entries

    def _read_leaves(self, tree):
        all_leaves = self._leaves
        # disable all branches
        tree.SetBranchStatus("*", 0)

        leaves_with_branches = []
        # leaves without branch names in them
        leaves = []
        for leaf in all_leaves:
            if '/' in leaf:
                leaves_with_branches.append(leaf)
            else:
                leaves.append(leaf)
        tree_branches = set(br.GetName() for br in tree.GetListOfBranches())
        allowed_branches = set()
        leaves_with_branches_names = []
        for leaf in leaves_with_branches:
            # "branch_name/leaf_name"
            br, leaf_name = leaf.split('/')
            if br not in tree_branches:
                raise lena.core.LenaRuntimeError(
                    "branch {} for leaf {} not found in tree {}"
                    .format(br, leaf, tree.GetName())
                )
            allowed_branches.add(br)
            leaves_with_branches_names.append(leaf_name)

        ## find branches for our leaves
        all_branches = tree.GetListOfBranches()
        # branches that correspond to our leaves
        leaves_branches = {leaf: [] for leaf in leaves}
        for br in all_branches:
            # branch title always contains leaflist,
            # see TBranch constructors and TTree::Branch methods.
            br_leaflist = br.GetTitle()
            br_leaves = []
            for leaf in br_leaflist.split(':'):
                # branch names are parts before possible [...]/
                ind = leaf.find('[')
                if ind != -1:
                    br_leaves.append(leaf[:ind])
                    continue
                ind = leaf.find('/')
                if ind != -1:
                    br_leaves.append(leaf[:ind])
                    continue
                br_leaves.append(leaf)
            for leaf in leaves:
                if leaf in br_leaves:
                    leaves_branches[leaf].append(br.GetName())

        for leaf in leaves:
            nbranches = len(leaves_branches[leaf])
            if not nbranches:
                raise lena.core.LenaRuntimeError(
                    "no branch for leaf {} found in the tree {}"
                    .format(leaf, tree.GetName())
                )
            elif nbranches > 1:
                raise lena.core.LenaRuntimeError(
                    "several branches were found for leaf {} "
                    "in the tree {}: {}"
                    .format(leaf, tree.GetName(), leaves_branches[leaf])
                )
            # exactly one branch found
            allowed_branches.add(leaves_branches[leaf][0])

        # enable allowed branches
        for br in allowed_branches:
            tree.SetBranchStatus(br, 1)

        # join all leave names for simplicity
        leaves_names = leaves[:]
        for leaf in leaves_with_branches:
            leaves_names.append(leaf.replace('/', '_'))
        leaves.extend(leaves_with_branches_names)

        # create output type
        tree_name = tree.GetName()
        tup_name = tree_name + "_entry" if tree_name else "tree_entry"
        entry_tuple = collections.namedtuple(tup_name, leaves_names)

        # yield entries
        for entry in tree:
            yield entry_tuple(*(getattr(entry, lf) for lf in leaves))

    def run(self, flow):
        """Read ROOT trees from *flow* and yield their contents.

        *context.input.root_tree_name* is updated with the name
        of the current tree.

        The tree must have one and only one branch corresponding to
        each leaf, otherwise :exc:`.LenaRuntimeError` is raised.
        To read leaves with the same name in several branches,
        specify branch names for them.
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
            if self._leaves:
                for data in self._read_leaves(tree):
                    yield (data, deepcopy(context))
            elif self._get_entries:
                for entry in self._get_entries(tree):
                    yield (entry, deepcopy(context))
