from lena.core import alter_sequence, flatten
from lena.core import FillComputeSeq, Sequence, Source, SourceEl
from lena.flow import Cache
# dummy elements
from lena.flow import Count, Print


class SimpleCache(Cache):

    def __init__(self):
        super(SimpleCache, self).__init__("dummy.pkl")

    def cache_exists(self):
        return True


def test_alter_sequence():
    sc = SimpleCache()
    scs = SourceEl(sc, call="_load_flow")
    ## alter_sequence with two elements works ##
    # Sequence works
    seq0 = Sequence(Count(), sc)
    assert alter_sequence(seq0) == Source(scs)
    # same works for tuples (which are Sequences in Lena Split)
    assert alter_sequence((Count(), sc)) == Source(scs)

    # FillComputeSeq works
    seq1 = FillComputeSeq(Count(), sc)
    assert alter_sequence(seq1) == Source(scs)

    ## alter_sequence with one element works ##
    # Sequence works
    assert alter_sequence(Sequence(sc)) == Source(scs)
    # FillComputeSeq can not contain only Cache


def test_flatten():
    seq0 = Sequence(Count(), Print())
    # a flat sequence remains unchanged
    assert flatten(seq0) is seq0

    seq1 = Sequence(Count(), Sequence(Print()))
    # nested sequences are extracted
    # Note that lists are used instead of sequences.
    assert flatten(seq1) == list(seq0._seq)

    # FillComputeSeq works
    seq2 = FillComputeSeq(Count(), Sequence(Print()))
    assert flatten(seq2) == list(seq0._seq)
