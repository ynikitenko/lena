"""Hypothesis strategy for histograms."""
from __future__ import print_function

import random

MAX_SAMPLES = 50


def generate_increasing_list(init_range=(-10, 10), diff_scale=1, samples=None,
                             max_samples=MAX_SAMPLES):
    """Generate an increasing list of floats.

    Values are generated using random.uniform distribution.
    The initial value is generated in the *init_range*.
    Next values are added to that with the difference
    in range (0, *diff_scale*).
    If *samples* is given, this will be the resulting list length.
    Otherwise sample size is random from 2 to max_samples.
    """
    init_val = random.uniform(*init_range)
    if samples is None:
        samples = random.randint(2, max_samples)
    diffs = [random.random() * diff_scale for _ in range(samples - 1)]
    results = [init_val]
    prev = init_val
    for diff in diffs:
        if not diff:
            continue
        prev = prev + diff
        results.append(prev)
    return results


def generate_data_in_range(min_val, max_val, samples=None):
    """Generate list of values in the half-open interval [min_val, max_val).

    *samples* designate number of values to be drawn. If not provided,
    it is generated randomly between 0 and MAX_SAMPLES.
    """
    if samples is None:
        samples = random.randint(0, MAX_SAMPLES)
    values = [random.uniform(min_val, max_val) for _ in range(samples)]
    return [val for val in values if val != max_val]


if __name__ == "__main__":
    # print(generate_increasing_list(init_range=(-10, 10), diff_scale=10))
    print(generate_data_in_range(-10, 10))
