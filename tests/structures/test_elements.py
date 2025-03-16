import collections
import copy
import pytest

import lena.structures
from lena.core import LenaValueError
from lena.math import mesh
from lena.structures import histogram, graph
from lena.variables import Variable
from lena.structures import HistToGraph, hist_to_graph, ScaleTo


def test_hist_to_graph():
    hist = histogram(mesh((0, 1), 1))
    hist.fill(0)
    context_no_transform = {"histogram": {"to_graph": False}}
    data = [
        0,
        copy.deepcopy(hist),
        (copy.deepcopy(hist), {}),
        (copy.deepcopy(hist), context_no_transform),
    ]
    nevents = Variable("nevents", lambda nevents: nevents)
    htg = HistToGraph(nevents)
    nev_context = {'value': {'variable': {'name': 'nevents'}}}
    gr = graph([[0], [1]])

    # run works correctly
    assert list(htg.run(data)) == [
        0,
        (gr, nev_context),
        (gr, nev_context),
        # values with the specified context are skipped
        (histogram([0, 1], bins=[1]),
         {'histogram': {'to_graph': False}}
        ),
    ]

    # different coordinates work
    assert list(HistToGraph(nevents, get_coordinate="right").run([hist])) == \
        [(graph([[1], [1]], scale=None), nev_context)]
    assert list(HistToGraph(nevents, get_coordinate="middle").run([hist])) == \
        [(graph([[0.5], [1]], scale=None), nev_context)]

    val_with_error = collections.namedtuple("val_with_error",
                                            ["value", "error"])
    hist1 = histogram(mesh((0, 1), 1))
    val = val_with_error(1, 2)
    hist1.bins = lena.structures.init_bins(hist1.edges, val)
    transform_value = Variable("value_error",
                               lambda val: (val.value, val.error))
    assert list(
        HistToGraph(
            make_value=transform_value, field_names=("x", "y", "z")
        ).run([hist1])
    ) == \
        [(graph([[0], [1], [2]], field_names="x,y,z"),
          {'value': {'variable': {'name': 'value_error'}}})]

    # wrong make_value raises
    with pytest.raises(lena.core.LenaTypeError):
        HistToGraph(lambda x: x, get_coordinate="left")

    # wrong coordinate raises LenaValueError in HistToGraph
    with pytest.raises(lena.core.LenaValueError):
        HistToGraph(nevents, get_coordinate="left_right")

    # same raises in hist_to_graph
    with pytest.raises(lena.core.LenaValueError):
        hist_to_graph(hist1, get_coordinate="left_right")

    # hist_to_graph works for 1-dimensional histograms
    assert hist_to_graph(histogram([0, 1], bins=[1])) == graph([[0], [1]])

    # scale works
    # True == 1 in Python, so better to test scale 2.
    assert hist_to_graph(histogram([0, 1], bins=[2]), scale=True) \
            == graph([[0], [2]], scale=2)

    # 2-dimensional histograms work
    hist2 = histogram(mesh(((0, 1), (0, 1)), (1, 1)), bins=[[2]])
    assert hist_to_graph(hist2, scale=True, field_names="x,y,z") \
            == graph([[0], [0], [2]], scale=2, field_names="x,y,z")


def test_scale_to():
    scale = 1.
    seq = lena.core.Sequence(
        ScaleTo(1.)
    )
    hist1 = histogram([0, 1], bins=[2])
    context1 = {}
    res = list(seq.run([(hist1, context1)]))
    assert len(res) == 1
    data, context = res[0]
    assert context == context1
    assert data.scale() == scale
