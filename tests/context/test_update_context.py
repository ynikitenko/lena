import copy
import pytest

import lena.core
from lena.context import UpdateContext
from lena.core import LenaValueError, LenaTypeError, LenaKeyError


def test_update_context_subcontext():
    data = (0, {"data": "yes"})
    orig_data = copy.deepcopy(data)

    # empty subcontext is difficult. If encountered runtime, it should be probably skipped.
    ## and don't do 100% tests of developed or new classes...
    # # empty subcontext overwrites all context
    # uc1 = UpdateContext("", {}, recursively=False)
    # assert uc1(data) == (0, {})
    # assert data == (0, {})
    # data = orig_data
    # # update all context recursively preserves existing data
    # uc12 = UpdateContext("", {"new_data": "no"})
    # assert uc12(copy.deepcopy(data)) == (0, {"data": "yes", "new_data": "no"})

    # subcontext must be a string or a dict
    with pytest.raises(lena.core.LenaTypeError):
        UpdateContext(0, {})
    # subcontext must be non-empty
    with pytest.raises(lena.core.LenaValueError):
        UpdateContext("", 0)


def test_update_context_update_not_str():
    data = (0, {"data": "yes"})
    # update can be not a dict or a string
    uc13 = UpdateContext("data", 0)

    # representation works
    assert repr(uc13) == 'UpdateContext("data", 0)'

    # equality testing works
    assert uc13 == UpdateContext("data", 0)
    assert uc13 != UpdateContext("data", 1)

    # for simple value default, skip_on_missing and raise_on_missing
    # can't be set
    with pytest.raises(LenaValueError):
        UpdateContext("data", 0, default="")
    assert uc13(copy.deepcopy(data)) == (0, {"data": 0})
    # simple string
    uc14 = UpdateContext("data", "data")
    assert uc14(copy.deepcopy(data)) == (0, {"data": "data"})
    # formatting string
    uc15 = UpdateContext("data", "{{data}}")
    assert uc15(copy.deepcopy(data)) == (0, {"data": "yes"})

    # non-empty subcontext is a proper subcontext
    uc2 = UpdateContext("new_data", {"new_data": "Yes"})
    assert uc2(copy.deepcopy(data)) == (0, {"data": "yes", "new_data": {"new_data": "Yes"}})
    uc3 = UpdateContext("data", {"new_data": "Yes"})
    assert uc3(copy.deepcopy(data)) == (0, {"data": {"new_data": "Yes"}})

    # nested subcontext works
    data = (0, {"data": {"yes": {"Yes": "YES"}}})
    uc4 = UpdateContext("data.yes", {"new_data": "Yes"})
    # recursively preserves context
    assert uc4(copy.deepcopy(data)) == (0, {"data": {"yes": {"Yes": "YES", "new_data": "Yes"}}})
    # non-recursively overwrites context
    uc5 = UpdateContext("data.yes", {"new_data": "Yes"}, recursively=False)
    assert uc5(copy.deepcopy(data)) == (0, {"data": {"yes": {"new_data": "Yes"}}})
    # key not in subdictionary
    data = (0, {"data": {"_yes": {"Yes": "YES"}}})
    uc6 = UpdateContext("data.yes.Yes", {"new_data": "Yes"}, recursively=False)
    assert uc6(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": {"new_data": "Yes"}},
                "_yes": {"Yes": "YES"}
            }
        }
    )
    with pytest.raises(LenaValueError):
        UpdateContext("data.yes.Yes", {"new_data": "Yes"}, skip_on_missing=True, raise_on_missing=True)
    with pytest.raises(LenaValueError):
        UpdateContext("data", "{{new_data}}", value=True, skip_on_missing=True, raise_on_missing=True)
    with pytest.raises(LenaValueError):
        UpdateContext("data", "{{new_data}}", value=True, default=0, raise_on_missing=True)
    with pytest.raises(LenaValueError):
        UpdateContext("data", "{{new_data}}", value=True, default=0, skip_on_missing=True)
    with pytest.raises(LenaValueError):
        UpdateContext("data", "{{new_data}}", default="")


def test_skip_on_missing():
    data = (0, {"data": {"yes": {"Yes": "YES"}}})

    # update format string
    uc1 = UpdateContext("data", "{{data.yes}}", recursively=False, skip_on_missing=True)
    assert uc1(copy.deepcopy(data))[1] == {"data": "{'Yes': 'YES'}"}
    d = {}
    assert uc1((0, d))[1] is d

    # update value
    uc2 = UpdateContext(
        "data", "{{data.yes}}", value=True, skip_on_missing=True,
        recursively=False
    )
    assert uc2(copy.deepcopy(data))[1] == {"data": {'Yes': 'YES'}}
    assert uc2((0, d))[1] is d


def test_update_context_update_str():
    # string initialization of update works
    # if value is True, the value is copied.
    data = (0, {"data": {"yes": {"Yes": "YES"}}})
    uc1 = UpdateContext("data.yes.Yes", "{{data.yes}}", recursively=False, value=True)
    assert uc1(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": {'Yes': 'YES'}}
            }
        }
    )

    # subdictionaries are converted to string if value is False
    uc2 = UpdateContext("data.yes.Yes", "{{data.yes}}", recursively=False, value=False)
    assert uc2(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": "{'Yes': 'YES'}"}
            }
        }
    )

    # value missing in data
    with pytest.raises(lena.core.LenaKeyError):
        uc1((0, {}))

    # value is missing, default is set
    uc12 = UpdateContext(
        "data.yes.Yes", "{{data.yes}}", recursively=False, value=True,
        default="no"
    )
    assert uc12((0, {}))[1] == {
            "data": {
                "yes": {"Yes": "no"}
            }
        }

    # default values
    # empty
    uc31 = UpdateContext("data", "{{data.yes|default('')}}", recursively=False)
    assert uc31((0, {})) == (0, {"data": ""})
    # a string
    uc32 = UpdateContext("data", "{{data.yes|default('x')}}", recursively=False)
    assert uc32((0, {})) == (0, {"data": "x"})

    # strings without braces are treated as simple update values
    uc4 = UpdateContext("data.yes.Yes", "data.yes", recursively=False)
    assert uc4(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": "data.yes"}
            }
        }
    )

    # braces can be only in the beginning and in the end of the string
    with pytest.raises(lena.core.LenaValueError):
        UpdateContext("data", "{{data.yes")
    with pytest.raises(lena.core.LenaValueError):
        UpdateContext("data", "{{{{data.yes}}")
    with pytest.raises(lena.core.LenaValueError):
        UpdateContext("data", "{{{data.yes}}")
    # }} don't raise.
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "data.yes}}")
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "data.ye}}s")
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "{data.ye}}s}")


def test_update_context_exception_strings():
    # test exception strings
    uc = UpdateContext("var", "{{data}}", raise_on_missing=True)
    with pytest.raises(lena.core.LenaKeyError, match="'data' is undefined, context={}"):
        uc((None, {}))
    with pytest.raises(
        lena.core.LenaValueError,
        match="fix braces for template string '{{{data}}' or set value to False"
        ):
        UpdateContext("var", "{{{data}}", value=True)
