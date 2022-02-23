import copy
import pytest

import lena.core
from lena.core import (
    Split, Sequence, Source, Call, FillComputeSeq, FillRequestSeq,
    FillCompute, FillRequest,
)
from lena.core import (
    LenaAttributeError, LenaRuntimeError, LenaTypeError, LenaValueError,
    LenaStopFill,
)
from lena.flow import Cache, Slice
from tests.example_sequences import (ASCIILowercase, ASCIIUppercase,
    ascii_lowercase, ascii_uppercase, lowercase_cached_filename, lowercase_cached_seq, id_)
# from tests.examples.fill_compute import Count
from lena.math import Sum
from lena.flow import Count
from tests.core.test_fill_compute_seq import cnt1


class StopFill():
    def __init__(self, max_count):
        self._max_count = max_count
        self._count = 0

    def fill_into(self, el, val):
        """If more than *max_count* times was filled,
        nothing is filled and LenaStopFill is raised.
        """
        if self._count >= self._max_count:
            raise lena.core.LenaStopFill
        el.fill(val)
        self._count += 1


class RunWithTrue():

    def run(self, flow):
        for val in flow:
            yield val
        yield True


def test_split_init():
    # initialization with a list is required
    with pytest.raises(LenaTypeError):
        s = Split(ascii_lowercase, ascii_uppercase)

    # empty list allowed
    s = Split([])
    flowc = [0, (1, {}), 2]
    assert list(s.run(flowc)) == flowc

    with pytest.raises(LenaTypeError):
        s = Split([((), ()),])

    # bufsize must be a natural number or None
    with pytest.raises(LenaValueError):
        s = Split([ascii_lowercase, ascii_uppercase], bufsize=0)
    with pytest.raises(LenaValueError):
        s = Split([ascii_lowercase, ascii_uppercase], bufsize=1.5)

    s = Split([RunWithTrue(), Sum()])
    res = list(s.run([]))
    assert res == [True, 0]


def test_split_buffer():
    s = Split([ascii_lowercase, ascii_uppercase])
    LOW_UP = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert "".join(s()) == LOW_UP
    s = Split([ascii_lowercase, ascii_uppercase], bufsize=1)
    # bufsize makes no difference, because these are Sources, not Sequences
    assert "".join(s.run([])) == LOW_UP
    assert "".join(s.run([0])) == LOW_UP

    # test Split in Source
    s = Source(ascii_lowercase, Split([lambda s: s.upper(), lambda s: s.lower()]))
    assert "".join(s()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    s = Source(ascii_lowercase, Split([lambda s: s.upper(), lambda s: s.lower()], bufsize=1))
    assert "".join(s()) == "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"

    # bufsize = None or 1000 does not matter
    s = Source(ascii_lowercase, Split([lambda s: s.upper(), lambda s: s.lower()], bufsize=None))
    assert "".join(s()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def test_split_sequence_with_cache():
    lowercase_cached_seq[0].drop_cache()
    s = Source(ascii_lowercase, Split([lambda s: s.upper(), lowercase_cached_seq]))
    # print(list(Cache(lowercase_cached_filename)._load_flow()))
    # print(Call(Cache(lowercase_cached_filename), call="_load_flow")())
    # print(list(Call(Cache(lowercase_cached_filename), call="_load_flow")()))
    assert "".join(s()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    # cache is actually used
    # Single Cache element
    s = Source(ascii_uppercase, Split([lambda s: s.upper(), lowercase_cached_seq]))
    assert "".join(s()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    # Sequence with Cache
    s = Source(ascii_uppercase, Split([lambda s: s.upper(), (lambda val: val, lowercase_cached_seq)]))
    assert "".join(s()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    # sequences are called in the order they were initialized in Source
    s = Source(ascii_uppercase, 
            Split([
                lambda s: s.upper(), 
                (lambda val: val, Cache(lowercase_cached_filename)),
                id_
            ])
        )
    assert "".join(s()) == \
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowercase_cached_seq[0].drop_cache()


def test_split_with_fill_computes():
    seq = Split([Sum(), Count()])
    assert seq._seq_types == ['fill_compute', 'fill_compute']

    flow = [0, 1, 2, 3, 4, 0]
    context = {'type': 'extended histogram'}
    orig_context = copy.deepcopy(context)
    counter_context = {'type': 'extended histogram', 'counter': 6}
    # otherwise context is updated by the last sequence.
    flowc = [(val, copy.deepcopy(context)) for val in flow]
    seq_res = list(seq.run(flowc))
    assert seq_res == [(10, orig_context), (6, counter_context)]

    # common methods fill and compute work
    seq2 = Split([Sum(), Count()], copy_buf=False)
    for val in flowc:
        seq2.fill(val)
    seq2_res = list(seq2.compute())
    assert seq2_res == [(10, counter_context), (6, counter_context)]

    # explicit FillComputeSeq initialization
    seq3 = Split([FillComputeSeq(Sum()), FillComputeSeq(Count())])
    seq3_res = list(seq3.run(flowc))
    assert seq3_res == seq2_res
    with pytest.raises(LenaAttributeError):
        # print(list(seq3()))
        list(seq3())

    seq = Split([(Slice(2), Sum()), Count()])
    # print(seq._sequences[0])
    assert list(seq.run(flowc)) == [(1, orig_context), (6, counter_context)]


def test_split_with_fill_request():
    seq1 = Split([(
        Slice(1000),
        FillRequest(Sum(), reset=True, buffer_input=True)
    )])
    seq2 = Split([
        FillRequestSeq(FillRequest(Sum(), reset=True, buffer_input=True),
                       buffer_input=True, reset=False)
    ])

    flow = [0, (1, {}), 2, 3]
    for val in flow:
        seq2.fill(val)
    res2 = list(seq2.request())
    # no compute method must be present
    with pytest.raises(AttributeError):
        list(seq2.compute())
    res1 = list(seq1.run(flow))
    assert res1 == res2

    # run with empty flow
    seq3 = Split([FillRequest(Sum(), reset=True, buffer_input=True)])
    res3 = list(seq3.run([]))
    # FillRequest doesn't yield for empty slices.
    assert res3 == []

    # test LenaStopFill
    seq4 = Split([(
        StopFill(2),
        FillRequest(Sum(), reset=True, buffer_input=True)
    )])
    res4 = list(seq4.run(flow))
    assert res4 == [0, 1]
    # now we call request for each bufsize values.
    # assert res4 == [1]
