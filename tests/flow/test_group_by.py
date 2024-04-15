import pytest

from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy


# In Python 2 the order of results is different than that in Python 3.
def oeq(c1, c2):
    # compare containers of distinct elements ignoring order
    if len(c1) != len(c2):
        return False
    for val in c1:
        if val not in c2:
            return False
    # just to be sure about duplicates.
    # Copied the idea from test_group_plots.py
    for val in c2:
        if val not in c1:
            return False
    return True


def test_group_by_include():
    ## trivial selection works
    # none of these values has a context, they will have the same key
    data0 = [1, "s", [], 2]
    g0 = GroupBy("", merge=tuple())
    for val in data0:
        g0.fill(val)
    # compute returns already lists of values.
    # Since they have the same key, they will be returned
    # in the proper order.
    assert list(g0.compute()) == [data0]

    ## reset works
    g0.reset()
    assert len(g0.groups) == 0

    # clear and update are deprecated
    with pytest.warns(DeprecationWarning):
        g0.clear()
    with pytest.warns(DeprecationWarning):
        g0.update(data0[0])

    del g0

    ## wrong initialization parameters raise
    with pytest.raises(LenaTypeError):
        GroupBy(1)

    ## context string works
    # simple context string
    data1 = [
        (1, {"detector": "D1"}),
        (2, {"detector": "D2"}),
        (3, {"detector": "D1"})
    ]
    # we don't have to manually write merge=tuple()
    g1 = GroupBy("")
    for val in data1:
        g1.fill(val)
    assert set(g1.groups.keys()) == set([
        '{"detector":"D1"}', '{"detector":"D2"}'
    ])
    groups1 = list(g1.compute())

    assert oeq(groups1, [
        [(1, {'detector': 'D1'}), (3, {'detector': 'D1'})],
        [(2, {'detector': 'D2'})]
    ])

    data2 = [
        (1, {"value":
             {"variable":
                 {"name": "x"}},
             "variable": {"name": "mean"}}),
        (2, {"value":
             {"variable":
                 {"name": "y"}},
             "variable": {"name": "mean"}}),
    ]

    # Previously, context was required to confirm to group_by.
    # Now we make a general selection. If a context key is required,
    # that could be checked by another element.
    # # missing context raises
    # with pytest.raises(LenaValueError):
    #     GroupBy("{{non_existent}}").fill(data2)

    # several subcontexts work
    g2 = GroupBy(("value.variable.name", "variable.name"))
    # but this looked really beautiful. And, at the same time,
    # it was a multiple ways to do the same.
    # g2 = GroupBy("{{value.variable.name}}_{{variable.name}}")
    g2.fill(data2[0])
    g2.fill(data2[1])
    groups2 = list(g2.compute())
    assert oeq(groups2, [
        [
            (1,
             {'value': {'variable': {'name': 'x'}},
              'variable': {'name': 'mean'}})
        ],
        [
            (2,
             {'value': {'variable': {'name': 'y'}},
              'variable': {'name': 'mean'}})
        ]
    ])

    ## Equality testing works
    # same as g2, but the key order changed
    g3 = GroupBy(("variable.name", "value.variable.name"))
    assert g3 == g2
    assert g3 != g1


def test_group_by_exclude():
    data = [
        (1, {"data_type": "data",
             "value": {
                       "variable": {"name": "x"},
                       "name": "mean"
             }}),
        (2, {"data_type": "data",
             "value": {
                       "variable": {"name": "y"},
                       "name": "median"}}),
        (3, {"data_type": "MC",
             "value": {
                       "variable": {"name": "x"},
                       "name": "median"}}),
        (4, {"data_type": "MC",
             "value": {
                       "variable": {"name": "y"},
                       "name": "mean"}}),
    ]
    gbe1 = GroupBy(merge=("data_type", "value.name"))
    gbe2 = GroupBy(merge=("value.variable.name", "value.name"))

    # nested subkeys raise
    with pytest.raises(LenaValueError):
        GroupBy(merge=("value", "value.variable.name"))
    with pytest.raises(LenaValueError):
        GroupBy(merge=("value", "value.variable"))

    # include and exclude work together
    gbe3 = GroupBy(group_by=("", "value.variable.name"),
                   merge=("value", "data_type"))
    for val in data:
        gbe1.fill(val)
        gbe2.fill(val)
        gbe3.fill(val)

    def group_data(group):
        return [val[0] for val in group]

    dtres1 = [group_data(grp) for grp in gbe1.compute()]
    dtres2 = [group_data(grp) for grp in gbe2.compute()]
    dtres3 = [group_data(grp) for grp in gbe3.compute()]

    # ignore data_type
    assert oeq(dtres1, [[1, 3], [2, 4]])
    # ignore value.variable.name
    assert oeq(dtres2, [[1, 2], [3, 4]])
    # ignore value.name and data_type
    assert oeq(dtres3, [[1, 3], [2, 4]])
