import copy
import json
import pickle

import pytest

import lena.core
from lena.context import Context, PrettyContext
# Context is deprecated since Lena 0.6


def test_pretty_context():
    d = {'a': {'b': 'c d'}}
    c = PrettyContext(d)

    ## repr
    # default formatter
    assert c.__repr__() == json.dumps(d, sort_keys=True, indent=4)
    # custom formatter
    c1 = PrettyContext(formatter=lambda s: "")
    assert c1.__repr__() == ""
    # oops, formatter must be callable
    with pytest.raises(lena.core.LenaTypeError):
        c1 = PrettyContext(formatter="")

    ## call
    res = c((1, {}))
    assert res[0] == 1
    assert res[1] == PrettyContext({})
    # PrettyContext can also be accepted
    res = c((1, PrettyContext()))
    assert res[1] == PrettyContext({})

    ## attribute access
    d1 = copy.deepcopy(d)
    c = PrettyContext(d1)
    assert c.a == d["a"]
    # nested attribute access works
    assert c.a.b == "c d"

    # missing attributes raise
    with pytest.raises(lena.core.LenaAttributeError):
        c.b

    ## setting attributes works
    c.b = 3
    d1["b"] = 3
    assert c == d1
    # nested setting attributes works
    c.a.b = "e"
    assert c.a.b == "e"
    # nested setting new attributes does not work
    with pytest.raises(AttributeError):
        c.d.e.f = "g"
        # assert c.d.e.f == "g"

    # private attributes raise
    with pytest.raises(AttributeError):
        c._aaa = 3
    with pytest.raises(AttributeError):
        c._aaa

    ## PrettyContext can be pickled
    d2 = {"a": "b"}
    c2 = PrettyContext(d2)
    picklestring = pickle.dumps(c2)
    assert pickle.loads(picklestring) == c2
