"""Check whether a sequence can be converted to a Lena Sequence."""
# otherwise import errors arise
# from . import source


def is_fill_compute_el(obj):
    """Object contains executable methods 'fill' and 'compute'."""
    return (hasattr(obj, 'fill')
            and hasattr(obj, 'compute')
            and callable(obj.fill)
            and callable(obj.compute))


def is_fill_compute_seq(seq):
    """Test whether *seq* can be converted to a FillComputeSeq.

    True only if it is a FillCompute element
    or contains at least one such,
    and it is not a Source sequence.
    """
    if is_source(seq):
        return False
    is_fcseq = False
    try:
        is_fcseq = any(map(is_fill_compute_el, seq))
    except TypeError:
        # seq is non-iterable
        pass
    if is_fill_compute_el(seq):
        is_fcseq = True
    return is_fcseq


def is_fill_request_el(obj):
    """Object contains executable methods 'fill' and 'request'."""
    return hasattr(obj, 'fill') and hasattr(obj, 'request') \
            and callable(obj.fill) and callable(obj.request)


def is_fill_request_seq(seq):
    """Test whether *seq* can be converted to a FillRequestSeq.

    True only if it is a FillRequest element
    or contains at least one such,
    and it is not a Source sequence.
    """
    if is_source(seq):
        return False
    is_fcseq = False
    if hasattr(seq, '__iter__'):
        is_fcseq = any(map(is_fill_request_el, seq))
    if is_fill_request_el(seq):
        is_fcseq = True
    return is_fcseq


def is_run_el(obj):
    """Object contains executable method 'run'."""
    return hasattr(obj, 'run') and callable(obj.run)


def is_source(seq):
    """Sequence is a Source, if and only if its type is Source."""
    # Otherwise lambdas would be counted as Source,
    # but they must be converted to Sequences.
    # Moreover: this makes Source elements explicit and visible in code.
    from . import source
    return isinstance(seq, source.Source)
