import pytest
import lena

from lena.flow import Filter, Selector, StoreFilled
from lena.structures import histogram


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
    assert list(f0.run(data)) == res_data
    assert list(f1.run(data)) == res_data

    # filter with a function works
    fun = lambda val: val
    f2 = Filter(fun)
    assert list(f2.run(data + [0, 4])) == [1, 2, "s", (3, {}), 4]

    ## Test fill_into
    sf1 = StoreFilled()
    for val in data:
        f1.fill_into(sf1, val)
    assert sf1.group == res_data

    # Lena classes work in filters
    data3 = [histogram([1, 2])]
    f3 = Filter(histogram)
    assert list(f3.run(data3)) == data3

    # representation works
    assert repr(f3) == "Filter(Selector(histogram))"

    # equality works
    f4 = Filter(fun)
    assert f4 == f2
    assert f3 != f4
    # NotImplemented
    assert f3 != 0

    ## errors are handled correctly

    # simple lambda raises correctly
    f5 = Filter(lambda val: len(val) > 0)
    data2 = [1, "s"]
    with pytest.raises(TypeError):
        list(f5.run(data2))
    # Selector raises correctly
    f6 = Filter(Selector(lambda val: len(val) > 0))
    with pytest.raises(TypeError):
        list(f6.run(data2))

    # raise_on_error set to False does not raise
    f7 = Filter(Selector(lambda val: len(val) > 0, raise_on_error=False))
    assert list(f7.run(data2)) == ["s"]
