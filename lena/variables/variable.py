"""Variables are functions to transform data adding context.

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
>>> positron = Variable(
...    "positron", latex_name="e^+",
...    getter=lambda double_ev: double_ev[0], type="particle"
... )
>>> x_e = Compose(positron, x)
>>> x_e(data[0])[0]
1.05
>>> x_e(data[0])[1] == {
...    'variable': {
...        'name': 'x',
...        'coordinate': {'name': 'x'},
...        'type': 'coordinate',
...        'compose': ['particle', 'coordinate'],
...        'particle': {'name': 'positron', 'latex_name': 'e^+'}
...    }
... }
True

:class:`Combine` and :class:`Compose` are subclasses
of a :class:`Variable`.
"""
import copy
from copy import deepcopy

import lena.core
import lena.context
import lena.flow


class Variable(object):
    """Function of data with context."""

    def __init__(self, name, getter, type="", **kwargs):
        """*name* is variable's name.

        *getter* is a Python function (not a :class:`Variable`)
        that performs the actual transformation of data.
        It must accept data and return data without context.

        Other variable's attributes can be passed as keyword arguments.
        Examples include *latex_name*, *unit* (like *cm* or *keV*),
        *range*, etc.

        *type* is the type of the variable.
        It depends on your application, examples could be
        "coordinate" or "particle".
        It has a special meaning: if present,
        its value is added to variable's
        context as a key with the context of this variable
        (see the example for this module).
        It is recommended to set the type,
        otherwise variable's data will be lost after composition
        of variables.

        **Attributes**

        *getter*

        *var_context* is the dictionary of attributes of the variable.
        It is added to *context.variable* during :meth:`__call__`.

        All public attributes of a variable
        can be accessed using dot notation
        (for example, *var.var_context["latex_name"]*
        can be written as *var.latex_name*).
        :exc:`.AttributeError` is raised
        if an attribute is missing.

        If *getter* is a :class:`Variable` or is not callable,
        :exc:`.LenaTypeError` is raised.
        """
        self.name = name
        if isinstance(getter, Variable):
            raise lena.core.LenaTypeError(
                "getter should be a function on data, not a Variable "
                "{}".format(getter)
            )
        if not callable(getter):
            raise lena.core.LenaTypeError(
                "getter must callable, {} given".format(getter)
            )
        # getter is public for possible performance implementations
        # (without context)
        # But probably for unification with other "performance" features
        # its name may be changed in the future.
        self.getter = getter

        # var_context is public, so that one can get all attributes
        self.var_context = {
            "name": self.name,
        }
        self.var_context.update(**kwargs)
        if type:
            # to take less space in context; this is obvious.
            # self.var_context["type"] = type
            varc = self.var_context
            varc.update(
                {type: deepcopy(varc)}
            )
            # we store type in this variable context,
            # but not in its type subcontext.
            varc["type"] = type

    def __call__(self, value):
        """Transform a *value*.

        Data part of the value is transformed by *getter*.

        *context.variable* is updated with the context of this variable
        (or created if missing).
        If context already contained *variable*, it is preserved as
        *context.variable.compose* subcontext.
        """
        data, context = lena.flow.get_data_context(value)
        data = self.getter(data)
        # Run and Call elements don't make a deep copy of context.
        # update_context was made a separate function,
        # because it was supposed to be used in a different place
        # (like SplitIntoBins or IterateBins) - but not needed now.
        # Maybe _update_context call should be optimized out.
        # deep copy, because we don't know
        # whether users will have nested keys
        self._update_context(context, copy.deepcopy(self.var_context))
        return (data, context)

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

    # todo: is this function really needed? Shall we delete that?
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

    @staticmethod
    def _update_context(context, var_context):
        # this method is private, because its exact signature
        # is not clear at the moment. It could be a static,
        # maybe a class method or an instance method.
        # An instance method would be easiest to use (and
        # wouldn't need to copy var_context from somewhere)
        # however a static method would allow to update
        # contexts from their dictionaries (in the context)
        # - but is that really needed?..

        # no deep copy of var_context is made
        # (do it in user code if needed)
        cvar = context.get("variable")
        # preserve variable composition information if that is present
        composed = []
        if cvar and ("type" in cvar):
            # If cvar has no "type",
            # then no types were in the recent variable or earlier
            if "type" in var_context:
                cur_type = var_context["type"]
            else:
                cur_type = []
            if "compose" in cvar:
                assert isinstance(cvar["compose"], list)
            else:
                cvar["compose"] = [cvar["type"]]
            if "compose" in var_context:
                assert isinstance(var_context["compose"], list)
                cvar["compose"].extend(cur_type)
            else:
                if cur_type:
                    cvar["compose"].append(cur_type)
            composed = cvar["compose"]

        old_cvar = context.get("variable", {})
        context["variable"] = var_context
        cvar = context["variable"]
        if composed:
            # we need to overwrite it,
            # because current variable context has set it wrong
            context["variable"]["compose"] = composed
            # preserve old types, but nothing more.
            for type_ in composed:
                if type_ not in cvar and type_ in old_cvar:
                    cvar[type_] = old_cvar[type_]

        # could be useful as a chainable method,
        # but in general it doesn't return anything.
        # Django allows chaining (stackoverflow),
        # while Python supports command-query separation
        # https://en.wikipedia.org/wiki/Command%E2%80%93query_separation
        # return context

    def __repr__(self):
        # We don't print all options to save space.
        # Complete getter address is meaningless.
        # This is repr, one can always get these options
        # directly if needed.
        # We don't enclose name in quotes,
        # because this repr doesn't allow object creation.
        return """Variable({})""".format(self.name)


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
        containing each variable's context.

        **Attributes**:

        *dim* is the number of variables.

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
        # we don't preserve types of combined variables,
        # because they will take too much space in context (visually).
        # types = [var.var_context.get("type", None) for var in args]
        # type1 = types[0]
        # # preserve type it is same for all variables
        # if all((tp == type1 for tp in types[1:])):
        #     var_context["type"] = type1
        var_context.update(kwargs)
        assert "dim" not in kwargs  # to set it manually is meaningless
        var_context.update({"dim": self.dim})
        var_context["combine"] = tuple(
            copy.deepcopy(var.var_context) for var in self._vars
        )

        super(Combine, self).__init__(name=name, getter=getter, **var_context)

    def __getitem__(self, index):
        """Get variable at the given *index*."""
        return self._vars[index]


class Compose(Variable):
    """Composition of variables."""

    def __init__(self, *args, **kwargs):
        """*args* are the variables to be composed.

        A keyword argument *name* can set
        the name of the composed variable.
        If that is missing, it the name of the last variable is used.

        *context.variable.compose* contains contexts
        of the composed variables
        (the first composed variable is most nested).

        If there are no variables or if *kwargs* contains *getter*,
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

        # composition of functions must be almost the same
        # as those functions in a sequence.
        compose = {"variable": copy.deepcopy(self._vars[0].var_context)}

        for var in self._vars[1:]:
            varc = copy.deepcopy(var.var_context)
            Variable._update_context(compose, varc)

        var_context = compose["variable"]
        # otherwise *name* will be given twice in super.__init__
        # var_context.pop("name")

        if "name" in kwargs:
            name = kwargs.pop("name")
        else:
            name = self._vars[-1].name
            # name = "_".join(var.name for var in args)
        var_context.update(kwargs)

        super(Compose, self).__init__(
            name=name, getter=getter
        )
        # we can't set it in super.__init__,
        # since we've done all work here
        self.var_context = var_context
