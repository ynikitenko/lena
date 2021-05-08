import pytest
pytestmark = pytest.mark.root

import ROOT

import lena
from lena.input import ReadROOTFile


def test_read_root_file(rootfile):
    read_file = ReadROOTFile()
    data = [rootfile]
    # todo: lena_sequence.__iter__ should not run
    # if without brackets!
    data_names = ["tree"]
    for ind, val in enumerate(read_file.run(data)):
        data, context = val
        assert data_names[ind] == data.GetName()
        assert context == {
            "input": {
                "root_file_path": rootfile,
            }
        }
    # in this list objects from file will be None!
    # data = list(read_file())
