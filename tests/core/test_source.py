import pytest
from itertools import islice

import lena.core
from lena.core import Source, Sequence
from lena.flow import Slice, CountFrom

from tests.shortcuts import cnt0


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

    # empty and wrong arguments raise proper errors
    with pytest.raises(lena.core.LenaTypeError):
        s = Source()
    with pytest.raises(lena.core.LenaTypeError):
        s = Source(1)

    # can initialize from iterable
    src3 = Source([1, 2, 3], lambda val: val+1)
    assert list(src3()) == [2, 3, 4]

    # emits a warning for a single iterable element
    with pytest.warns(UserWarning):
        # This really looks like an error.
        # What would that sequence do anyway.
        Source((cnt0, Slice(1)))
