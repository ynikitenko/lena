from __future__ import print_function

import os
import os

import pytest

from lena.flow import Cache
from lena.core import Sequence, Source, LenaTypeError, LenaValueError
from tests.example_sequences import (
    ASCIILowercase, ASCIIUppercase, ascii_lowercase, ascii_uppercase,
    lowercase_cached_filename, lowercase_cached_seq, id_
)
from lena.core import Source
from lena.flow.cache import Cache
from lena.flow.iterators import Slice
from tests.shortcuts import cnt1, cnt1c


def test_cache():
    lowercase_cached_seq[0].drop_cache()
    s = Source(ascii_lowercase, lowercase_cached_seq)
    assert "".join(s()) == "abcdefghijklmnopqrstuvwxyz"
    # cache is actually used
    s = Source(ascii_uppercase, lowercase_cached_seq)
    assert "".join(s()) == "abcdefghijklmnopqrstuvwxyz"
    lowercase_cached_seq[0].drop_cache()


# it's shame, but I had two tests in different files
def test_cache_2():
    # works well in sequence
    s1 = Source(
            cnt1,
            Slice(2),
            Cache("cache.tmp"),
         )
    res1 = [result for result in s1()]
    assert len(res1) == 2
    assert res1 == [1, 2]

    # works well after cached
    s2 = Source(
            cnt1,
            Cache("cache.tmp"),
         )
    res2 = [result for result in s2()]
    assert res1 == res2

    # works well with later elements in sequence
    s3 = Source(
            cnt1,
            Cache("cache.tmp"),
            Slice(1),
         )
    res3 = [result for result in s3()]
    assert res3 != res2
    assert res2 == res3 + [2]

    # works well for flow with context
    s4c = Source(
            cnt1c,
            Slice(2),
            Cache("cache_c.tmp"),
         )
    res4 = [result for result in s4c()]
    assert res4 == [(1, {'1': 1}), (2, {'2': 2})]

    # clean up
    os.remove("cache.tmp")
    os.remove("cache_c.tmp")


def test_alter_sequence():
    cached_to_source = Cache.alter_sequence
    # remove cache
    try:
        os.remove(lowercase_cached_filename)
    except Exception:
        pass
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

    lowercase_cache_el.drop_cache()
