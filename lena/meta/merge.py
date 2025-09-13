from lena.core import Source, Split, FillComputeSeq
from lena.core import LenaTypeError, LenaValueError
# We don't merge tails, since they don't influence efficiency,
# can be easily divergent (DrawDetector vs not),
# and ultimately might require multiple sequence merges
# (for each equal subsequence); most likely impossible.


def merge_heads(*seqs):
    """Merge common heads of sequences *seqs*.

    Equal elements are merged into a common sequence,
    first unequal ones are put into a :class:`.Split`
    and recursively merged with similar ones.
    To be able to be merged, sequence elements
    must support equality comparison.

    This class can optimize processing same data with
    several sequences in different modules
    by reading that data once and processing that simultaneously.
    Example:

    .. code-block:: python

        s1 = Source(
            ReadData(),
            Process1(),
        )
        s2 = Source(
            ReadData(),
            Process2(),
        )
        merged = merge_heads(s1, s2)

        # merged is
        Source(
            ReadData(),
            Split([
                Process1(),
                Process2(),
            ]),
        )

        # merge_heads(s1, s1) is s1

    *seqs* are Lena sequences. They must be of the same type
    (for example :class:`.Source`).

    .. versionadded:: 0.6
    """
    if len(seqs) == 1:
        return seqs[0]

    if not seqs:
        raise LenaTypeError("no sequences provided")

    types = set((type(seq) for seq in seqs))
    if len(types) != 1:
        raise LenaTypeError(
            "all sequences must have the same type, "
            "{} provided".format(types)
        )

    # todo: add other types.
    # Maybe unwrap existing sequences.
    # assert type(seqs[0]) == Source
    # Only :class:`.Source` are allowed.

    head = []
    for ind, el0 in enumerate(seqs[0]):
        # collect elements with the given index from each sequence
        els = [el0]
        for seq in seqs[1:]:
            # subsequences (where seq0 is the head of seq1) are forbidden.
            # Alternatively: put an empty Sequence after s0.
            # It is hard to imagine that scenario. Can be done manually.
            el = seq[ind]
            # Subsequences are ignored.
            # try:
            #     el = seq[ind]
            # except IndexError:
            #     # reached end of seq, and it is same as others
            #     raise LenaValueError(
            #         "subsequences are forbidden. "
            #         "{} is a subsequence of {}".format(seq, seqs[0])
            #     )
            if el in els:
                continue
            else:
                els.append(el)

        # all elements are equal up to now
        if len(els) == 1:
            head.append(el0)
            continue

        # unequal sequences encountered
        merges = []
        for el in els:
            el_merges = []
            # here the original order of sequences can be changed.
            for seq in seqs:
                if seq[ind] == el:
                    if seq[ind+1:]:
                        # here we ignore empty tails...
                        el_merges.append(seq[ind+1:])
            merges.append((el, *merge_heads(el_merges)))
        # Split determines sequence types automatically
        # Every merge is a tuple.
        split = Split(merges)
        head.append(split)
        return type(seqs[0])(*head)

    # all sequences are equal. Return the first sequence.
    # Could raise, but this is better for recursive calls.
    return type(seqs[0])(*head)
