import collections

import pytest
pytestmark = pytest.mark.root

import ROOT

import lena
from lena.core import Sequence
from lena.flow import Print
from lena.variables import Variable, Combine

from lena.output.write_root_tree import WriteROOTTree

py_root_types = collections.namedtuple("py_root_types", ["python", "root"])

# todo: test for signed/unsigned values with different bitness
test_data = [(x, x+0.5) for x in range(10)]


def test_val_to_type_fields():
    # file won't be written
    root_tree = WriteROOTTree("tree", "file.root")

    # single variable works
    t = Variable("t", lambda v: v)
    val = t((0, {}))
    assert root_tree._val_to_type_fields(val) == \
        [('t', py_root_types(python='l', root='L'))]

    # compound variable should be combined.
    val = t(((0, 0.), {}))
    with pytest.raises(lena.core.LenaValueError):
        root_tree._val_to_type_fields(val)

    # Combine works
    x = Variable("x", lambda v: v[0])
    y = Variable("y", lambda v: v[1])
    xy = Combine(x, y)
    # both integer and float work
    val = xy((0, 0.))
    assert root_tree._val_to_type_fields(val) == \
        [("x", py_root_types(python='l', root='L')),
         ("y", py_root_types(python='d', root='D'))]

    # warn about different types in data!
    # but in fact it's honest: if your 1st value has precision as int,
    # all others should not be more precise.


def test_run():
    root_tree = WriteROOTTree("tree", "file.root")
    x = Variable("x", lambda v: v[0])
    y = Variable("y", lambda v: v[1])
    xy = Combine(x, y)
    data = test_data
    seq = Sequence(xy, root_tree)
    assert list(seq.run(data)) == [
        ('file.root',
            {
                "output": {
                    'root_file_path': 'file.root',
                    'root_tree_name': 'tree'
                },
                "variable": {
                     'combine': (
                         {'name': 'x'},
                         {'name': 'y'}
                     ),
                     'dim': 2,
                     'name': 'x_y'
                }
            })
    ]
    return "file.root"

# # manually test that tree was written:
# root_file = ROOT.TFile("file.root")
# tree = root_file.Get("tree")
# print(tree)
