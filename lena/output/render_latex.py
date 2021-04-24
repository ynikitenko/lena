"""Create LaTeX text from templates and data."""
from __future__ import print_function

import jinja2

import lena.core
import lena.flow
import lena.context
from lena.context import get_recursively as _get_recursively


_ljinja_env = {
        "block_start_string": r'\BLOCK{',
        "block_end_string": '}',
        "variable_start_string": r'\VAR{',
        "variable_end_string": '}',
        "comment_start_string": r'\#{',
        "comment_end_string": '}',
        "line_statement_prefix": '%-',
        "line_comment_prefix": '%#',
        "trim_blocks": True,
        "lstrip_blocks": True,
        "autoescape": False,
}


class _Template(jinja2.Template):
    # this class is not used. Environment is used.
    """Adapt jijna2 template to LaTeX.

    Working with not completely rendered environments may be a problem. 
    For example, undefined variable's attributes are not processed correctly,
    https://github.com/pallets/jinja/issues/811
    New class was suggested to be written for that.
    """

    def __new__(cls, *args, **jkws):
        # Jinja Template uses not __init__(), but __new__().
        kws = jkws.copy()
        kws.update(_ljinja_env)
        # how to efficiently merge two dicts: https://stackoverflow.com/a/26853961/952234
        # print kws
        sucls = super(_Template, cls)
        return sucls.__new__(sucls, *args, **kws)


class _Environment(jinja2.Environment):
    """Jinja environment."""

    def __init__(self, *args, **jkws):
        kws = jkws.copy()
        kws.update(_ljinja_env)
        super(_Environment, self).__init__(*args, **kws)
        # Python 3
        # super().__init__(*args, **kws)


def _is_csv(value):
    """Test whether context.output.filetype is "csv"."""
    context = lena.flow.get_context(value)
    return _get_recursively(
        context, "output.filetype", None
    ) == "csv"


def _select_template_or_default(val, default=""):
    data, context = lena.flow.get_data_context(val)
    out_template = _get_recursively(context, "output.template", None)
    if out_template:
        return out_template
    if not default:
        raise lena.core.LenaRuntimeError(
            "context contains no template and empty default provided, "
            "{} is context".format(context)
        )
    return default


class RenderLaTeX(object):
    """Create LaTeX from templates and data."""

    def __init__(self, select_template="", template_dir=".", select_data=None,
                 verbose=0):
        """*select_template* is a string or a callable.
        If a string, it is the name of the template to be used
        (unless *context.output.template* overwrites that).
        If *select_template* is a callable, it must accept
        a value from the flow and return template name.
        If *select_template* is an empty string (default)
        and no template could be found in the context,
        :exc:`.LenaRuntimeError` is raised.

        *template_dir* is the path to the directory with templates
        (used by jinja2.FileSystemLoader).
        By default, it is the current directory.

        *select_data* is a callable to choose data to be rendered.
        It should accept a value from flow and return boolean.
        By default CSV files are selected (see :meth:`run`).

        *verbose* controls the verbosity of output.
        If it is 1, selected values are printed during :meth:`run`.
        If it is 2 or higher, not selected values are printed as well.
        """
        if isinstance(select_template, str):
            self._select_template = lambda _: \
                _select_template_or_default(_, default=select_template)
        elif callable(select_template):
            self._select_template = select_template
        else:
            raise lena.core.LenaTypeError(
                "select_template must be a string or a callable, "
                "{}".format(select_template) + "provided"
            )

        if select_data is None:
            self._select_data = _is_csv
        elif callable(select_data):
            self._select_data = select_data
        else:
            raise lena.core.LenaTypeError(
                "select_template must be a string or a callable, "
                "{} provided".format(select_template)
            )
        self._loader = jinja2.FileSystemLoader(template_dir)
        self._environment = _Environment(loader=self._loader)
        self._verbose = verbose
        # print("templates:", self._environment.list_templates())

    def run(self, flow):
        """Render values from *flow* to LaTeX.

        If no custom *select_data* was initialized,
        values with *context.output.filetype* equal to *"csv"*
        are selected by default.

        Rendered LaTeX text is yielded as the data part of the tuple
        (use :class:`.Writer` to write that to the filesystem).
        *context.output.filetype* updates to *"tex"*.

        Not selected values pass unchanged.
        """
        _update_recursively = lena.context.update_recursively
        verbose = self._verbose
        select_data = self._select_data
        for val in flow:
            if select_data(val):
                if verbose:
                    print("RenderLaTeX: selected", val)
                template = self._environment.get_template(self._select_template(val))
                context = lena.flow.get_context(val)
                _update_recursively(context, {"output": {"filetype": "tex"}})
                _update_recursively(context, {"output": {"fileext": "tex"}})

                data = template.render(context)
                yield (data, context)
            else:
                if verbose >= 2:
                    print("RenderLaTeX: not selected", val)
                yield val
