import copy
import pytest

import lena.core
import lena.context
from lena.core import LenaTypeError, Sequence
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
    # assert c.range == [mm.range]
    cm = Variable("cm", unit="cm", getter=lambda x: x, type="coordinate", range=[0, 10])
    c2 = Combine(mm, cm)
    # assert c2.range == [mm.range, cm.range]
    # same explicitly
    # assert c2.range == [[0, 100], [0, 10]]
    # has no range
    eV = Variable("cm", unit="cm", getter=lambda x: x, type="coordinate")
    c3 = Combine(mm, eV)
    # missing attribute raises
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
                {
                    'coordinate': {'name': 'mm', 'unit': 'mm'},
                    'name': 'mm',
                    'type': 'coordinate',
                    'unit': 'mm'
                },
                {
                    'combine': (
                        {
                            'coordinate': {'name': 'mm',
                                           'unit': 'mm'},
                            'name': 'mm',
                            'type': 'coordinate',
                            'unit': 'mm'
                        },
                        {
                            'coordinate': {'name': 'm',
                                            'unit': 'm'},
                            'name': 'm',
                            'type': 'coordinate',
                            'unit': 'm'
                        }
                    ),
                    'dim': 2,
                    'name': 'mm_m'
                }
            ),
            'dim': 2,
            'name': 'mm_mm_m'
        }
    }

    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="length")
    square = Variable("square", type="area", getter=lambda x: x*x, unit="mm^2")
    sq_m = Variable("sq_m", getter = lambda x: x*x, type="function")
    sq_mm = Compose(mm, square)
    sq_m_mm = Combine(sq_m, sq_mm, name="sq_m_mm")
    assert list(map(get_data, map(sq_m_mm, copy.deepcopy(data)))) == [
        (1, 100), (4, 400), (9, 900)
    ]
    res = sq_m_mm(copy.deepcopy(data[0]))
    assert res[0] == (1, 100)
    assert res[1] == {
        'variable': {
            'dim': 2,
            'name': 'sq_m_mm',
            'combine': (sq_m.var_context, sq_mm.var_context)
        }
    }


def test_compose():
    data = [((1.05, 0.98, 0.8), (1.1, 1.1, 1.3))]
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
    # actually it is stupid to name a variable "mm".
    assert c.name == "mm"
    # no more hard-coded LaTeX names.
    with pytest.raises(lena.core.LenaAttributeError):
        c.latex_name
    x = Variable("x", unit="mm", getter=lambda coord: coord[0]*10,
                 type="coordinate")
    positron = Variable("positron", getter=lambda event: event[0],
                        latex_name="e^+", type="particle")
    res = list(Sequence(positron, x).run(data))[0]
    seq_res = (
        10.5,
        {'variable': {'coordinate': {'name': 'x',
                                     'unit': 'mm'},
                      'compose': ['particle', 'coordinate'],
                      'name': 'x',
                      'particle': {'latex_name': 'e^+',
                                   'name': 'positron'},
                      'type': 'coordinate',
                      'unit': 'mm'}},
    )
    assert res == seq_res
    c = Compose(positron, x)
    assert c.name == "x"
    # sequence and Compose produce same results
    assert c(data[0]) == seq_res
    print(c.var_context)
    assert c.compose == ["particle", "coordinate"]
    # all args must be variables
    with pytest.raises(LenaTypeError):
        c = Compose(lambda x: x)
    # latex_name taken from kwargs
    c = Compose(positron, x, latex_name="x_{pos}")
    assert c.latex_name == "x_{pos}"

    # omg, how could it be...
    reversed_join = lambda args: "_".join(reversed(args))
    c = Compose(positron, x, latex_name=reversed_join)
    # meaningless, but why not to check?..
    assert c.latex_name == reversed_join
    # this logic is too complicated. I even forgot about that.
    # This should not work, also because
    # 1) it's different in sequences.
    #    It's hard to maintain this logic then.
    # 2) it's really easy to implement having all variables at hand.
    # 3) the future is in self creation
    #    (in MakeFilename or jinja filters).
    # assert c.latex_name == "x_e^+"

    ## test call
    c = Compose(positron, x)
    assert c(data[0])[0] == 10.5
    # second time application gives the same
    assert c(data[0])[0] == 10.5
    res1 = {
        'variable': {
            'compose': ['particle', 'coordinate'],
            'coordinate': {
                'name': 'x',
                'unit': 'mm'
            },
            'particle': {
                'name': 'positron',
                'latex_name': 'e^+',
            },
            'name': 'x',
            'type': 'coordinate',
            'unit': 'mm'
        }
    }
    assert c(data[0])[1] == res1
    del x.var_context["type"]
    c = Compose(positron, x)
    assert "type" not in c(data[0])[1]["variable"]

    data = [1, 2, 3]
    # Compose works same as composition in a sequence
    mm = Variable("mm", unit="mm", getter=lambda x: x*10, type="length")
    square = Variable("square", type="area", getter=lambda x: x*x, unit="mm^2")
    sq_mm = Compose(mm, square)
    res1 = list(lena.core.Sequence(mm, square).run(copy.deepcopy(data)))[0]
    res2 = sq_mm(copy.deepcopy(data[0]))
    # res1[1]["variable"]["name"] = 'mm_square'
    # res1[1]["variable"]["latex_name"] = 'square_{mm}'
    # assert res1 == res2
    assert list(map(get_data, map(sq_mm, copy.deepcopy(data)))) == [100, 400, 900]
    assert sq_mm(copy.deepcopy(data[0])) == (
        100, {
            'variable': {
                'length': {'name': 'mm', 'unit': 'mm'},
                'compose': ['length', 'area'],
                'name': 'square',
                'area': {'name': 'square', 'unit': 'mm^2'},
                'type': 'area',
                'unit': 'mm^2'
            }
        }
    )


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
    assert sq_m.var_context == {
        'function': {
            'name': 'sq',
            # 'type': 'function'
        },
        'name': 'sq',
        'type': 'function'
    }
    assert sq_m(copy.deepcopy(data[0])) == (
        1, {'1': 1,
            'variable': sq_m.var_context}
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
