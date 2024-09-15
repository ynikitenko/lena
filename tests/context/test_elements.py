from copy import deepcopy

import pytest

from lena.context import DeleteContext


def test_delete_context():
    # calling without an argument raises.
    # This test is stupid, but we leave it as a restriction.
    with pytest.raises(TypeError):
        DeleteContext()

    value = (1, {"a": {"b": "c"}})

    # missing keys are skipped
    dcd = DeleteContext("d")
    assert dcd(deepcopy(value)) == value

    # present keys are removed
    dcb = DeleteContext("a.b")
    # tuples/lists work same as strings
    dcbt = DeleteContext(("a", "b"))
    dcbl = DeleteContext(["a", "b"])
    # we leave the empty subcontext to show that there was some.
    new_val = (1, {"a": {}})

    assert dcb(deepcopy(value))  == new_val
    assert dcbt(deepcopy(value)) == new_val
    assert dcbl(deepcopy(value)) == new_val
