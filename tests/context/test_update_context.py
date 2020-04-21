import copy
import pytest

import lena.core
from lena.context import UpdateContext


def test_update_context():
    data = (0, {"data": "yes"})
    orig_data = copy.deepcopy(data)

    # empty subcontext overwrites all context
    uc1 = UpdateContext("", {}, recursively=False)
    assert uc1(data) == (0, {})
    assert data == (0, {})
    data = orig_data
    # update all context recursively preserves existing data
    uc12 = UpdateContext("", {"new_data": "no"})
    assert uc12(copy.deepcopy(data)) == (0, {"data": "yes", "new_data": "no"})

    # subcontext and update must be a string or a dict
    with pytest.raises(lena.core.LenaTypeError):
        UpdateContext(0, {})
    with pytest.raises(lena.core.LenaTypeError):
        UpdateContext("", 0)

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
