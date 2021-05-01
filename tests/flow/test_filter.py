import pytest
import lena

from lena.flow import Filter, Selector

from tests.examples.fill import StoreFilled


def test_filter():
    # initialization argument must be callable, a Selector,
    # or should be able to be converted to a Selector
    with pytest.raises(lena.core.LenaTypeError):
        Filter(1)

    # filter with a selector works
    s = Selector([int, str])
    f0 = Filter(s)

    ## Test run
    f1 = Filter([int, str])
    data = [1, 2, "s", [], (), (3, {})]
    res_data = [1, 2, "s", (3, {})]
    assert list(f0.run(data)) == res_data  # list(f1.run(data))
    assert list(f1.run(data)) == [1, 2, "s", (3, {})]

    # filter with a function works
    fun = lambda val: val
    f2 = Filter(fun)
    assert list(f2.run(data + [0, 4])) == [1, 2, "s", (3, {}), 4]

    ## Test fill_into
    sf1 = StoreFilled()
    for val in data:
        f1.fill_into(sf1, val)
    assert sf1.list == res_data
