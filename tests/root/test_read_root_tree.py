import pytest
pytestmark = pytest.mark.root

import ROOT

import lena
from lena.input import ReadROOTTree
from .test_write_root_tree import test_data


def test_read_root_tree(rootfile):
    # branches or get_entry must be provided
    with pytest.raises(lena.core.LenaTypeError):
        read_tree = ReadROOTTree()

    # get tree from file
    fil = ROOT.TFile(rootfile)
    tree = fil.Get("tree")
    data = [tree]

    # ReadROOTTree runs.
    read_tree = ReadROOTTree(branches=["x", "y"])
    tree_data = []
    for val in read_tree.run(data):
        data, context = val
        tree_data.append((data.x, data.y))
        assert context == {
            'data': {
                'root_tree_name': 'tree'
            }
        }
    assert tree_data == test_data
