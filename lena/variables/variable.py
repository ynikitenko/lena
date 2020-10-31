"""Variables are functions to transform data and add context.

A variable can represent a particle type, a coordinate, etc.
They transform raw input data into Lena data with context.
Variables have name and may have other attributes
like LaTeX name, dimension or unit.

Variables can be composed using :class:`Compose`,
which corresponds to function composition.

Variables can be combined into multidimensional variables
using :class:`Combine`.

Examples:

>>> from lena.variables import Variable, Compose
>>> # data is pairs of (positron, neutron) coordinates
>>> data = [((1.05, 0.98, 0.8), (1.1, 1.1, 1.3))]
>>> x = Variable(
...    "x", lambda coord: coord[0], type="coordinate"
... )
>>> neutron = Variable(
...    "neutron", latex_name="n",
...    getter=lambda double_ev: double_ev[1], type="particle"
... )
>>> x_n = Compose(neutron, x)
>>> x_n(data[0])[0]
1.1
>>> x_n(data[0])[1] == {
...     'variable': {
...         'name': 'neutron_x', 'particle': 'neutron',
...         'latex_name': 'x_{n}', 'coordinate': 'x', 'type': 'coordinate',
...         'compose': {
...             'type': 'particle', 'latex_name': 'n',
...             'name': 'neutron', 'particle': 'neutron'
...         },
...     }
... }
True

:class:`Combine` and :class:`Compose` are subclasses
of a :class:`Variable`.
"""
from __future__ import print_function

import copy

import lena.core
import lena.context
import lena.flow


class Variable(object):
    """Function of data with context."""

    def __init__(self, name, getter, **kwargs):
        """*name* is variable's name.

        *getter* is the python function (not a :class:`Variable`)
        that performs the actual transformation of data.
        It must accept data and return data without context.

        Other variable's attributes can be passed as keyword arguments.
        Examples include *latex_name*, *unit* (like *cm* or *keV*),
        *range*, etc.

        *type* is the type of the variable.
        It depends on your application, examples are
        'coordinate' or 'particle_type'.
        It has a special meaning: if present,
        its value is added to variable's
        context as a key with variable's name
        (see example for this module).
        Thus variable type's data is preserved during composition
        of different types.

        **Attributes**

        *getter* is the function
        that does the actual data transformation.

        *var_context* is the dictionary of attributes of the variable,
        which is added to *context.variable* during :meth:`__call__`.

        ..
            and used during variable transformations (see :ref:`functions`).

        All public attributes of a variable
        can be accessed using dot notation
        (for example, *var.var_context["latex_name"]*
        can be simply *var.latex_name*).
        :exc:`.AttributeError` is raised
        if the attribute is missing.

        If *getter* is a :class:`Variable` or is not callable,
        :exc:`.LenaTypeError` is raised.
        """
        self.name = name
        if isinstance(getter, Variable):
            raise lena.core.LenaTypeError(
                "getter should be a function on data, not a Variable. " +
                "Got {}.".format(getter)
            )
        if not callable(getter):
            raise lena.core.LenaTypeError(
                "a callable getter must be provided, {} given".format(getter)
            )
        # getter is public for possible performance implementations
        # (without context)
        self.getter = getter

        # var_context is public, so that one can get all attributes
        self.var_context = {
            "name": self.name,
        }
        if "type" in kwargs:
            self.var_context.update({kwargs["type"]: self.name})
        self.var_context.update(**kwargs)

    def __call__(self, value):
        """Transform a *value*.

        Data part of the value is transformed by the *getter*.
        *Context.variable* is updated with the context of this variable
        (or created if missing).

        If context already contained *variable*, it is preserved as
        *context.variable.compose* subcontext.

        Return *(data, context)*.
        """
        data, context = lena.flow.get_data_context(value)
        # Run (and Call) elements don't make deep copy.
        # context = copy.deepcopy(context)
        var_context = context.get("variable")
        if var_context:
            # deep copy, otherwise it will be updated during update_recursively
            context["variable"]["compose"] = copy.deepcopy(var_context)
        # update recursively, because we need to preserve "type"
        # and other not overwritten data
        lena.context.update_recursively(
            context, {"variable": copy.deepcopy(self.var_context)}
        )
        new_data = self.getter(data)
        return (new_data, context)

    def __getattr__(self, name):
        # otherwise infinite recursion (solved by this answer):
        # The __setstate__ method copy.copy() is looking for is optional,
        # and your class indeed has no such attribute.
        # https://stackoverflow.com/a/34950256/952234
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            return self.var_context[name]
        except KeyError:
            raise lena.core.LenaAttributeError(
                "{} missing in {}".format(name, self.name)
            )

    def get(self, key, default=None):
        """Return the attribute *key* if present, else default.

        *key* can be a dot-separated string, a list or a dictionary
        (see :func:`context.get_recursively <.get_recursively>`).

        If default is not given, it defaults to ``None``,
        so that this method never raises a :exc:`KeyError`.
        """
        return lena.context.get_recursively(
            self.var_context, key, default=default
        )


class Combine(Variable):
    r"""Combine variables into a tuple.

    :class:`Combine`\ *(var1, var2, ...)(value)*
    is *((var1.getter(value), var2.getter(value), ...), context)*.
    """

    def __init__(self, *args, **kwargs):
        r"""*args* are the variables to be combined.

        Keyword arguments are passed to :class:`Variable`'s __init__.
        For example, *name* is the name of the combined variable.
        If not provided, it is its variables' names joined with '_'.

        *context.variable* is updated with *combine*, which is a tuple
        of each variable's context.

        **Attributes**:

        *dim* is the number of variables.

        *range*. If all variables have an attribute *range*,
        the *range* of this variable is set to a list of them.

        All *args* must be *Variables*
        and there must be at least one of them,
        otherwise :class:`LenaTypeError` is raised.
        """
        # set _vars, dim and getter.
        if not args:
            raise lena.core.LenaTypeError(
                "Combine must be initialized with 1 or more variables"
            )
        all_vars = all((isinstance(arg, Variable) for arg in args))
        if not all_vars:
            raise lena.core.LenaTypeError(
                "All arguments to be combined must be Variables, "
                "{} provided".format(args)
            )
        self._vars = args
        self.dim = len(args)
        getter = lambda val: tuple(var.getter(val) for var in self._vars)

        # update var_context with name and kwargs.
        name = kwargs.pop("name", None)
        if name is None:
            name = "_".join([var.name for var in self._vars])
        var_context = {}
        var_context.update(kwargs)
        assert "dim" not in kwargs  # to set it manually is meaningless
        var_context.update({"dim": self.dim})
        var_context["combine"] = tuple(
            copy.deepcopy(var.var_context) for var in self._vars
        )

        # set range of the combined variables
        if all(hasattr(var, "range") for var in self._vars):
            range_ = [var.range for var in self._vars]
            var_context["range"] = range_

        super(Combine, self).__init__(name=name, getter=getter, **var_context)

    def __getitem__(self, index):
        """Get variable at the given *index*."""
        return self._vars[index]


class Compose(Variable):
    """Composition of variables."""

    def __init__(self, *args, **kwargs):
        """*args* are the variables to be composed.

        Keyword arguments:

        *name* is the name of the composed variable.
        If that is missing, it is composed from variables
        names joined with underscore.

        *latex_name* is LaTeX name of the composed variable.
        If that is missing and if there are only two variables,
        it is composed from variables' names
        (or their LaTeX names if present)
        as a subscript in the reverse order *(latex2_{latex1})*.

        *context.variable.compose* contains contexts
        of the composed variables
        (the first composed variable is most nested).

        If any keyword argument is a callable,
        it is used to create the corresponding variable attribute.
        In this case, all variables must have this attribute,
        and the callable is applied to the list of these attributes.
        If any attribute is missing,
        :exc:`.LenaAttributeError` is raised.
        This can be used to create composed attributes
        other than *latex_name*.

        If there are no variables or if *kwargs* contain *getter*,
        :exc:`.LenaTypeError` is raised.
        """
        if not all(isinstance(arg, Variable) for arg in args):
            raise lena.core.LenaTypeError(
                "All arguments to be composed must be Variables, "
                "{} provided".format(args)
            )
        if not args:
            raise lena.core.LenaTypeError(
                "at least one variable must be provided"
            )
        if "getter" in kwargs:
            raise lena.core.LenaTypeError(
                "getter must not be provided"
            )
        def getter(value):
            for var in self._vars:
                value = var.getter(value)
            return value
        self._vars = args
        if "latex_name" not in kwargs and len(args) == 2:
            latex_name_1 = args[0].get("latex_name", args[0].name)
            latex_name_2 = args[1].get("latex_name", args[1].name)
            if latex_name_1 and latex_name_2:
                latex_name = "{}_{{{}}}".format(latex_name_2, latex_name_1)
                kwargs["latex_name"] = latex_name
        for kw in kwargs:
            kwarg = kwargs[kw]
            if callable(kwarg):
                try:
                    var_args = [getattr(var, kw) for var in args]
                except AttributeError:
                    raise lena.core.LenaAttributeError(
                        "all variables must contain {}, ".format(kw) +
                        "{} given".format(args)
                    )
                else:
                    kwargs[kw] = kwarg(var_args)

        # composition of functions must be almost the same
        # as those functions in a sequence.
        # The only difference seems to be that only type is copied here,
        # and in Variable.__call__ other keys are copied as well
        compose = copy.deepcopy(self._vars[0].var_context)
        # def get_lowest_compose(d):
        #     while True:
        #         if isinstance(d, dict) and "compose" in d:
        #             d = d["compose"]
        #         else:
        #             return d
        def collect_types(d):
            types = {}
            def collect_type_this_level(d):
                if "type" in d and d["type"] in d:
                    return {d["type"]: d[d["type"]]}
                else:
                    return {}
            composes = [d]
            while "compose" in d:
                d = d["compose"]
                composes.append(d)
            for d in reversed(composes):
                types.update(collect_type_this_level(d))
            return types
        for var in self._vars[1:]:
            varc = copy.deepcopy(var.var_context)
            lena.context.update_nested(varc, {"compose": compose})
            # get_lowest_compose(varc).update({"compose": compose})
            compose = varc
        # one Composed variable must be same as a simple variable
        var_context = compose
        types = collect_types(var_context)
        var_context.update(types)
        var_context.pop("name")

        if "name" in kwargs:
            name = kwargs.pop("name")
        else:
            name = "_".join(var.name for var in args)
        var_context.update(kwargs)

        super(Compose, self).__init__(
            name=name, getter=getter, **var_context
        )
