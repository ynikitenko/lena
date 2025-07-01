from lena.core import alter_sequence, flatten
from lena.core import FillComputeSeq, Sequence, Source
from lena.flow import Cache
# dummy elements
from lena.flow import Count, Print


class SimpleCache(Cache):

    def __init__(self, filename, recompute=False,
                 method="cPickle", protocol=2):
        super(SimpleCache, self).__init__("dummy.pkl")

    def cache_exists(self):
        return True


def test_flatten():
    seq0 = Sequence(Count(), Print())
    # a flat sequence remains unchanged
    assert flatten(seq0) is seq0

    seq1 = Sequence(Count(), Sequence(Print()))
    # nested sequences are extracted
    # Note that lists are used instead of sequences.
    assert flatten(seq1) == list(seq0._seq)
