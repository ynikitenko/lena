import copy
import pytest

import lena.core
from lena.context import UpdateContext


def test_update_context():
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

    # update can be not a dict or a string
    uc13 = UpdateContext("data", 0)
    assert uc13(copy.deepcopy(data)) == (0, {"data": 0})
    # simple string
    uc14 = UpdateContext("data", "data")
    assert uc14(copy.deepcopy(data)) == (0, {"data": "data"})
    # formatting string
    uc15 = UpdateContext("data", "{data}")
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

    # string initialization of update works
    # subdictionaries are converted to string with format_str
    data = (0, {"data": {"yes": {"Yes": "YES"}}})
    uc7 = UpdateContext("data.yes.Yes", "{data.yes}", recursively=False)
    assert uc7(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": {'Yes': 'YES'}}
            }
        }
    )
    # value missing in data
    with pytest.raises(lena.core.LenaKeyError):
        uc7((0, {}))
    # default is set
    uc71 = UpdateContext("data", "{data.yes}", default="", recursively=False)
    assert uc71((0, {})) == (0, {"data": ""})

    # strings without braces are treated as simple update values
    uc8 = UpdateContext("data.yes.Yes", "data.yes", recursively=False)
    assert uc8(copy.deepcopy(data)) == (
        0,
        {
            "data": {
                "yes": {"Yes": "data.yes"}
            }
        }
    )
    # # braces can be only in the beginning and in the end of the string
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "{data.yes")
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "data.yes}")
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "data.ye}s")
    # with pytest.raises(lena.core.LenaValueError):
    #     UpdateContext("data", "{data.ye}s}")
