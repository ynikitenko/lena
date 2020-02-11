from __future__ import print_function

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
from lena.flow import Cache, ISlice
from tests.example_sequences import (ASCIILowercase, ASCIIUppercase,
    ascii_lowercase, ascii_uppercase, lowercase_cached_filename, lowercase_cached_seq, id_)
from tests.examples.fill_compute import Count, Sum
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
    flowc = [(val, context) for val in flow]
    res = seq.run(flowc)
    seq_res = list(res)
    assert seq_res == [10, 6]
    # common methods fill and compute work
    seq2 = Split([Sum(), Count()], copy_buf=False)
    for val in flowc:
        seq2.fill(val)
    seq2_res = list(seq2.compute())
    assert seq2_res == seq_res
    # explicit FillComputeSeq initialization
    seq3 = Split([FillComputeSeq(Sum()), FillComputeSeq(Count())])
    seq3_res = list(seq3.run(flowc))
    assert seq3_res == seq_res
    with pytest.raises(LenaAttributeError):
        print(list(seq3()))
        # this won't work, because it's a generator:
        # seq3()

    seq = Split([(ISlice(2), Sum()), Count()])
    print(seq._sequences[0])
    assert list(seq.run(flowc)) == [1, 6]


def test_split_with_fill_request():
    seq1 = Split([(ISlice(1000), FillRequest(Sum(), request="compute"))])
    seq2 = Split([FillRequestSeq(FillRequest(Sum(), request="compute"))])
    seq3 = Split([FillRequest(Sum(), request="compute")])
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
    res3 = list(seq3.run([]))
    assert res3 == [0]

    # test LenaStopFill
    seq4 = Split([(StopFill(2), FillRequest(Sum(), request="compute"))])
    res4 = list(seq4.run(flow))
    assert res4 == [1]
