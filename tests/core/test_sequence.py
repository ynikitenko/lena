"""args is a list of functions or executable classes.

>>> it2 = ISlice(2)
>>>
>>> for el in it2.run(cnt0()):
...        print(el, end=" ")
0 1 
>>>
>>> from lena.flow import Count, Print, ISlice
>>> it5  = ISlice(5)
>>> seq = Source(cnt0, Sequence(it5))
>>> res = seq()
>>> for val in res:
...        print(val, end=" ")
0 1 2 3 4 
>>>
>>> # Test chained sequences.
>>> printsseq(seq)
0 1 2 3 4
>>> seq2 = Sequence(mul2)
>>> printsseq(seq)
0 1 2 3 4
>>>
>>> pseq = Print(end=' ')
>>> seq3 = Source(seq, pseq, seq2)
>>> printsseq(seq3)
0 1 2 3 4 0 2 4 6 8
>>>
"""
from __future__ import print_function

import pytest
from itertools import islice

from lena.core import LenaTypeError
from lena.core import Source, Sequence
from lena.flow import Count, Print, ISlice, TransformIf
from lena.flow import Print
from itertools import islice
from tests.core.test_fill_compute_seq import mul2


def cnt0(): 
    i = 0
    while True:
        yield i
        i = i + 1


def test_sequence_init():
    it5 = ISlice(5)
    sseq = Source(cnt0, it5)
    with pytest.raises(LenaTypeError):
        sseq = Source(cnt0, it5, ())


def test_sequence():
    it5 = ISlice(5)
    sseq = Source(cnt0, it5)
    assert list(sseq()) == [0, 1, 2, 3, 4]
    seq = Sequence(TransformIf(int, lambda i: i+1))
    print(list(seq.run(sseq())))

    # Test special double underscore methods,
    # emulating a container.
    # can create a list from that
    seq2 = Sequence(*list(seq))
    # can take len
    assert len(seq2) == 1
    # can get item
    assert isinstance(seq2[0], TransformIf)
    # deletion is prohibited
    # I don't know why, but last time both exceptions below were AttributeError
    # it changed after I based Sequence on LenaSequence 
    # (based on object, which was not before).
    with pytest.raises(TypeError):
        del seq2[0]
    # setting elements is prohibited
    with pytest.raises(TypeError):
        seq2[0] = 0

def printsseq(sseq):
    res = sseq()
    # for val in res:
    #     print(val, end=" ")
    print(*[val for val in res], sep=" ")
    # print()


# test_sequence()

