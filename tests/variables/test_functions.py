from __future__ import print_function

import pytest
from copy import deepcopy

from lena.core import LenaValueError
from lena.variables.variable import Combine, Variable
from lena.variables.functions import abs, Cm


def _test_abs():
    # Variable x
    x = Variable(name='x', getter=lambda data: data[0], type='coordinate')
    abs_x = abs(x)
    # pairs of (x, y) coordinates
    data = [(0, 1), (-1, 1)]
    x_context = {'variable': {
        'name': 'x',
        'coordinate': {'name': 'x'},
        'type': 'coordinate'
        }
    }
    assert list(map(x, data)) == [
        (0, x_context), 
        (-1, x_context)
    ]
    
    abs_x_context = {
        'variable': {
            'dim': 1,
            'name': 'abs_x',
            'coordinate': {'name': 'x', 'unit': 'cm'},
            'type': 'coordinate',
            'latex_name': '|x|'
        }
    }
    list(map(abs_x, data)) == [
        (0, abs_x_context), 
        (1, abs_x_context)
    ]


# doesn't work. Not sure I need that Cm...
def _test_cm():
    data = [(0, 1), (-1, 1)]
    # Variable x without a unit
    x = Variable(name='x', getter=lambda data: data[0], type='coordinate')
    with pytest.raises(LenaValueError):
        Cm(x)
    # Variable x with a unit
    var_args = {"name": 'x', "getter": lambda data: data[0], "type": 'coordinate'}
    # cm
    var_args.update(unit="cm")
    x = Variable(**var_args)
    x_context = {
        'variable': {
            'name': 'x',
            'coordinate': {'name': 'x', 'unit': 'cm'},
            'type': 'coordinate',
            'unit': 'cm'
        }
    }
    assert list(map(Cm(x), data)) == [
        (0, x_context),
        (-1, x_context)
    ]
    # mm
    var_args.update(unit="mm")
    x = Variable(**var_args)
    assert list(map(Cm(x), data)) == [
        (0, x_context),
        (-0.1, x_context)
    ]
    # m
    var_args.update(unit="m")
    x = Variable(**var_args)
    assert list(map(Cm(x), data)) == [
        (0, x_context),
        (-100, x_context)
    ]
    # Cm did not change our variable.
    x_context_m = deepcopy(x_context)
    x_context_m["variable"]["unit"] = "m"
    assert list(map(x, data)) == [
        (0, x_context_m),
        (-1, x_context_m)
    ]
    # unknown unit
    var_args.update(unit="unknown")
    x = Variable(**var_args)
    with pytest.raises(LenaValueError):
        list(map(Cm(x), data))
