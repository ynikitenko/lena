import pytest

import lena.core
from lena.structures import graph, root_graph_errors, ROOTGraphErrors


def test_root_graph_errors():
    # no errors
    gr0 = graph([[0, 1, 2], [2, 3, 4]])
    rgr0 = root_graph_errors(gr0)
    assert list(rgr0) == [(0, 2), (1, 3), (2, 4)]
    assert len(rgr0) == 3
    context0 = {}
    rgr0._update_context(context0)
    assert context0 == {}

    # x error
    gr1 = graph([[0, 1], [2, 3], [0.1, 0.1]], field_names="x,y,error_x")
    rgr1 = root_graph_errors(gr1)
    assert list(rgr1) == [(0, 2, 0.1), (1, 3, 0.1)]
    assert len(rgr1) == 2
    context1 = {}
    rgr1._update_context(context1)
    assert context1 == {"error": {"x": {"index": 2}}}

    # x and y errors
    gr2 = graph([[0, 1], [2, 3], [0.1, 0.1], [0.2, 0.2]],
                field_names="x,y,error_x,error_y")
    rgr2 = root_graph_errors(gr2)

    assert list(rgr2) == [(0, 2, 0.1, 0.2), (1, 3, 0.1, 0.2)]
    assert len(rgr2) == 2
    context2 = {}
    rgr2._update_context(context2)
    assert context2 == {
        "error": {
            "x": {"index": 2},
            "y": {"index": 3}
        }
    }

    # test comparison
    # different errors give different graphs
    coords = [[0, 1], [2, 3], [0.1, 0.1]]
    grx = graph(coords, field_names="x,y,error_x")
    gry = graph(coords, field_names="x,y,error_y")
    rgrx = root_graph_errors(grx)
    rgry = root_graph_errors(gry)
    # no, no idea why this is not covered in Python 2...
    assert rgrx != rgry
    # not root_graph_errors returns False
    assert rgrx != coords

    # error suffixes are not allowed
    gre = graph(coords, field_names="x,y,error_x_low")
    with pytest.raises(lena.core.LenaValueError):
        root_graph_errors(gre)

    # only 2-dimensional graphs are allowed
    gr3d = graph(coords, field_names="x,y,z")
    with pytest.raises(lena.core.LenaValueError):
        root_graph_errors(gr3d)


def test_ROOTGraphErrors():
    el = ROOTGraphErrors()
    gr = graph([[0, 1], [1, 2]])
    rgr = root_graph_errors(gr)
    assert el(gr) == (rgr, {})
