"""IncludeExcludeTree hypothesis testing (to be done):

1) IET(include=True) + IET(include=False) = Id on every context.

2) If a context has no intersection with the exclude keys in include tree,
then it is selected.
From this and (1) a similar thing for an exclude follows.

"""
import pytest

from lena.core import LenaValueError

from lena.context.include_exclude_tree import (
    _group_by_starting_prefixes, _split_key, make_include_exclude_tree,
    _startswith
)
from lena.context import IncludeExcludeTree


def test_group_by_starting_prefixes():
    gsp = _group_by_starting_prefixes
    keys = [
        ("a", "b", "c"),
        ("a", "c", "c"),
        ("b", "c", "d"),
    ]
    assert gsp(keys) == {
        "a": [("b", "c"), ("c", "c")],
        "b": [("c", "d")],
    }

    # An empty key raises.
    # Should never happen, but just in case.
    with pytest.raises(AssertionError):
        gsp([
            ("a", "b"),
            (),
        ])


def test_include_exclude_tree():
    IET = IncludeExcludeTree

    # IETs can be simply including/excluding everything
    true_iet  = IET([], {}, include=True)
    false_iet = IET([], {}, include=False)

    # equality testing works
    assert true_iet != false_iet

    c1 = {"a": 1, "b": 2, "c": {"d": 3}}

    # pure include/exclude IETs work
    assert true_iet.get(c1)  == c1
    assert false_iet.get(c1) == {}

    # excluding simple keys works
    iet1 = IET(["a", "b"], {}, include=True)
    assert iet1.get(c1) == {"c": {"d": 3}}

    # including simple keys works
    # in fact, keys should be a set, but any container
    # that can be used with "in" can work.
    iet2 = IET({"a", "b"}, {}, include=False)
    assert iet2.get(c1) == {"a": 1, "b": 2}

    # incorrect tests don't raise.
    # incorrect subtree raises
    # with pytest.raises(AssertionError):
        # IET([],
        #     {
        #         "a": IET(
        #             set(),
        #             # we only need this IET to be an argument here
        #             {"dummy": true_iet},
        #             include=True
        #         ),
        #     },
        #     # same as in its subtree
        #     include=True
        # )
        # this tree would be perfectly correct
        # for merge="a.dummy.smth_else" .

    ## A real subtree works
    iet4 = IET(["d"], {}, include=False)

    # include everything except "a", and also "c.d", but not "c.*"
    iet3 = IET(["a"], {"c": iet4}, include=True)
    c2 = {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}
    assert iet3.get(c2) == {"b": 2, "c": {"d": 3}}

    # "d" is not a dict here, so it won't be selected
    c3 = {"a": 1, "b": 2, "c": "d"}
    assert iet3.get(c3) == {"b": 2}

    # equality testing works
    assert iet3 == iet3
    assert iet3 != iet4


def test_make_include_exclude_tree():
    ## Simplest (improper) selectors work
    iet_true  = make_include_exclude_tree("")
    iet_false = make_include_exclude_tree(excludes="")
    c1 = {"a": 1, "b": 2}
    # initialization is correct
    assert iet_true.keys == set()
    assert iet_true.subtrees == {}
    assert iet_true.include == True
    assert iet_false.include == False
    # context selection is correct
    assert iet_true.get(c1) == c1
    assert iet_false.get(c1) == {}

    ## Real include/exclude selectors work
    c2 = {"a": 1, "b": 2, "c": {"d": 3, "e": 0}}
    iet1 = make_include_exclude_tree(
        includes=("", "c.d"),
        excludes=("c")
    )
    assert iet1.get(c2) == {"a": 1, "b": 2, "c": {"d": 3}}


def test_split_key():
    # keys are split by dots properly
    assert _split_key("a.b") == ["a", "b"]

    # improper keys raise
    for key in (".a", "a.", "a..b"):
        with pytest.raises(LenaValueError):
            _split_key(key)

    # all lines are covered
    assert _split_key("") == [""]


def test_startswith():
    s1 = "ab"
    s2 = "abc"
    # for strings the meaning is the same as usually
    assert _startswith(s1, s2)
    assert not _startswith(s2, s1)

    # every container starts with itself
    assert _startswith(s1, s1)

    # every container starts with an empty one
    assert _startswith([], [1])
