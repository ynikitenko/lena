import pytest

import lena.core
from lena.flow import GroupBy


def test_group_by():
    ## arbitrary callable works
    data0 = [1, "s", [], 2]
    g0 = GroupBy(type)
    for val in data0:
        g0.update(val)
    r0 = g0.groups
    assert r0[type(1)] == [1, 2]
    assert r0[type(list())] == [[]]
    assert r0[type(str())] == ['s']
    assert len(r0) == 3

    ## clear works
    g0.clear()
    assert len(g0.groups) == 0

    ## wrong initialization parameter raises
    with pytest.raises(lena.core.LenaTypeError):
        GroupBy(1)

    ## context string works
    # simple context string
    data1 = [(1, {"detector": "D1"}),
            (2, {"detector": "D2"}),
            (3, {"detector": "D1"})
           ]
    g1 = GroupBy("{{detector}}")
    for val in data1:
        g1.update(val)
    assert len(g1.groups) == 2
    assert g1.groups == {
        'D1': [(1, {'detector': 'D1'}), (3, {'detector': 'D1'})],
        'D2': [(2, {'detector': 'D2'})]
    }

    data2 = (
        1,
        {"value":
             {"variable":
                 {"name": "x"}},
         "variable": {"name": "mean"}}
    )

    # missing context raises
    with pytest.raises(lena.core.LenaValueError):
        GroupBy("{{non_existent}}").update(data2)

    # several subcontexts work
    g2 = GroupBy("{{value.variable.name}}_{{variable.name}}")
    g2.update(data2)
    assert g2.groups == {
        'x_mean': [
            (1,
             {'value': {'variable': {'name': 'x'}},
              'variable': {'name': 'mean'}})
        ]
    }
