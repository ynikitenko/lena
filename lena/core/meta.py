# functions to deal with sequences
import lena.core
from . import lena_sequence


def alter_sequence(seq):
    orig_seq = seq
    seq = flatten(seq)
    changed = False
    if not isinstance(seq, (lena_sequence.LenaSequence, tuple)):
        # an element
        el = seq
        if hasattr(el, "alter_sequence") and callable(el.alter_sequence):
            return el.alter_sequence(el)
        else:
            return orig_seq
    for ind in reversed(range(len(seq))):
        el = seq[ind]
        if hasattr(el, "alter_sequence") and callable(el.alter_sequence):
            new_seq = el.alter_sequence(seq)
            if new_seq == seq:
                continue
            else:
                # call recursively for the new sequence
                return alter_sequence(new_seq)
    # not altered
    return orig_seq


def flatten(seq):
    """Unnest sequences. Split is unaffected."""
    flattened = []
    flat = True
    if not isinstance(seq, (lena_sequence.LenaSequence, tuple)):
        # seq is an element
        return seq
    for el in seq:
        if isinstance(el, lena_sequence.LenaSequence):
            flattened.extend(flatten(el))
            flat = False
        else:
            flattened.append(el)

    if flat:
        # return unchanged
        return seq
    else:
        # return flattened list
        return flattened
