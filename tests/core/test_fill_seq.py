from __future__ import print_function

import pytest

import lena.core 
from lena.core import Sequence, Source
from lena.core import FillSeq, FillInto
from tests.examples.fill import StoreFilled
from tests.examples.numeric import Add


def test_lena_sequence_fill():
    ## test LenaSequence
    s1 = FillSeq(StoreFilled())
    s2 = FillSeq(Add(0), StoreFilled())
    # can take len
    assert len(s1) == 1
    assert len(s2) == 2
    # can get item
    assert isinstance(s2[0], FillInto)
    # deletion is prohibited
    with pytest.raises(TypeError):
        del s2[0]
    # setting elements is prohibited
    with pytest.raises(TypeError):
        s2[0] = 0


def test_fill():
    store = StoreFilled()

    s1 = FillSeq(store)
    # empty FillSeq sequence doesn't transform
    s1.fill(1)
    assert store == [1]

    s2 = FillSeq(Add(0), store)
    store.list = []
    s2.fill(1)
    assert store == [1]

    # Store adds elements
    s3 = FillSeq(Add(1), store)
    s3.fill(1)
    assert store.list == [1, 2]
    # sequence of two elements
    s4 = FillSeq(Add(1), Add(-1), store)
    s4.fill(1)
    assert store == [1, 2, 1]

    # nested long FillSeq
    # won't work here.
    # store = StoreFilled()
    # s5 = FillSeq(s1, Add(0), *s4, Add(3), store)
    # s5.fill(1)
    # assert store == [4]
    # with pytest.raises(lena.core.LenaTypeError):
    #     s = FillSeq(5, store)
