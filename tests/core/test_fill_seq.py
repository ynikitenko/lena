import pytest

from lena.core import Sequence, Source, FillSeq, FillInto
from lena.flow import StoreFilled
from tests.examples.numeric import Add


def test_lena_sequence_fill():
    ## test LenaSequence
    s1 = FillSeq(StoreFilled())
    s2 = FillSeq(Add(0), StoreFilled())
    # can take len
    assert len(s1) == 1
    assert len(s2) == 2
    # can get item
    # data_seq wraps an element in an adapter
    assert isinstance(s2._data_seq[0], FillInto)
    # original sequence stores the element as it was
    assert isinstance(s2._seq[0], Add)
    # deletion is prohibited
    with pytest.raises(TypeError):
        del s2[0]
    # setting elements is prohibited
    with pytest.raises(TypeError):
        s2[0] = 0


def test_fill():
    store0 = StoreFilled()

    s1 = FillSeq(store0)
    # empty FillSeq sequence doesn't transform
    s1.fill(1)
    assert store0.group == [1]

    store = StoreFilled()
    s2 = FillSeq(Add(0), store)
    store.list = []
    s2.fill(1)
    assert store.group == [1]

    # Store adds elements
    s3 = FillSeq(Add(1), store)
    s3.fill(1)
    assert store.group == [1, 2]
    # sequence of two elements
    s4 = FillSeq(Add(1), Add(-1), store)
    s4.fill(1)
    assert store.group == [1, 2, 1]

    # nested long FillSeq
    # won't work here.
    # store = StoreFilled()
    # s5 = FillSeq(s1, Add(0), *s4, Add(3), store)
    # s5.fill(1)
    # assert store == [4]
    # with pytest.raises(lena.core.LenaTypeError):
    #     s = FillSeq(5, store)
