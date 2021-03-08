import pytest
import ROOT

import lena
from lena.flow.read_root_file import ReadROOTFile


def test_read_root_file():
    read_file = ReadROOTFile()
    data = ["file.root"]
    # todo: lena_sequence.__iter__ should not run
    # if without brackets!
    data_names = ["tree"]
    for ind, val in enumerate(read_file.run(data)):
        data, context = val
        assert data_names[ind] == data.GetName()
        assert context == {
            'data': {
                'root_file_path': 'file.root'
            }
        }
    # in this list objects from file will be None!
    # data = list(read_file())
