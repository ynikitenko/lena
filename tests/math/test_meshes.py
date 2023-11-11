"""Testing mesh functions.

refine_mesh properties:

- original mesh values are in refined.
- refine N composed with refine M is refine N * M
- refine 1 is same mesh

mesh properties:
- edges are always conserved.
- if nbins is 1, return mesh.
- mesh with nbins * N is mesh refined with N.
- mesh points are equidistant.
"""
from __future__ import print_function

import pytest

from lena.math import md_map, mesh, refine_mesh

from tests.examples.fill_compute import Count


def test_md_map():
    # one array works
    arr0 = [0, 1]
    add_one = lambda x: x + 1
    assert md_map(add_one, arr0) == [1, 2]

    # two arrays work
    arr1 = [0, 1]
    sum_two = lambda a, b: a + b
    assert md_map(sum_two, arr0, arr1) == [0, 2]

    # one nested array works
    assert md_map(add_one, [arr0]) == [[1, 2]]

    # two nested arrays work
    assert md_map(sum_two, [arr0], [arr1]) == [[0, 2]]

    # generators work
    arr2 = [Count(), Count()]
    arr2[1].fill(1)
    seq_map = lambda cell: list(cell.compute())[0]
    assert md_map(seq_map, arr2) == [0, 1]

    # example from doctest
    arr3 = [[0, -1], [2, 3]]
    assert md_map(abs, arr3) == [[0, 1], [2, 3]]


def test_refine_mesh():
    arr = [0, 1]
    arr2 = refine_mesh(arr, 2)
    assert arr2 == [0, 0.5, 1]
    arr4 = refine_mesh(arr, 4)
    assert arr4 == refine_mesh(arr2, 2)
    # assert arr_refined == [0, 0.25, 0.5, 0.75, 1]
    arr = [-10, 0, 1, 1.5]
    assert refine_mesh(arr, 4) == refine_mesh(refine_mesh(arr, 2), 2)


if __name__ == "__main__":
    test_refine_mesh()
