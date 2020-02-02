import pytest

from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy, GroupScale
from lena.structures import Histogram, Graph


def test_group_scale():
    h0 = Histogram([0, 1], [0])
    h1 = Histogram([0, 1], [1])
    h2 = Histogram([0, 2], [2])
    g1 = Graph(((0, 1), (1, 2)))
    data = [h0, h1, h2, g1]
    gs = GroupScale(lambda _: True)
    # too many items selected
    with pytest.raises(LenaValueError):
        gs.scale(data)
    gs = GroupScale(lambda _: False)
    # no items selected
    with pytest.raises(LenaValueError):
        gs.scale(data)
    h2sel = lambda h: h.edges[1] == 2
    gs = GroupScale(h2sel)
    # graph without a scale can't be rescaled
    with pytest.raises(LenaValueError):
        gs.scale(data)
    gs = GroupScale(h2sel, allow_unknown_scale=True)
    # histogram h0 with a zero scale can't be rescaled
    with pytest.raises(LenaValueError):
        gs.scale(data)
    # values without a scale method can't be rescaled
    gs = GroupScale(h2sel)
    data1 = [h1, h2, 1]
    with pytest.raises(LenaValueError):
        gs.scale(data1)

    # finally, GroupScale works
    gs = GroupScale(h2sel, allow_zero_scale=True, allow_unknown_scale=True)
    gsnum = GroupScale(4, allow_zero_scale=True, allow_unknown_scale=True)
    scaled = gs.scale(data)
    scaled_to_num = gsnum.scale(data)
    assert scaled == scaled_to_num
    # group scaled adds context, so we need to get rid of that
    scaled = [sc[0] for sc in scaled]
    get_scale = lambda val: val.scale()
    assert list(map(get_scale, scaled[:-1])) == [0, 4, 4]
    # initial data is unchanged
    assert list(map(get_scale, data[:-1])) == [0, 1, 4]
