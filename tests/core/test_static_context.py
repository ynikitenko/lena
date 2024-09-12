from copy import deepcopy

import pytest

from lena.core import Sequence, Source, Split

# we don't test them here, but use them for our tests.
from lena.meta.elements import SetContext, UpdateContextFromStatic, StoreContext

set_context_far  = SetContext("data.detector", "far")
set_context_near = SetContext("data.detector", "near")


def test_sequence():
    data = [(0, {})]
    cfar = {'data': {'detector': 'far'}}
    cnear = {'data': {'detector': 'near'}}

    # simple set and get works
    sfar = Sequence(set_context_far)
    assert sfar._get_context() == cfar

    # nested sequence with a context works
    sfar2 = Sequence(deepcopy(sfar))
    assert sfar2._get_context() == cfar

    # later context updates the previous one
    snear1 = Sequence(deepcopy(sfar), set_context_near)
    assert snear1._get_context() == cnear

    # internal context overwrites external (previous) one
    sc1 = StoreContext()
    sc2 = StoreContext()
    sc_empty = StoreContext()
    sfar3 = Sequence(sc_empty, set_context_near, sc1, lambda val: val, deepcopy(sfar), sc2)
    assert sfar3._get_context() == cfar
    assert sc1.context == cnear
    assert sc2.context == cfar
    assert sc_empty.context == {}

    ## todo v0.7: to be be changed.
    # static context does not alter context
    # within a sequence
    sfar = Sequence(set_context_far)
    assert list(sfar.run(deepcopy(data))) == data

    # with UpdateContextFromStatic,
    # static context is updated after the sequence
    sfar_u0 = Sequence(sfar, UpdateContextFromStatic())
    resfar_u0 = list(sfar_u0.run(deepcopy(data)))
    assert resfar_u0[0][1] == cfar


def _test_set_context_split():
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


def _test_set_template_context_split():
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
