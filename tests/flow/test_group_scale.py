import copy
import pytest

from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy, GroupScale, scale_to, Selector
from lena.structures import histogram, graph


def test_group_scale():
    h0 = histogram([0, 1], [0])
    h1 = histogram([0, 1], [1])
    h2 = histogram([0, 2], [2])
    gr = graph([[0, 1], [1, 2]])
    data = [h0, h1, h2, gr]
    data0 = copy.deepcopy(data)

    # too many items selected
    gs = GroupScale(lambda _: True)
    with pytest.raises(LenaValueError):
        gs(data)

    # no items selected
    gs = GroupScale(lambda _: False)
    with pytest.raises(LenaValueError):
        gs(data)

    # graph without a scale can't be rescaled
    h2sel = Selector(lambda h: h.edges[1] == 2, raise_on_error=False)
    gs = GroupScale(h2sel)
    with pytest.raises(LenaValueError):
        gs(data)

    # histogram h0 with a zero scale can't be rescaled
    gs = GroupScale(h2sel, allow_unknown_scale=True)
    with pytest.raises(LenaValueError):
        gs(data[:3])

    # values without a scale method can't be rescaled
    gs = GroupScale(h2sel)
    data1 = [h1, h2, 1]
    with pytest.raises(LenaValueError):
        gs(data1)

    # finally, GroupScale works
    # h2 scale is 4, so they should be equal.
    gs = GroupScale(h2sel, allow_zero_scale=True, allow_unknown_scale=True)
    gsnum = GroupScale(4, allow_zero_scale=True, allow_unknown_scale=True)
    data1 = copy.deepcopy(data)
    data2 = copy.deepcopy(data)
    data1 = gs(data1)
    data2 = gsnum(data2)
    assert data1 == data2

    # note that no context is added when we modify data in place!
    get_scale = lambda val: val.get_scale()
    assert list(map(get_scale, data1)) == [0, 4, 4, None]

    # a single value instead of a group raises
    with pytest.raises(LenaValueError):
        gs(1)
