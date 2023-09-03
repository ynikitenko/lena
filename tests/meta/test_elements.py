from copy import deepcopy

import pytest

from lena.core import Sequence, Source, Split

from lena.meta.elements import SetContext, UpdateContextFromStatic


class StoreContext():

    def __init__(self, name=""):
        self._name = name
        self._has_no_data = True

    def _set_context(self, context):
        print("StoreContext({}), {}".format(self._name, context))
        self.context = context


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
    s1 = Sequence(set_context_near, deepcopy(s0))
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


def test_set_context_split():
    set_context_far = SetContext("data.detector", "far")
    set_context_near = SetContext("data.detector", "near")
    set_context_common = SetContext("data.lost", True)
    call = lambda _: "we won't run this"
    store1, store2, store3, store4 = [StoreContext(str(i)) for i in range(1, 5)]

    split = Split([
        (
            set_context_common,
            call,
            set_context_far,
            store2,
        ),
        (
            set_context_common,
            call,
            store3,
            set_context_near,
        ),
    ])
    assert split._get_context() == {'data': {'lost': True}}

    s0 = Source(
        SetContext("data.cycle", 1),
        call,
        store1,
        split,
        store4
    )
    assert store1.context == {'data': {'cycle': 1, 'lost': True}}
    assert store2.context == {
        'data': {'cycle': 1, 'detector': 'far', 'lost': True}
    }
    assert store3.context == {
        'data': {'cycle': 1, 'detector': 'near', 'lost': True}
    }
    # static context is the same for the same level of nesting
    assert store4.context == store1.context
