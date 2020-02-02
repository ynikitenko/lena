from __future__ import print_function

import pytest

from lena.core import Sequence, Source, LenaTypeError, LenaValueError, Call
from lena.core.split import Split
from lena.flow import Cache
from lena.flow import ISlice
from tests.example_sequences import (ASCIILowercase, ASCIIUppercase,
    ascii_lowercase, ascii_uppercase, lowercase_cached_filename, lowercase_cached_seq, id_)
from tests.examples.fill_compute import Count, Sum
from tests.core.test_fill_compute_seq import cnt1


def test_split_init():
    # check whether requires initialization with a list
    with pytest.raises(LenaTypeError):
        s = Split(ascii_lowercase, ascii_uppercase)
    # empty list allowed
    s = Split([])
    with pytest.raises(LenaTypeError):
        s = Split([((), ()),])

    # bufsize must be a natural number or None
    with pytest.raises(LenaValueError):
        s = Split([ascii_lowercase, ascii_uppercase], bufsize=0)
    with pytest.raises(LenaValueError):
        s = Split([ascii_lowercase, ascii_uppercase], bufsize=1.5)


def test_split_buffer():
    s = Split([ascii_lowercase, ascii_uppercase])
    assert "".join(s()) == "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = Split([ascii_lowercase, ascii_uppercase], bufsize=1)
    # no difference, because these are Sources, not Sequences
    assert "".join(s()) == "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

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
    # print(seq._sequences)
    assert seq._seq_types == ['fill_compute', 'fill_compute']
    flow = [0, 1, 2, 3, 4, 0]
    context = {'type': 'extended histogram'}
    flowc = [(val, context) for val in flow]
    res = seq.run(flowc)
    assert list(res) == [10, 6]

    seq = Split([(ISlice(2), Sum()), Count()])
    print(seq._sequences[0])
    assert list(seq.run(flowc)) == [1, 6]
