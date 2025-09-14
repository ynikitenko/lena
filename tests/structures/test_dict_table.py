from copy import deepcopy

import pytest

from lena.core import LenaKeyError
from lena.structures import dict_table, DictTable

d = [
    {"detector": "FDI",  "value": 3},
    {"detector": "FDII", "value": 2},
]
# data includes context
data = deepcopy([
    (d[0], dict(d[0], common="c")),
    (d[1], dict(d[1], common="c")),
])


def test_dict_table():
    tab = dict_table(deepcopy(d))

    # getting a value works
    assert tab["value"] == [3, 2]

    # getting a tuple works
    assert tab[("detector", "value")] == [('FDI', 3), ('FDII', 2)]

    ## selection works
    # selecting one item works
    assert tab["detector.FDI"] == d[0]

    # selecting one value from an item works
    assert tab["detector.FDI"]["value"] == 3

    # no constraint means not selecting, but getting values
    assert tab["detector"] == ['FDI', 'FDII']

    # getting multiple values works
    assert tab.filter_columns("value") == [3, 2]

    # columns can not be filtered on an item.
    # detector.FDI is not a key, since it has no nested value.
    with pytest.raises(LenaKeyError):
        tab.filter_columns("detector.FDI")


def test_dict_table_el():
    dt = DictTable()

    # DictTable is properly filled and yields
    for val in data:
        dt.fill(val)
    # the result includes common context (intersection of those filled)
    # these are bad tests, since they touch object internals
    # assert dt._contexts == [val[1] for val in data]
    # assert dt._items == [val[1] for val in data]
    res = [
        dict(d[0], common="c"),
        dict(d[1], common="c"),
    ]
    assert list(dt.compute()) == [(dict_table(res), {"common": "c"})]

    # representation works
    assert repr(dt) == "DictTable([{'detector': 'FDI', 'value': 3, 'common': 'c'}, " + \
                                  "{'detector': 'FDII', 'value': 2, 'common': 'c'}])"

    ## empty DictTable works
    # reset works
    dt.reset()
    # equality works
    assert dt == DictTable()
    # empty compute
    assert list(dt.compute()) == [(dict_table([]), {})]
    # representation works
    assert repr(dt) == "DictTable()"
