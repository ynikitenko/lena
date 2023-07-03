import copy
import pytest

import lena.core
import lena.context
from lena.core import LenaTypeError
from lena.flow import get_data
from lena.variables.variable import Combine, Compose, Variable


def test_combine():
    ## init and getitem work
    # must have arguments
    with pytest.raises(LenaTypeError):
        Combine()
    with pytest.raises(LenaTypeError):
        Combine("xy")
    with pytest.raises(LenaTypeError):
        Combine(lambda x: x)
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="coordinate", range=[0, 100])
    c = Combine(mm, name="xy")
    assert c[0] == mm

    # range creation works
    assert c.range == [mm.range]
    cm = Variable("cm", unit="cm", getter=lambda x: x, type="coordinate", range=[0, 10])
    c2 = Combine(mm, cm)
    assert c2.range == [mm.range, cm.range]
    # same explicitly
    assert c2.range == [[0, 100], [0, 10]]
    # has no range
    eV = Variable("cm", unit="cm", getter=lambda x: x, type="coordinate")
    c3 = Combine(mm, eV)
    with pytest.raises(lena.core.LenaAttributeError):
        c3.range

    ## __call__ works
    data = [1, 2, 3]
    results = map(c, data)
    assert [res[0] for res in results]  == [(10,), (20,), (30,)]
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="coordinate")
    m = Variable("m", unit="m", getter=lambda x: x/100., type="coordinate")
    c = Combine(mm, m)
    results = map(c, data)
    assert c.name == "mm_m"
    assert [res[0] for res in results]  == [(10,0.01), (20,0.02), (30,0.03)]
    # combination of Combines works
    c = Combine(mm, Combine(mm, m))
    results = [c(dt) for dt in data]
    assert [res[0] for res in results]  == [(10, (10, 0.01)), (20, (20, 0.02)), (30, (30, 0.03))]
    # context is fine
    rescont = results[0][1]
    assert rescont == {
        'variable': {
            'combine': (
                {'coordinate': 'mm',
                         'name': 'mm',
                         'type': 'coordinate',
                         'unit': 'mm'},
                {'combine': (
                    {'coordinate': 'mm',
                     'name': 'mm',
                     'type': 'coordinate',
                     'unit': 'mm'},
                    {'coordinate': 'm',
                     'name': 'm',
                     'type': 'coordinate',
                     'unit': 'm'}
                ),
                'dim': 2,
                'name': 'mm_m'}
            ),
            'dim': 2,
            'name': 'mm_mm_m'
        }
    }


def test_compose():
    ## test initialization
    with pytest.raises(LenaTypeError):
        # empty Compose is prohibited,
        # because it won't work in the Sequence.
        c = Compose()
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="coordinate")
    # getter can't be provided in kwargs
    with pytest.raises(LenaTypeError):
        c = Compose(mm, name="mm", getter=lambda x: x)
    c = Compose(mm, name="mm")
    assert c.name == "mm"
    positron = Variable("positron", getter=lambda x: x*10, type="particle")
    c = Compose(positron, mm)
    assert c.name == "positron_mm"
    # in this implementation c has latex_name.
    # with pytest.raises(AttributeError):
    # # with pytest.raises(lena.core.LenaAttributeError):
    #     c.latex_name
    assert c.latex_name == "mm_{positron}"
    x = Variable("x", unit="mm", getter=lambda coord: coord[0]*10,
                 latex_name="x", type="coordinate")
    positron = Variable("positron", getter=lambda event: event[0],
                        latex_name="e^+", type="particle")
    c = Compose(positron, x)
    assert c.name == "positron_x"
    assert c.latex_name == "x_{e^+}"
    # all args must be variables
    with pytest.raises(LenaTypeError):
        c = Compose(lambda x: x)
    # latex_name taken from kwargs
    c = Compose(positron, x, latex_name="x_{pos}")
    assert c.latex_name == "x_{pos}"
    reversed_join = lambda args: "_".join(reversed(args))
    c = Compose(positron, x, latex_name=reversed_join)
    assert c.latex_name == "x_e^+"
    with pytest.raises(lena.core.LenaAttributeError):
        c = Compose(positron, mm, latex_name=reversed_join)
    c = Compose(positron, x, name=reversed_join)
    assert c.name == "x_positron"

    ## test call
    data = [((1.05, 0.98, 0.8), (1.1, 1.1, 1.3))]
    assert c(data[0])[0] == 10.5
    # second time application gives the same
    assert c(data[0])[0] == 10.5
    res1 = {
        'variable': {
            'compose': {
                'latex_name': 'e^+',
                'name': 'positron',
                'particle': 'positron',
                'type': 'particle'
            },
            'coordinate': 'x',
            'latex_name': 'x_{e^+}',
            'name': 'x_positron',
            'particle': 'positron',
            'type': 'coordinate',
            'unit': 'mm'
        }
    }
    assert c(data[0])[1] == res1
    del x.var_context["type"]
    c = Compose(positron, x)
    assert "type" not in c(data[0])[1]["variable"]
    abs_ = Variable("abs", getter = abs)

    ## This test was done with a general idea,
    # but without much thought. Many tunings here
    # were made ad hoc. Rewrite that completely or remove.
    c1 = Compose(positron, Compose(x, abs_))
    del c1.var_context["latex_name"]
    # res1["variable"]["name"] = "positron_x"
    # del res1["variable"]["type"]
    # assert c(data[0])[1] == res1
    c2 = Compose(positron, x, abs_)
    res1 = c1(data[0])
    res2 = c2(data[0])
    # fix res1
    for update_str in [
        "variable.compose.compose.latex_name.e^+",
        "variable.compose.compose.name.positron",
        "variable.compose.compose.particle.positron",
        "variable.compose.compose.type.particle",
        # "variable.compose.type.particle",
        "variable.compose.latex_name.x",
        "variable.compose.name.x",
        ]:
        cont = lena.context.str_to_dict(update_str)
        lena.context.update_recursively(res1[1], cont)
    # fix res1 more
    del res1[1]["variable"]["compose"]["particle"]
    del res1[1]["variable"]["compose"]["type"]
    del res1[1]["variable"]["compose"]["compose"]["coordinate"]
    del res1[1]["variable"]["compose"]["compose"]["unit"]
    # fix res2
    del res2[1]["variable"]["compose"]["coordinate"]
    del res2[1]["variable"]["compose"]["unit"]
    # data is equal
    assert res1[0] == res2[0]
    # context is almost equal (mod previous fixes)
    assert res1[1] == res2[1]


def test_variable():
    ## test initialization
    # init works
    sq_m = Variable("sq_m", getter = lambda x: x*x, type="function")

    # repr works
    assert repr(sq_m) == "Variable(sq_m)"

    # getter=None raises
    with pytest.raises(LenaTypeError):
        sq_m = Variable("sq", getter=None, type="function")

    # not callable getter raises
    with pytest.raises(LenaTypeError):
        sq_m = Variable("sq", getter=5, type="function")

    # getter Variable raises
    with pytest.raises(LenaTypeError):
        Variable(sq_m, getter=sq_m)

    ## test actual work
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="length")
    sq_m = Variable("sq", getter = lambda x: x*x, type="function")

    data = [1, 2, 3]
    data = list(map(lambda v: (v, {str(v): v}), data))
    results = map(sq_m, copy.deepcopy(data))
    assert list(map(get_data, results)) == [1, 4, 9]
    assert sq_m.var_context == {'function': 'sq', 'name': 'sq', 'type': 'function'}
    assert sq_m(copy.deepcopy(data[0])) == (
        1, {
            '1': 1, 
            'variable': {
                'function': 'sq',
                'name': 'sq',
                'type': 'function'
            }
        }
    )

    # Compose works
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="length")
    square = Variable("square", type="area", getter=lambda x: x*x, unit="mm^2")
    sq_mm = Compose(mm, square)
    res1 = list(lena.core.Sequence(mm, square).run(copy.deepcopy(data)))[0]
    res2 = sq_mm(copy.deepcopy(copy.deepcopy(data[0])))
    res1[1]["variable"]["name"] = 'mm_square'
    res1[1]["variable"]["latex_name"] = 'square_{mm}'
    assert res1 == res2
    assert list(map(get_data, map(sq_mm, copy.deepcopy(data)))) == [100, 400, 900]
    assert sq_mm(copy.deepcopy(data[0])) == (
        100, {
            '1': 1, 
            'variable': {
                'length': 'mm', 
                'compose': {
                    'length': 'mm', 'type': 'length',
                    'name': 'mm', 'unit': 'mm'
                }, 
                'latex_name': 'square_{mm}',
                'name': 'mm_square',
                'area': 'square',
                'type': 'area', 'unit': 'mm^2'
            }
        }
    )

    # Combine works
    sq_m_mm = Combine(sq_m, sq_mm, name="sq_m_mm")
    assert list(map(get_data, map(sq_m_mm, copy.deepcopy(data)))) == [
        (1, 100), (4, 400), (9, 900)
    ]
    assert sq_m_mm(copy.deepcopy(data[0])) == (
        (1, 100), {
            '1': 1, 
            'variable': {
                'dim': 2, 'name': 'sq_m_mm',
                'combine': (sq_m.var_context, sq_mm.var_context)
            }
        }
    )


def test_getattr_and_var_context():
    x_mm = Variable("x", unit="mm", getter=lambda x: x*10, type="coordinate")
    y_mm = Variable("y", unit="mm", getter=lambda x: x*10, type="coordinate")

    # Variable attribute works
    assert x_mm.type == "coordinate"

    # getter should not be in var_context
    assert "getter" not in x_mm.var_context

    # Combine attribute works
    combine1 = Combine(x_mm, name="xy")
    assert combine1.name == "xy"

    xy_range = [(0,1), (0,1)]
    combine2 = Combine(x_mm, y_mm, name="xy", range=xy_range)
    assert combine2.range == xy_range

    # name and getter should not be in var_context
    assert "getter" not in combine1.var_context

    # Compose attribute works
    compose = Compose(x_mm, y_mm, name="xy", type="coordinate")
    assert compose.type == "coordinate"
    assert "getter" not in compose.var_context
