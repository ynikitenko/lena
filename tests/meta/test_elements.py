from copy import deepcopy

import pytest

from lena.core import Sequence, Source

from lena.meta.elements import SetContext, UpdateContextFromStatic


def test_set_context():
    data = [(0, {})]
    set_context_far = SetContext("data.detector", "far")

    # repr works
    assert repr(set_context_far) == 'SetContext("data.detector", "far")'

    ## static context does not alter context
    # within a sequence
    s0 = Sequence(set_context_far)
    assert list(s0.run(deepcopy(data))) == data

    # outside a sequence
    set_context_near = SetContext("data.detector", "near")
    s1 = Sequence(set_context_near, s0)
    assert list(s1.run(deepcopy(data))) == data

    # static context is updated after the element
    s0u0 = Sequence(set_context_far, UpdateContextFromStatic())
    res0u0 = list(s0u0.run(deepcopy(data)))
    assert len(res0u0) == len(data)
    assert res0u0[0][0] == data[0][0]
    assert res0u0[0][1] == {'data': {'detector': 'far'}}

    # static context is updated after the sequence
    s0u1 = Sequence(s0, UpdateContextFromStatic())
    res0u1 = list(s0u1.run(deepcopy(data)))
    assert res0u1[0][1] == {'data': {'detector': 'far'}}

    # external context overwrites internal (further) one
    s1u0 = Sequence(s1, UpdateContextFromStatic())
    res1u0 = list(s1u0.run(deepcopy(data)))
    assert res1u0[0][1] == {'data': {'detector': 'near'}}
