import pytest

import lena.core
import lena.flow
from lena.flow import seq_map, get_context, get_data, get_data_context


def test_get_data_context():
    val = (0, 1)
    assert get_data(val) == val
    assert get_context(val) == {}
    assert get_data_context(val) == (val, {})
    val = (0, {"a": "b"})
    assert get_data(val) == 0
    assert get_context(val) == val[1]
    assert get_data_context(val) == (0, val[1])


def test_seq_map():
    # works for different containers
    data = set([1, 2, 3])
    s = lena.core.Sequence(lambda x: x+1)
    res = seq_map(s, data)
    assert set(res) == set([2, 3, 4])
    # order is preserved
    data = [1, 2, 3]
    res = seq_map(s, data)
    assert res == [2, 3, 4]
    # one_result is True by default
    res = seq_map(s, data, one_result=True)
    assert res == [2, 3, 4]
    # one_result False works fine
    res = seq_map(s, data, one_result=False)
    assert res == [[2], [3], [4]]
    ### not single results work correctly
    class compl_seq():
        def run(self, flow):
            for val in flow:
                if val == 1:
                    yield val
                else:
                    yield val
                    yield val
    # LenaValueError is raised
    with pytest.raises(lena.core.LenaValueError):
        seq_map(compl_seq(), data)
    # multiple results work fine
    res = seq_map(compl_seq(), data, one_result=False)
    assert res == [[1], [2, 2], [3, 3]]
