from copy import deepcopy

import pytest

from lena.core import Sequence, Source, Split, LenaKeyError
from lena.flow import Count

# we don't test them here, but use them for our tests.
from lena.meta.elements import SetContext, UpdateContextFromStatic, StoreContext

# note that SetContext gets external context as well,
# so it may be dangerous to reuse them in different sequences.
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


def test_set_context_split():
    set_context_common = SetContext("data.lost", True)
    call = lambda _: "we won't run this"
    store1, store_f2, store3, store_n4, store5 = [StoreContext() for _ in range(5)]
    # [StoreContext()] * 5 wouldn't work here, the objects would be the same.

    split = Split([
        (
            set_context_common,
            call,
            set_context_far,
            store_f2,
        ),
        (
            set_context_common,
            call,
            store3,
            set_context_near,
            SetContext("data.cycle", 2),
            store_n4,
        ),
    ])

    # the resulting context is intersection of the inner contexts.
    assert split._get_context() == {'data': {'lost': True}}

    s0 = Source(
        SetContext("data.cycle", 1),
        call,
        store1,
        split,
        store5
    )
    # context before Split is correct
    assert store1.context == {'data': {'cycle': 1}}

    # external context is passed into sequences
    assert store_f2.context == {
        'data': {'cycle': 1, 'detector': 'far', 'lost': True}
    }
    assert store3.context == {
        'data': {'cycle': 1, 'lost': True}
    }
    # external context is overwritten in further sequences
    # (probably that should be tested in a Sequence).
    assert store_n4.context == {
        'data': {'cycle': 2, 'detector': 'near', 'lost': True}
    }

    # the resulting context is intersection of the inner contexts.
    assert store5.context == {'data': {'lost': True}}

    # Split with an element without a static context works
    store11 = StoreContext()
    s1 = Source(
        SetContext("cycle", 1),
        Split([Count()]),
        store11,
    )
    assert store11.context == {'cycle': 1}


def test_set_formatted_context():
    # this function tests at large, but is still useful.
    set_context_common1 = SetContext("data.lost", True)
    set_context_common2 = SetContext("data.lost", True)
    call = lambda _: "we won't run this"
    store1, store_split, store3, store4 = [StoreContext() for _ in range(1, 5)]

    # elements that could not set context raise
    s0 = Sequence(
        call,
        store3,
        SetContext("cycle", "{{data.cycle}}"),
        call,
    )
    with pytest.raises(LenaKeyError) as exc:
        s0._get_context()
    # Sequence knows that the key "data" was missing
    # while setting static context.
    assert "data" in str(exc.value)
    # the complete string is 'nested dict data not found in {}',
    # but it might change.

    seq = Sequence(
        set_context_common1,
        call,
        store3,
        set_context_near,
        # internal context overwrites external one
        SetContext("data.cycle", 2),
        SetContext("cycle", "{{data.cycle}}"),
        SetContext("detector", "{{data.detector}}"),
        SetContext("detector", "maybe_{{detector}}"),
    )
    # context formatting works in Sequence reality.
    assert seq._get_context()["detector"] == "maybe_near"

    split = Split([
        (
            set_context_common2,
            call,
            # data.cycle is set externally (and correctly)
            SetContext("cycle", "{{data.cycle}}"),
            set_context_far,
            store_split,
        ),
        seq,
    ])

    s0 = Source(
        SetContext("data.cycle", 1),
        call,
        store1,
        split,
        store4
    )
    assert store1.context == {'data': {'cycle': 1}}
    assert store_split.context == {
        'data': {'cycle': 1, 'detector': 'far', 'lost': True},
        'cycle': '1',
    }
    assert store3.context == {
        'data': {'lost': True, 'cycle': 1,}
    }
    # intersection of Split branches, data.cycle is removed.
    assert store4.context == {'data': {'lost': True}}
