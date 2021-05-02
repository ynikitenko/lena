from __future__ import print_function

import pytest
from itertools import islice

import lena.core
from lena.core import Source, Sequence
from lena.flow import Slice


def cnt0(): 
    i = 0
    while True:
        yield i
        i = i + 1


def test_source():
    it5 = Slice(5)
    sseq = Source(cnt0, it5)
    assert list(sseq()) == [0, 1, 2, 3, 4]

    ## Test special double underscore methods, emulating a container.
    # can create a list from that
    seq2 = Source(*list(sseq))
    # can take len
    assert len(seq2) == 2
    # can get item
    assert callable(seq2[0])

    # deletion is prohibited
    with pytest.raises(TypeError):
        del seq2[0]
    # setting elements is prohibited
    with pytest.raises(TypeError):
        seq2[0] = 0

    with pytest.raises(lena.core.LenaTypeError):
        s = Source()
    with pytest.raises(lena.core.LenaTypeError):
        s = Source(1)
