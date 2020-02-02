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

from lena.math import refine_mesh, mesh


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
