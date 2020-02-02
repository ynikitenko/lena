"""LenaSequence abstract base class."""


# pylint: disable=no-member
# this is an abstract base class and _seq will be defined in subclasses

class LenaSequence(object):
    """Abstract base class for all Lena sequences.

    A sequence consists of elements.
    *LenaSequence* provides methods to iterate over a sequence,
    get its length and get an item at the given index.
    """

    def __iter__(self):
        return self._seq.__iter__()

    def __len__(self):
        return self._seq.__len__()

    def __getitem__(self, ind):
        return self._seq[ind]
