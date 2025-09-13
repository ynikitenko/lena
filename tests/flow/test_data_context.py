from functools import partial

import pytest

from lena.core import LenaTypeError
from lena.flow import Context


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
