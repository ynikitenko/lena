import pytest

from lena.flow.progress import Progress


def test_progress(capsys):
    data = list(range(3))

    # default formatting with no name works
    p1 = Progress()
    assert list(p1.run(data)) == data
    captured = capsys.readouterr()
    assert captured.out == "  33% [1/3] \n  67% [2/3] \n 100% [3/3] \n"

    # default formatting with name works
    data = [0]
    p2 = Progress("events")
    assert list(p2.run(data)) == data
    captured = capsys.readouterr()
    assert captured.out == " 100% [1/1] events\n"

    # custom formatting works
    p3 = Progress("hares got", format="{index}/{total} {name}")
    assert list(p3.run(data)) == data
    captured = capsys.readouterr()
    assert captured.out == "1/1 hares got\n"
