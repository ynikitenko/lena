# requires jinja2
import copy
import re

import lena.core
import lena.context
import lena.flow


_sentinel = object()


class UpdateContext():
    """Update context of passing values."""

    def __init__(self, subcontext, update, value=False, default=_sentinel,
                 skip_on_missing=False, raise_on_missing=False,
                 recursively=True):
        """*subcontext* is a string representing the part of context
        to be updated (for example, *"output.plot"*).
        *subcontext* must be non-empty.

        *update* will become the value of *subcontext*
        during :meth:`__call__`.
        It can be one of three different types:

            - a simple value (not a string),
            - a context formatting string,
            - a context value (a string in curly braces).

        A context formatting string is any string
        with arguments enclosed in double braces
        (for example, *"{{variable.type}}_{{variable.name}}"*).
        Its argument values will be filled from context
        during :meth:`__call__`.
        If a formatting argument is missing in context, it will be
        substituted with an empty string.

        To set *update* to a value from context (not a string),
        the keyword argument *value* must be set to ``True``
        and the *update* format string must be
        a non-empty single expression in double braces
        (*"{{variable.compose}}"*).

        If *update* corresponds to a context value and
        a formatting argument is missing in the context,
        :exc:`.LenaKeyError` will be raised unless a *default* is set.
        In this case *default* will be used for the update value.

        If *update* is a context formatting string, *default*
        keyword argument can't be used.
        To set a default value other than an empty string,
        use a jinja2 filter. For example, if
        *update* is *"{{variable.name|default('x')}}"*, then *update*
        will be set to "x" both if *context.variable.name* is missing
        and if *context.variable* is missing itself.

        Other variants to deal with missing context values are:

            - to skip update (don't change the context),
              set by *skip_on_missing*, or
            - to raise :exc:`.LenaKeyError` (set by *raise_on_missing*).

        Only one of *default*, *skip_on_missing* or *raise_on_missing*
        can be set, otherwise :exc:`.LenaValueError` is raised.
        None of these options can be used if *update* is a simple value.

        If *recursively* is ``True`` (default), not overwritten
        existing values of *subcontext* are preserved.
        Otherwise, all existing values of *subcontext* (at its lowest level)
        are removed.
        See also :func:`.update_recursively`.

        Example:

        >>> from lena.context import UpdateContext
        >>> make_scatter = UpdateContext("output.plot", {"scatter": True})
        >>> # call directly
        >>> make_scatter(((0, 0), {}))
        ((0, 0), {'output': {'plot': {'scatter': True}}})
        >>> # or use in a sequence

        If *subcontext* is not a string, :exc:`.LenaTypeError` is raised.
        If it is empty, :exc:`.LenaValueError` is raised.
        If *value* is ``True``, braces can be only the first two
        and the last two symbols of *update*,
        otherwise :exc:`.LenaValueError` is raised.
        """
        import jinja2
        # The "Context" in the class name means any general context
        # (not only :class:`.Context`).

        # subcontext is a string, because it must have at most one value
        # at each nesting level.
        if not isinstance(subcontext, str):
            raise lena.core.LenaTypeError(
                "subcontext must be a string, {} provided".format(subcontext)
            )
        if not subcontext:
            raise lena.core.LenaValueError(
                "subcontext must be non-empty"
            )
        self._subcontext = lena.context.str_to_list(subcontext)

        self._has_default = default is not _sentinel
        n_of_active = (
            int(self._has_default) + int(raise_on_missing)
            + int(skip_on_missing)
        )
        if n_of_active > 1:
            raise lena.core.LenaValueError(
                "only one of skip_on_missing, raise_on_missing "
                "or default must be active"
            )
        self._skip_on_missing = skip_on_missing
        self._raise_on_missing = raise_on_missing

        value = bool(value)
        if not isinstance(update, str):
            # simple update
            self._update = update
            if n_of_active:
                raise lena.core.LenaValueError(
                    "for simple update skip_on_missing, default "
                    "and raise_on_missing must not be set"
                )
        elif value and re.match('{{[^{}]+}}$', update):
            # context value update
            # {{at least one symbol in between, no { or } in between}}
            self._context_value = True
            self._update = update[2:-2]
            if not self._has_default and not self._skip_on_missing:
                self._raise_on_missing = True
        else:
            # context format update
            if value:
                raise lena.core.LenaValueError(
                    "fix braces for template string '{}' or set value to False"
                    .format(update)
                )
            self._context_value = False
            if self._has_default:
                raise lena.core.LenaValueError(
                    "default for a formatting string must be set inside it"
                )
            try:
                if raise_on_missing or skip_on_missing:
                    self._update = jinja2.Template(
                        update, undefined=jinja2.StrictUndefined
                    )
                else:
                    # ChainableUndefined appeared in jinja2 2.11.0
                    self._update = jinja2.Template(
                        update, undefined=jinja2.ChainableUndefined
                    )
            except jinja2.exceptions.TemplateSyntaxError as err:
                raise lena.core.LenaValueError(
                    "template syntax error, {}".format(err.message)
                )
        self._value = value
        self._default = default
        self._recursively = bool(recursively)

    def __call__(self, value):
        """Update *value*'s context.

        If the *value* is updated,
        *subcontext* is always created
        (also if the *value* contains no context).

        :exc:`.LenaKeyError` is raised if
        *raise_on_missing* is ``True`` and
        the update argument is missing in *value*'s context.
        """
        import jinja2
        data, context = lena.flow.get_data_context(value)
        if isinstance(self._update, (str, jinja2.Template)):
            if self._context_value:
                if not self._has_default:
                    try:
                        update = lena.context.get_recursively(context,
                                                              self._update)
                    except lena.core.LenaKeyError as err:
                        if self._skip_on_missing:
                            return value
                        else:
                            assert self._raise_on_missing
                            raise err
                else:
                    update = lena.context.get_recursively(
                        context, self._update, self._default
                    )
                    assert not self._raise_on_missing
                    assert not self._skip_on_missing
                update = copy.deepcopy(update)
            else:
                # context format update
                try:
                    update = self._update.render(context)
                except jinja2.exceptions.UndefinedError as err:
                    if self._raise_on_missing:
                        raise lena.core.LenaKeyError(
                            "{}, context={}".format(err.message, context)
                        )
                    else:
                        # todo: any better way to check it?
                        assert self._skip_on_missing
                        return value
        else:
            update = copy.deepcopy(self._update)
        # now empty context is prohibited.
        # May be skipped in runtime in the future.
        assert self._subcontext
        keys = self._subcontext
        subdict = context
        for key in keys[:-1]:
            if key not in subdict or not isinstance(subdict[key], dict):
                subdict[key] = {}
            subdict = subdict[key]
        if self._recursively:
            lena.context.update_recursively(subdict, {keys[-1]: update})
        else:
            subdict[keys[-1]] = update
        return (data, context)
