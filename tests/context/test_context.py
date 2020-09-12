from __future__ import print_function

import copy
import json
import pytest

import lena.core
from lena.context import Context


def test_context():
    d = {'a': {'b': 'c d'}}
    c = Context(d)

    ## repr
    # default formatter
    assert c.__repr__() == json.dumps(d, sort_keys=True, indent=4)
    # custom formatter
    c1 = Context(formatter=lambda s: "")
    assert c1.__repr__() == ""
    # oops, formatter must be callable
    with pytest.raises(lena.core.LenaTypeError):
        c1 = Context(formatter="")

    ## call
    res = c((1, {}))
    assert res[0] == 1
    assert res[1] == Context({})
    # Context can also be accepted
    res = c((1, Context()))
    assert res[1] == Context({})

    ## attribute access
    d1 = copy.deepcopy(d)
    c = Context(d1)
    assert c.a == d["a"]
    # missing attributes raise
    with pytest.raises(lena.core.LenaAttributeError):
        c.b
    c.b = 3
    d1["b"] = 3
    assert c == d1
    # private attributes raise
    with pytest.raises(AttributeError):
        c._aaa = 3
    with pytest.raises(AttributeError):
        c._aaa
