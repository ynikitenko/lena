import pytest

from lena.core import Source, Sequence, Split
from lena.core import LenaTypeError
from lena.flow import CountFrom, Slice

from lena.meta import merge_heads


def test_merge_heads():
    s0 = Source(CountFrom(0))
    s1 = Source(CountFrom(0))
    # same sequences with one element merge
    assert merge_heads(s0, s1) == s0

    # no sequences raise
    with pytest.raises(LenaTypeError):
        merge_heads()

    s2 = Source(CountFrom(0), Slice(2))
    s3 = Source(CountFrom(0), Slice(2))
    s4 = Source(CountFrom(0), Slice(1))

    # same sequences with several elements merge
    assert merge_heads(s2, s3) == s2

    # sequences with different elements are properly merged
    merge24 = Source(
        CountFrom(0),
        Split([
            Slice(2),
            Slice(1),
        ]),
    )
    assert merge_heads(s2, s4) == merge24

    # s3 is merged with s2
    assert merge_heads(s2, s4, s3) == merge24
