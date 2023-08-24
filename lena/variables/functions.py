"""Functions transform variables into variables.

This module contains example implementations of functions.

Warning
-------
    This module seems to be not very sound or developed.
    Don't rely on it, because it may change.
"""
from __future__ import print_function

import copy  

import lena.variables
import lena.core 
abs_ = abs


def abs(var, name=None, latex_name=None):
    r"""Absolute value of a variable.

    :func:`abs`\ (*var*) is the absolute value of a variable *var*,
    its name is by default prepended with "abs\_"
    and latex name is surrounded by '|'.

    *name*, if given, is the name of the resulting variable.

    If *latex_name* is not given,
    it is *var.latex_name* (or *var.name* if that is missing)
    surrounded by '|' symbols.

    Example: 

    >>> # pairs of (x, y) coordinates
    >>> data = [(0, 1), (-1, 1)]
    >>> x = lena.variables.Variable(name='x', getter=lambda data: data[0],
    ...        type='coordinate')
    >>> list(map(x, data))[1] == (
    ...    -1,
    ...    {'variable': 
    ...        {'coordinate': {'name': 'x'},
    ...         'name': 'x',
    ...         'type': 'coordinate'}
    ...    }
    ... )
    True
    """
    # originally it was called abs_,
    # but there were problems with automatic documentation (autosummary)
    if name is None:
        name = "abs_" + var.name
    if latex_name is None:
        var_latex_name = var.get("latex_name", var.name)
        latex_name = '|' + var_latex_name + '|'
    getter = lambda val: abs_(var.getter(val))
    # getter = lambda val: __builtins__["abs"](var.getter(val))
    var_context = copy.deepcopy(var.var_context)
    var_context.update(name=name, latex_name=latex_name, getter=getter)
    # type is explicitly provided here as kwargs
    return lena.variables.Variable(**var_context)


def Cm(var):
    """Convert variable *var* from meters and millimeters to centimeters.

    Warning
    -------
    This function is likely to be changed. 
    Probably call it convert_scale(var, scale).
    To make a new variable instead of patching the old one
    is more functional.

    If variable unit is not set,
    :class:`LenaValueError` is raised.

    Note that this is a function returning a new variable,
    it's not a class.
    """
    var = copy.deepcopy(var)
    unit = var.get("unit")
    if not unit:
        raise lena.core.LenaValueError("in order to use Cm, "
                             + "the variable must have set its unit.")
    if unit == "cm":
        return var
    if unit == "m":
        getter = lambda val: val * 100
    elif unit == "mm":
        getter = lambda val: val / 10.
    else:
        raise lena.core.LenaValueError(
            "unknown unit {}. Can't convert to cm.".format(unit)
        )
    var.unit = "cm"
    var.var_context["unit"] = "cm"
    # otherwise infinite recursion
    old_getter = var.getter
    var.getter = lambda val: getter(old_getter(val))
    return var
