import pytest
import ROOT

from lena.core import Sequence, LenaTypeError
from lena.ROOT.write_root_file import WriteROOTFile

ROOTFILE = "test.root"


def test_write_root_file():
    ## not writable data raises
    not_writable = ("string", {"output": {"root_key": "str"}})
    data_nw = [not_writable]
    s = Sequence(
        WriteROOTFile(ROOTFILE, "recreate")
    )
    with pytest.raises(LenaTypeError):
        # "could not write key str to file test.root"
        list(s.run(data_nw))

    ## data without root_key-s passes unchanged
    data_skipped = [("string", {}), "str2"]
    out_val = ('test.root', {'output': {'filepath': 'test.root'}})
    assert list(s.run(data_skipped)) == data_skipped + [out_val]

    ## ROOT values are actually written
    param = ROOT.TParameter('bool')("mybool", False)
    data_written = [(param, {"output": {"root_key": "mykey"}})]
    # Problem: without recreation this does not work.
    # recreate the ROOT file
    s1 = Sequence(
        WriteROOTFile(ROOTFILE, "recreate")
    )
    assert list(s1.run(data_written)) == [out_val]

    # the value has been actually written
    with ROOT.TFile(ROOTFILE, "read") as fil:
        print([key.GetName() for key in fil.GetListOfKeys()])
        val = fil.Get("mykey")
        assert val.GetName() == "mybool"
        assert val.GetVal() is False
