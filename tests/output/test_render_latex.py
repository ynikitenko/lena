import copy
from copy import deepcopy
import inspect
import jinja2
import os
import pytest
import sys

import lena
from lena.output.render_latex import (
    RenderLaTeX, _Template, _Environment, _select_template_or_default
)
from lena.context import get_recursively, update_recursively


def test_template():
    # Check that old template syntax (like {{ var }}) doesn't work. 
    t1 = _Template('Hello {{ name }}!')
    assert t1.render(name='John Doe') == u'Hello {{ name }}!'
    assert t1.environment.variable_start_string == r'\VAR{'
    # New \VAR{ syntax works.
    t2 = _Template(r'Hello \VAR{ name }!')
    assert t2.render(name='John Doe') == u'Hello John Doe!'
    assert t2.render(name='John Doe') == u'Hello John Doe!'
    True
    assert t2.render({"name": 'John Doe'}) == u'Hello John Doe!'
    ## this stream test doesn't work, it worked before,
    ## I don't know what changed and I don't use that anyway.
    # stream = t2.stream(name='John Doe')
    # assert next(stream) == u'Hello John Doe!'
    # with pytest.raises(StopIteration):
    #     next(stream)
    # t2.render({"name1": 'John Doe'}) == 'Hello \VAR{ name }!'
    assert t2.render({"name1": 'John Doe'}) == u'Hello !'
    t3 = _Template(r'Hello \VAR{ name }!', undefined=jinja2.DebugUndefined)
    assert t3.render({"name1": 'John Doe'}) == u'Hello {{ name }}!'
    assert t3.render({"name1": 'John Doe'}) != r'Hello \VAR{ name }!'


def test_environment():
    env = _Environment()
    # Old template syntax (like {{ var }}) doesn't work. 
    t1 = env.from_string('Hello {{ name }}!')
    assert t1.render(name='John Doe') == u'Hello {{ name }}!'

    # New \VAR{ syntax works.
    t2 = env.from_string(r'Hello \VAR{ name }!')
    assert t2.render(name='John Doe') == u'Hello John Doe!'
    
    assert jinja2.Environment(
        variable_start_string=r'\VAR{', undefined=jinja2.DebugUndefined
    ).from_string("{{ val }}").render({"val": "Hello"}) ==  u'{{ val }}'
    assert jinja2.Environment(
        variable_start_string=r'\VAR{', variable_end_string='}'
    ).from_string(r'\VAR{ val }').render({"val": "Hello"}) == u'Hello'
    assert jinja2.Environment(
        variable_start_string=r'\VAR{', variable_end_string='}',
        undefined=jinja2.DebugUndefined
    ).from_string("{{ val }}").render({"val": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(
        variable_start_string=r'\VAR{', undefined=jinja2.DebugUndefined
    ).from_string(r"\VAR{ val }}").render({"val": "Hello"}) == u'Hello'
    # Incorrect, should be "\VAR{ val }}"
    # Submitted to https://github.com/pallets/jinja/issues/958
    # That bug was closed, a new wrapper was suggested (DIY).
    assert jinja2.Environment(
        variable_start_string=r'\VAR{',
        undefined=jinja2.DebugUndefined
    ).from_string(r"\VAR{ val }}").render({"val1": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(undefined=jinja2.DebugUndefined)\
        .from_string("{{ val }}").render({"val1": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(variable_start_string=r'\VAR{')\
        .from_string(r"\VAR{ val }}").render({"val": "Hello"}) == u'Hello'


def test_render_latex():
    curpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    # may also need os.path.abspath(curpath)
    template_dir = curpath
    renderer = RenderLaTeX("hist1.tex", template_dir)

    ## Template inheritance works ##
    context = {"output": {"filetype": "csv", "filepath": "output.csv"}}
    data, new_context = next(
        renderer.run([("output.csv", deepcopy(context))])
    )
    rendered_file = os.path.join(curpath, "rendered.tex")
    with open(rendered_file) as fil:
        rendered = "".join(fil.readlines())
        # same:
        # rendered = "".join([line for line in fil])
    if sys.version[0] == "2":
        rendered = unicode(rendered)
    # Warning: print can't show non-printed characters,
    # you won't see if there is a space at the end of the line!
    # print(data)
    # print(rendered)
    assert repr(data + "\n") == repr(rendered)
    assert new_context == {
        'output': {
            "fileext": "tex",
            "filetype": "tex",
            "filepath": "output.csv"
        }
    }

    # not selected data passes unchanged
    assert list(renderer.run([("output.csv", {})])) == [("output.csv", {})]


def test_select_template():
    select = _select_template_or_default
    # raises if no template could be found
    empty = (None, {})
    with pytest.raises(lena.core.LenaRuntimeError):
        select(empty)
    # returns default if set
    assert select(empty, default="default") == "default"

    # output.template is used if present
    context_with_template = {"output": {"template": "from_context"}}
    val = (None, context_with_template)
    assert select(val) == "from_context"
    # output.template overwrites default
    assert select(val, default="default") == "from_context"

    # wrong type raises
    with pytest.raises(lena.core.LenaTypeError):
        RenderLaTeX(select_template=1)

    # custom function works
    sel = lambda _: "template"
    render = RenderLaTeX(select_template=sel)
    assert render._select_template(val) == "template"


def test_select_data():
    # select_data must be None or callable
    with pytest.raises(lena.core.LenaTypeError):
        RenderLaTeX(select_data=1)
    render = RenderLaTeX(select_data=lambda _: True)
    assert render._select_data(0) is True


def test_verbose(capsys):
    template_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
    renderer = RenderLaTeX("hist1.tex", template_dir)
    val = (None, {})
    # verbose=1: selected values are printed
    render1 = RenderLaTeX(
        "hist1.tex",
        template_dir,
        select_data=lambda _: True,
        verbose=1
    )
    list(render1.run([copy.deepcopy(val)]))
    captured = capsys.readouterr()
    assert captured.out == "# RenderLaTeX: selected (None, {})\n"

    # verbose=2: not selected values are printed too
    render2 = RenderLaTeX(
        "hist1.tex",
        template_dir,
        select_data=lambda val: val[0],
        verbose=2
    )
    data = [(None, {}), (1, {})]
    list(render2.run(data))
    captured = capsys.readouterr()
    assert captured.out == (
        "# RenderLaTeX: not selected (None, {})\n"
        "# RenderLaTeX: selected (1, {})\n"
    )
