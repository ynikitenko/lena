from lena.core import LenaTypeError


class compose():
    """Function composition of *seq*.

    All elements of *seq* must be callable and return a single value
    (be :class:`.Call` elements).
    They are applied in the order of their appearance in *seq*.

    This is a helper class, but not a Lena sequence,
    since it is does not support transformations of many to many.

    .. versionadded:: 0.6

    .. seealso::
       :class:`.core.Sequence` accepts iterators and takes into account context.
       :class:`.variables.Compose` makes composition of Lena variables.
    """

    def __init__(self, *seq):
        if not all(map(callable, seq)):
            raise LenaTypeError(
                "all arguments must be callable, {}".format(seq)
            )
        if not seq:
            raise LenaTypeError("arguments must be non-empty")
        self._seq = seq

    def __call__(self, val):
        # an alternative could be reduce. However, that may not always
        # be faster: https://stackoverflow.com/questions/5436503/summing-with-a-for-loop-faster-than-with-reduce
        # toolz.functoolz.Compose also uses a simple for loop,
        # https://github.com/pytoolz/toolz/blob/master/toolz/functoolz.py#L473
        for func in self._seq:
            val = func(val)
        return val

    def __eq__(self, other):
        if not isinstance(other, compose):
            return NotImplemented
        # many functions (e.g. lambdas) can compare unequal
        return self._seq == other._seq
