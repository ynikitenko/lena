import pytest

from lena.core import LenaIndexError, LenaTypeError, LenaValueError
from lena.math import mesh
from lena.structures import Histogram
from lena.structures.hist_functions import (
    check_edges_increasing,
    get_bin_edges,
    get_bin_on_value_1d, get_bin_on_value,
    get_bin_on_index,
    integral,
    iter_bins,
    iter_cells,
    unify_1_md,
)


def test_check_edges_increasing():
    with pytest.raises(LenaValueError):
        check_edges_increasing([1, 0])
    with pytest.raises(LenaValueError):
        check_edges_increasing([1])
    with pytest.raises(LenaValueError):
        check_edges_increasing([])
    with pytest.raises(LenaValueError):
        check_edges_increasing([[1]])
    check_edges_increasing([1, 2, 3])


def test_get_bin_edges():
    hist = Histogram(mesh((0, 5), 5))
    assert get_bin_edges(0, hist.edges) == (0, 1)
    hist = Histogram(mesh(((0, 5), (0, 1)), (5, 2)))
    assert get_bin_edges((0, 1), hist.edges) == [(0, 1), (0.5, 1)]


def test_get_bin_on_value_1d():
    # attempts to cover the branch ind_guess == ind_max
    # it seems that it is impossible, because of the formula for shift.
    arr = [0, 1, 2, 3, 4, 4.1, 4.9, 7, 8, 9, 9.01]
    assert get_bin_on_value_1d(5, arr) == 6
    assert get_bin_on_value_1d(9.009, arr) == 9

    arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9.01]
    assert get_bin_on_value_1d(9.01, arr) == 10 

    arr = [0, 1, 4, 5, 7, 10]
    assert get_bin_on_value_1d(0, arr) == 0
    assert get_bin_on_value_1d(2, arr) == 1
    assert get_bin_on_value_1d(4, arr) == 2
    assert get_bin_on_value_1d(10, arr) == 5

    arr = [0, 1]
    assert get_bin_on_value_1d(-0.5, arr) == -1
    assert get_bin_on_value_1d(0, arr) == 0
    assert get_bin_on_value_1d(0.5, arr) == 0
    assert get_bin_on_value_1d(1, arr) == 1
    assert get_bin_on_value_1d(1.5, arr) == 1

    arr = [0, 0.5, 1.1, 1.5]
    assert get_bin_on_value_1d(0.7, arr) == 1
    assert get_bin_on_value_1d(1.4, arr) == 2

    arr = [-100, 0.1, 0.2, 0.3, 0.4, 0.5, 1]
    assert get_bin_on_value_1d(0.05, arr) == 0
    assert get_bin_on_value_1d(0.11, arr) == 1
    assert get_bin_on_value_1d(0.49, arr) == 4
    assert get_bin_on_value_1d(0.51, arr) == 5
    assert get_bin_on_value_1d(0.99, arr) == 5

    arr = [-10] + list(range(1, 11))
    assert get_bin_on_value_1d(9.9, arr) == 9


def test_get_bin_on_value():
    edges = [[1, 2, 3], [1, 3.5]]
    assert get_bin_on_value((1.5, 2), edges) == [0, 0]
    assert get_bin_on_value((1.5, 0), edges) == [0, -1]
    assert get_bin_on_value((3, 2), edges) == [2, 0]

    edges = [1, 2, 3]
    assert get_bin_on_value(2, edges) == [1]
    with pytest.raises(LenaValueError):
    # I think that is Value error
    # with pytest.raises(LenaTypeError):
        get_bin_on_value((2, ), edges)


def test_get_bin_on_index():
    assert get_bin_on_index((0, 1), [[0, 1], [0, 0]]) == 1
    assert get_bin_on_index(0, [[0, 1], [0, 0]]) == [0, 1]
    with pytest.raises(LenaIndexError):
        get_bin_on_index(2, [[0, 1], [0, 0]])


def test_iter_cells():
    hist = Histogram(mesh((0, 2), 2))
    assert list(iter_cells(hist)) == [((0, 1), 0), ((1, 2), 0)]
    hist = Histogram(mesh(((0, 5), (0, 1)), (5, 2)))
    assert list(iter_cells(hist))[:2] == [([(0, 1), (0, 0.5)], 0), ([(0, 1), (0.5, 1)], 0)]


def test_unify_1_md():
    arr1 = [1, 2, 3]
    arr2 = [arr1]
    assert unify_1_md([], arr2)[1] == arr2
    assert unify_1_md([], arr1)[1] == arr2
