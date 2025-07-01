from __future__ import print_function

import lena.flow
from lena.flow import Slice, Print
from lena.core import Source


def test_print(capsys):
    # this is one of my very first tests, so it's a bit complicated
    # mocker.patch('__future__.print')
    it5 = lambda: Slice(5)
    printel = Print(end=' ')
    seq1 = Source(lena.flow.CountFrom(0), printel, it5())
    [print(val, sep=" ", end=" ") for val in seq1()]
    captured = capsys.readouterr()
    assert captured.out == "0 0 1 1 2 2 3 3 4 4 "

    seq2 = Source(lena.flow.CountFrom(0), printel, it5(), lena.flow.End())
    list(seq2())
    captured = capsys.readouterr()
    assert captured.out == "0 1 2 3 4 "

    # equality test works
    assert printel == Print(end=' ')
    assert printel != Print()
    assert Print() == Print()
