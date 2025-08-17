import pytest
pytestmark = pytest.mark.root

import ROOT

import lena
from lena.core import LenaKeyError, LenaTypeError
from lena.ROOT import ReadROOTFile


def test_read_root_file(rootfile):
    data = [rootfile]
    res_context = {
        "input": {
            "root_file_key": "tree",
            "root_file_path": rootfile,
        }
    }

    # reading all keys works
    read_file = ReadROOTFile()
    # one must explicitly cycle through the flow.
    # Saving results into a list won't help!
    for ind, val in enumerate(read_file.run(data)):
        dt, context = val
        assert dt.GetName() == "tree"
        assert context == res_context
    # in this list objects from file will be None!
    # data = list(read_file())
    assert ind == 0
    del ind

    # reading specified keys works
    read_file_keys = ReadROOTFile("tree", raise_on_missing=False)
    # explicitly cycle.
    for ind, val in enumerate(read_file_keys.run(data)):
        dt, context = val
        assert dt.GetName() == "tree"
        assert context == res_context
    assert ind == 0
    del ind

    # several keys work. A missing key is not yielded.
    read_file_keys = ReadROOTFile(("tree", "missing"), raise_on_missing=False)
    # explicitly cycle.
    for ind, val in enumerate(read_file_keys.run(data)):
        dt, context = val
        assert dt.GetName() == "tree"
        assert context == res_context
    # only one value was read.
    # "missing" was not yielded as a null value.
    assert ind == 0

    # a missing key raises if needed
    read_file_missing_keys = ReadROOTFile("missing", raise_on_missing=True)
    with pytest.raises(LenaKeyError):
        list(read_file_missing_keys.run(data))

    # not an iterable key raises
    with pytest.raises(LenaTypeError):
        ReadROOTFile(0)

    # not string keys raise
    with pytest.raises(LenaTypeError):
        ReadROOTFile((0,))
