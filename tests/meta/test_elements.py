from copy import deepcopy

import pytest

from lena.core import Sequence, Source, Split

from lena.meta.elements import SetContext, UpdateContextFromStatic, StoreContext

set_context_far  = SetContext("data.detector", "far")
set_context_near = SetContext("data.detector", "near")


def test_set_context():
    # representation works
    assert repr(set_context_far) == 'SetContext("data.detector", "far")'

    # equality works
    set_context_far2  = SetContext("data.detector", "far")
    assert set_context_far2 == set_context_far
    assert set_context_near != set_context_far
    assert set_context_near != "some other value"

    # _get_context works
    assert set_context_far._get_context() == {"data": {"detector": "far"}}


def test_sequence():
    # todo: move to core.
    data = [(0, {})]

    # todo: this should be changed.
    ## static context does not alter context
    # within a sequence
    sfar = Sequence(set_context_far)
    assert list(sfar.run(deepcopy(data))) == data

    # static context is updated after the sequence
    sfar_u0 = Sequence(sfar, UpdateContextFromStatic())
    resfar_u0 = list(sfar_u0.run(deepcopy(data)))
    assert resfar_u0[0][1] == {'data': {'detector': 'far'}}

    # static context is updated after the element
    sfar_u1 = Sequence(set_context_far, UpdateContextFromStatic())
    resfar_u1 = list(sfar_u1.run(deepcopy(data)))
    assert len(resfar_u1) == len(data)
    assert resfar_u1[0][0] == data[0][0]
    assert resfar_u1[0][1] == {'data': {'detector': 'far'}}

    # outside a sequence
    snear = Sequence(deepcopy(sfar), set_context_near)
    assert list(snear.run(deepcopy(data))) == data

    # todo: internal context overwrites external (previous) one
    sfar_u0 = Sequence(set_context_near, deepcopy(sfar), UpdateContextFromStatic())
    resfar_u0 = list(sfar_u0.run(deepcopy(data)))
    assert resfar_u0[0][1] == {'data': {'detector': 'near'}}


def test_set_context_split():
    set_context_far = SetContext("data.detector", "far")
    set_context_near = SetContext("data.detector", "near")
    set_context_common = SetContext("data.lost", True)
    call = lambda _: "we won't run this"
    store1, store2, store3, store4 = [StoreContext() for i in range(1, 5)]

    split = Split([
        (
            set_context_common,
            call,
            set_context_far,
            store2,
        ),
        (
            # common context updates the sequence containing Split
            set_context_common,
            call,
            store3,
            set_context_near,
            # external context overwrites internal one
            SetContext("data.cycle", 2),
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


def test_set_template_context_split():
    set_context_far = SetContext("data.detector", "far")
    set_context_near = SetContext("data.detector", "near")
    set_context_common = SetContext("data.lost", True)
    call = lambda _: "we won't run this"
    store1, store2, store3, store4 = [StoreContext() for i in range(1, 5)]

    seq = Sequence(
        # common context updates the sequence containing Split
        set_context_common,
        call,
        store3,
        set_context_near,
        # external context overwrites internal one
        SetContext("data.cycle", 2),
        SetContext("cycle", "{{data.cycle}}"),
        # todo: this is too complicated for now
        # # this will be overwritten
        # SetContext("cycle", "{{cycle}}_indeed"),
        SetContext("detector", "maybe_{{detector}}"),
        SetContext("detector", "{{data.detector}}"),
    )
    # print(seq[-1]._context)
    assert seq._get_context()["detector"] == "maybe_near"

    split = Split([
        (
            set_context_common,
            call,
            # data.cycle is set externally (and correctly)
            SetContext("cycle", "{{data.cycle}}"),
            # SetContext("cycle", "{{cycle}}_indeed"),
            set_context_far,
            store2,
        ),
        seq,
    ])
    assert split._get_context() == {'data': {'lost': True}}

    s0 = Source(
        SetContext("data.cycle", 1),
        call,
        store1,
        split,
        store4
    )
    assert store1.context == {
        'data': {'cycle': 1, 'lost': True},
        'cycle': '1',
    }
    assert store2.context == {
        'data': {'cycle': 1, 'detector': 'far', 'lost': True},
        'cycle': '1',
    }
    assert store3.context == {
        'data': {'cycle': 1, 'detector': 'near', 'lost': True},
        'detector': 'maybe_near',
        'cycle': '1',
        # 'cycle': '2_indeed',
    }
    # static context is the same for the same level of nesting
    assert store4.context == store1.context


def test_store_context():
    sc1 = StoreContext()
    sc2 = StoreContext()
    sc_empty = StoreContext()

    # _set_context works
    seq = Sequence(SetContext("a", "b"), sc1, sc2)

    assert sc1.context == {"a": "b"}

    # representation works
    assert repr(sc1) == 'StoreContext() or "{\'a\': \'b\'}"'

    # equality works
    assert sc1 == sc2
    assert sc1 != sc_empty
    assert sc1 != "some other value"
