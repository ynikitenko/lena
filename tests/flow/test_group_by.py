import pytest

from lena.core import LenaTypeError, LenaValueError
from lena.flow import GroupBy


def test_group_by():
    ## arbitrary callable works
    data0 = [1, "s", [], 2]
    g0 = GroupBy(type)
    for val in data0:
        g0.fill(val)
    r0 = g0.groups
    assert r0[type(1)] == [1, 2]
    assert r0[type(list())] == [[]]
    assert r0[type(str())] == ['s']
    assert len(r0) == 3

    ## reset works
    g0.reset()
    assert len(g0.groups) == 0

    # clear and update are deprecated
    with pytest.warns(DeprecationWarning):
        g0.clear()
    with pytest.warns(DeprecationWarning):
        g0.update(data0[0])

    del g0

    ## wrong initialization parameter raises
    with pytest.raises(LenaTypeError):
        GroupBy(1)

    ## context string works
    # simple context string
    data1 = [(1, {"detector": "D1"}),
            (2, {"detector": "D2"}),
            (3, {"detector": "D1"})
           ]
    g1 = GroupBy("{{detector}}")
    for val in data1:
        g1.fill(val)
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
    with pytest.raises(LenaValueError):
        GroupBy("{{non_existent}}").fill(data2)

    # several subcontexts work
    g2 = GroupBy("{{value.variable.name}}_{{variable.name}}")
    g2.fill(data2)
    assert g2.groups == {
        'x_mean': [
            (1,
             {'value': {'variable': {'name': 'x'}},
              'variable': {'name': 'mean'}})
        ]
    }

    # tuple works
    g3 = GroupBy(("{{value.variable.name}}", "{{variable.name}}"))
    assert g3._group_by(data2) == ('x', 'mean')
    assert g3._group_by((None, {"variable": {"name": "mean"}})) == ('', 'mean')
    # all empty keys raise
    with pytest.raises(LenaValueError) as err:
        g3._group_by(data1)
    assert "no key found" in str(err.value)

    # equality testing works
    g4 = GroupBy(("{{value.variable.name}}", "{{variable.name}}"))
    assert g4 == g3
    assert g4 != g2
