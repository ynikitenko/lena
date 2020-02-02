from __future__ import print_function

import lena.flow
from lena.flow import ISlice, Print
from lena.core import Source


class RunAll():
    def run(self, it):
        for val in it:
            pass
        return
        yield "this is a generator"


def test_print(capsys):
    # this is one of my very first tests, so it's a bit complicated
    # mocker.patch('__future__.print')
    it5 = lambda: ISlice(5)
    printel = Print(end=' ')
    seq1 = Source(lena.flow.CountFrom(0), printel, it5())
    [print(val, sep=" ", end=" ") for val in seq1()]
    captured = capsys.readouterr()
    assert captured.out == "0 0 1 1 2 2 3 3 4 4 "
    seq2 = Source(lena.flow.CountFrom(0), printel, it5(), RunAll())
    list(seq2())
    captured = capsys.readouterr()
    assert captured.out == "0 1 2 3 4 "
