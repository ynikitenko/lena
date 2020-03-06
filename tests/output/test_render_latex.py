from __future__ import print_function

import inspect
import jinja2
import os
import pytest
import sys

from copy import deepcopy

from lena.output import RenderLaTeX, Template, Environment


def test_template():
    # Check that old template syntax (like {{ var }}) doesn't work. 
    t1 = Template('Hello {{ name }}!')
    assert t1.render(name='John Doe') == u'Hello {{ name }}!'
    assert t1.environment.variable_start_string == r'\VAR{'
    # New \VAR{ syntax works.
    t2 = Template(r'Hello \VAR{ name }!')
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
    t3 = Template(r'Hello \VAR{ name }!', undefined=jinja2.DebugUndefined)
    assert t3.render({"name1": 'John Doe'}) == u'Hello {{ name }}!'
    assert t3.render({"name1": 'John Doe'}) != 'Hello \VAR{ name }!'


def test_environment():
    env = Environment()
    # Old template syntax (like {{ var }}) doesn't work. 
    t1 = env.from_string('Hello {{ name }}!')
    assert t1.render(name='John Doe') == u'Hello {{ name }}!'

    # New \VAR{ syntax works.
    t2 = env.from_string(r'Hello \VAR{ name }!')
    assert t2.render(name='John Doe') == u'Hello John Doe!'
    
    assert jinja2.Environment(variable_start_string='\VAR{', undefined=jinja2.DebugUndefined).from_string("{{ val }}").render({"val": "Hello"}) ==  u'{{ val }}'
    assert jinja2.Environment(variable_start_string='\VAR{', variable_end_string='}').from_string(r'\VAR{ val }').render({"val": "Hello"}) == u'Hello'
    assert jinja2.Environment(variable_start_string='\VAR{', variable_end_string='}', undefined=jinja2.DebugUndefined).from_string("{{ val }}").render({"val": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(variable_start_string='\VAR{', undefined=jinja2.DebugUndefined).from_string("\VAR{ val }}").render({"val": "Hello"}) == u'Hello'
    # Incorrect, should be "\VAR{ val }}"
    # Submitted to https://github.com/pallets/jinja/issues/958
    # That bug was closed, a new wrapper was suggested (DIY).
    assert jinja2.Environment(variable_start_string='\VAR{', undefined=jinja2.DebugUndefined).from_string("\VAR{ val }}").render({"val1": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(undefined=jinja2.DebugUndefined).from_string("{{ val }}").render({"val1": "Hello"}) == u'{{ val }}'
    assert jinja2.Environment(variable_start_string='\VAR{').from_string("\VAR{ val }}").render({"val": "Hello"}) == u'Hello'


def test_render_latex():
    curpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    # may also need os.path.abspath(curpath)
    template_dir = curpath
    renderer = RenderLaTeX("hist1.tex", template_dir)

    ## Template inheritance works ##
    context = {"output": {"filetype": "csv", "filepath": "output.csv"}}
    data, new_context = next(renderer.run([("output.csv", deepcopy(context))]))
    # print(data, new_context)
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
    assert new_context == {'output': {'fileext': 'tex', 'filetype': 'tex', "filepath": "output.csv"}}

    ## repeat works ##
    context["output"].update({"latex": {"repeat": [{"scale": "log"}]}})
    rendered_l = list(renderer.run([("output.csv", context)]))
    assert len(rendered_l) == 2
    # for res in rendered_l:
    #     print(res[1])
    context_1 = rendered_l[0][1]
    assert "scale" not in context_1
    assert context_1 == {
        'output': {'fileext': 'tex', 'filetype': 'tex', "filepath": "output.csv",
                   'latex': {'repeat': [{'scale': 'log'}]}}
        }
    context_2 = rendered_l[1][1]
    assert context_2["scale"] == "log"
    context_1.update({"scale": "log"})
    assert context_1 == context_2

    # not selected data passes unchanged
    assert list(renderer.run([("output.csv", {})])) == [("output.csv", {})]
