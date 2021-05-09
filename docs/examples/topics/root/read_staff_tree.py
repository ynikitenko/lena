import copy
import itertools
import sys

import ROOT
from ROOT import TFile, TTree, gROOT

import lena
from lena.flow import Print
from lena.input import ReadROOTFile, ReadROOTTree
from lena.variables import Variable


def staff_get_entries():
    # create a C++ structure
    gROOT.ProcessLine(
    "struct staff_t {\
       Int_t           Category;\
       UInt_t          Flag;\
       Int_t           Age;\
       Int_t           Service;\
       Int_t           Children;\
       Int_t           Grade;\
       Int_t           Step;\
       Int_t           Hrweek;\
       Int_t           Cost;\
       Char_t          Division[4];\
       Char_t          Nation[3];\
    };")
    # get a staff_t object into Python
    staff = ROOT.staff_t()
    def get_entries(tree):
        # here you can disable some branches to optimise performance
        tree.SetBranchAddress("staff", staff)
        for entry in tree:
            # or copy.copy if there is no deep nesting
            yield copy.deepcopy(staff)
    return get_entries


# imperative approach
f = TFile("staff.root")
staff_tree = f.Get("T")
for staff_m in itertools.islice(staff_tree, 10):
    print(staff_m.Age, end='')
print()

get_entries = staff_get_entries()
for staff_m in itertools.islice(get_entries(staff_tree), 10):
    print(staff_m.Age, ", ", sep="", end="")
print()

# Lena sequence
s1 = lena.core.Sequence(
    ReadROOTFile(),
    ReadROOTTree(get_entries=staff_get_entries()),
    Variable("age", lambda staff: staff.Age),
    # create histograms, do normal Lena processing
    Print(),
    lena.flow.Slice(10),
)

# run the sequence
list(s1.run(["staff.root"]))
# (58, {'input': {'root_file_path': 'staff.root', 'root_tree_name': 'T'}, 'variable': {'name': 'age'}})
# ...

s2 = lena.core.Sequence(
    ReadROOTFile(),
    # several leaves can be read into a named tuple
    ReadROOTTree(["Divisions/Division", "Age"]),
    Print(),
    lena.flow.Slice(10),
)

# run the sequence
list(s2.run(["staff.root"]))
