import sys

import pytest


# this function works when used solely,
# but not with other modules tests.
@pytest.mark.skip(reason="can only test this separately from other modules")
def test_missing_jinja2():
    # we check that a proper and clear exception is raised 
    # if jinja2 is missing when using RenderLaTeX
    # from https://stackoverflow.com/a/1350574/952234
    import jinja2
    # doesn't help.
    # jinja2_tmp = jinja2
    sys.modules["jinja2"] = None
    from lena.output import RenderLaTeX
    with pytest.raises(ImportError) as err:
        r = RenderLaTeX("hello")
    assert str(err.value) == "RenderLaTeX can't be used because jinja2 is not found"
    # seems tests are run non-atomically, so need to return this
    # del sys.modules["jinja2"]
    # doesn't work:
    # sys.modules["jinja2"] = jinja2_tmp
