import os

import pytest

from lena.core import Sequence, Source, LenaTypeError, LenaValueError
from lena.flow.cache import Cache
from lena.flow.iterators import Slice
from lena.meta import SetContext

from tests.example_sequences import (
    ASCIILowercase, ASCIIUppercase, ascii_lowercase, ascii_uppercase,
    lowercase_cached_filename, lowercase_cached_seq, id_,
)
from tests.shortcuts import cnt1, cnt1c


def test_cache(tmpdir):
    low_letters = "abcdefghijklmnopqrstuvwxyz"
    os.chdir(str(tmpdir))

    # empty cache makes no problems
    s1 = Source(ascii_lowercase, lowercase_cached_seq)
    assert "".join(s1()) == low_letters

    # filled cache is actually used
    s2 = Source(ascii_uppercase, lowercase_cached_seq)
    assert "".join(s2()) == low_letters

    # recompute works
    c3 = Cache(lowercase_cached_filename, recompute=True)
    s3 = Source(ascii_uppercase, c3)
    assert "".join(s3()) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# it's a shame, but I had two tests in different files
def test_cache_2(tmp_path):
    cache1 = str(tmp_path / "cache.pkl")
    # works well in sequence
    s1 = Source(
            cnt1,
            Slice(2),
            Cache(cache1),
         )
    res1 = [res for res in s1()]
    assert res1 == [1, 2]

    # works well after cached
    s2 = Source(
            cnt1,
            Slice(10),
            Cache(cache1),
         )
    res2 = list(s2())
    print(cache1, res2)
    assert res1 == res2

    # works well with later elements in sequence
    s3 = Source(
            cnt1,
            Cache(cache1),
            Slice(1),
         )
    res3 = [result for result in s3()]
    assert res3 != res2
    assert res2 == res3 + [2]

    # works well for flow with context
    cache_c = str(tmp_path / "cache_c")
    s4c = Source(
            cnt1c,
            Slice(2),
            Cache(cache_c),
         )
    res4 = [result for result in s4c()]
    assert res4 == [(1, {'1': 1}), (2, {'2': 2})]


def test_alter_sequence(tmpdir):
    os.chdir(str(tmpdir))
    cached_to_source = Cache.alter_sequence

    lowercase_cache_el = Cache(lowercase_cached_filename)
    el = lowercase_cache_el 
    s0 = Sequence(el)
    s = Sequence(lowercase_cached_seq, id_)
    # no change occurs
    ## for the element
    assert cached_to_source(el) == el
    ## for the Sequence
    assert cached_to_source(s) == s

    # fill cache
    assert "".join(s.run(list(ascii_lowercase()))) == "abcdefghijklmnopqrstuvwxyz"
    # changes to Source
    ## element
    assert cached_to_source(el) != el 
    assert isinstance(cached_to_source(el), Source)

    assert cached_to_source(s0) != s0
    assert isinstance(cached_to_source(s0), Source)
    # this fails for nested Sequences. To be done.
    assert cached_to_source(s) != s
    assert isinstance(cached_to_source(s), Source)

def test_set_context():
    orig_filename = "{{detector}}_detector.pkl"
    cache = Cache(orig_filename)
    s = Sequence(SetContext("detector", "far"), cache)
    assert cache._orig_filename == orig_filename
    assert cache._filename == "far_detector.pkl"
