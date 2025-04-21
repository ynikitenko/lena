"""Hypothesis strategy for histograms."""
import hypothesis.strategies as st


_low_edge = st.floats(
    allow_infinity=False, allow_nan=False,
    min_value=-1e+9, max_value=1e+9
)
_diffs = st.lists(
    st.floats(
        min_value=1e-3,
        # too small values may fail during refinement.
        # exclude_min=True,
        max_value=1e+3,  # otherwise 2 * 8.98846567431158e+307 is infinity
        # also max_value should not be much larger than min_value in order
        # to not lose precision.
        allow_infinity=False,
        allow_nan=False,
    ),
    min_size=0,
    max_size=100,
)

# @given works only for tests, which return None.
@st.composite
def generate_increasing_list(draw):
    """Generate an increasing list of floats."""
    low_edge1 = draw(_low_edge)
    low_edge2 = draw(_low_edge)
    # a rare case, but Hypothesis would find that
    if low_edge1 == low_edge2:
        low_edge2 = low_edge1 + 1
    if low_edge1 < low_edge2:
        results = [low_edge1, low_edge2]
    else:
        results = [low_edge2, low_edge1]
    diffs = draw(_diffs)
    # or use itertools.accumulate with *initial* for Python >= 3.8
    prev = results[-1]
    for diff in diffs:
        cur = prev + diff
        if cur == prev:
            # we have to skip those
            # because of possible precision loss with large numbers
            continue
        results.append(cur)
        prev = cur
    return results
