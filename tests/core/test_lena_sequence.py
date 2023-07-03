import pytest

from lena.core import Source, Sequence
from lena.flow import Count, Slice

from tests.shortcuts import cnt0


def test_repr_sequence():
    # zero-element sequence works
    s01 = Sequence()
    assert repr(s01) == "Sequence()"

    # one-element sequence works
    s02 = Sequence(Sequence())
    assert repr(s02) == "Sequence(\n    Sequence()\n)"

    # nesting works
    s03 = Sequence(Sequence(Sequence()))
    # print(s03)
    assert repr(s03) == "Sequence(\n    Sequence(\n        Sequence()\n    )\n)"


def test_repr_source():
    # not Lena elements can also be represented
    cnt = cnt0
    slice1 = Slice(1)

    # representation with one element works
    s1 = Source(cnt)
    mnl = "\n"
    # print(s1)
    assert repr(s1) == "".join(["Source(", mnl,
                                " "*4, repr(cnt), mnl, ")"])

    # representation with two elements works
    s2 = Source(cnt, slice1)
    # print(s2)
    assert repr(s2) == "".join(["Source(", mnl,
                                " "*4, repr(cnt), ",", mnl,
                                " "*4, repr(slice1), mnl, ")"])
