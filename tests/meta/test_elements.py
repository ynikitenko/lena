from copy import deepcopy

import pytest

from lena.core import LenaAttributeError
from lena.meta.elements import SetContext, UpdateContextFromStatic, StoreContext

set_context_far  = SetContext("data.detector", "far")
set_context_near = SetContext("data.detector", "near")


def test_set_context():
    # representation works
    assert repr(set_context_far) == 'SetContext("data.detector", "far")'

    # equality works
    set_context_far2  = SetContext("data.detector", "far")
    assert set_context_far2 == set_context_far
    assert set_context_near != set_context_far
    assert set_context_near != "some other value"

    # _get_context works
    assert set_context_far._get_context() == {"data": {"detector": "far"}}

    # not string values work
    sc3 = SetContext("nevents", 3)
    assert sc3._get_context() == {"nevents": 3}

    ## context formatting works
    sc4 = SetContext("full_name", "{{detector}}")

    dt_context = {"detector": "far"}
    sc4._set_context(dt_context)
    assert sc4._get_context() == {"detector": "far", "full_name": "far"}

    # missing context raises
    sc5 = SetContext("full_name", "{{detector}}")
    with pytest.raises(LenaAttributeError):
        # detector was not set
        sc5._get_context()


def test_store_context():
    sc1 = StoreContext()
    sc2 = StoreContext()
    sc_empty = StoreContext()
    context = {"a": "b"}

    # _set_context works
    sc1._set_context(context)
    sc2._set_context(context)
    assert sc1.context == {"a": "b"}

    # representation works
    assert repr(sc1) == 'StoreContext() or "{\'a\': \'b\'}"'

    # equality works
    assert sc1 == sc2
    assert sc1 != sc_empty
    assert sc1 != "some other value"
