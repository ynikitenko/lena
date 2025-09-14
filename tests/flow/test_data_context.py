from functools import partial

import pytest

from lena.core import LenaTypeError
from lena.flow import Data, Context


def test_data():
    dt1 = Data(
        lambda x: x+1,
        lambda x: x*2,
    )
    # context is added if missing
    assert dt1(1) == (4, {})
    # context is left unchanged
    assert dt1((1, {"a": "b"})) == (4, {"a": "b"})

    dt2 = Data(
        lambda x: x+1,
    )
    # one element works
    assert dt2(1) == (2, {})

    # empty context manager raises
    with pytest.raises(LenaTypeError):
        Data()


def test_context():
    def insert(ctx, val):
        # ctx.update({"val": val})
        ctx["val"] = val
        return ctx

    ctx = Context(
        partial(insert, val="a"),
        partial(insert, val="b"),
    )
    assert ctx((None, {})) == (None, {"val": "b"})

    # empty context manager raises
    with pytest.raises(LenaTypeError):
        Context()
