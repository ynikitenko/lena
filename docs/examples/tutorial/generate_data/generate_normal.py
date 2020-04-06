"""Generate 3-dimensional vectors normally distributed."""
from __future__ import print_function

import random
import sys
import os
import itertools
# import numpy as np
# from scipy.stats import norm


DATADIR = os.path.join("..", "data")


def normal3_shifted(size, seed, means, sigmas):
    if sys.version_info.major == 2:
        random.seed(seed)
    else:
        random.seed(seed, version=1)
    # x and y ~ Norm(0, 5), z ~ Norm(2, 5)
    ms = list(zip(means, sigmas))
    x = lambda: random.gauss(*ms[0])
    y = lambda: random.gauss(*ms[1])
    z = lambda: random.gauss(*ms[2])
    return list((x(), y(), z()) for i in range(0, size))


# def normal3_shifted_numpy(size):
#     np.random.seed(0)
#     # x and y ~ Norm(0, 5), z ~ Norm(2, 5)
#     rv = [norm(0, scale=5), norm(0, scale=5), norm(2, scale=5)]
#     xs, ys, zs = [var.rvs(size=size) for var in rv]
#     xyzs = zip(xs, ys, zs)
#     return xyzs


def formatter3(v):
    return "{:f},{:f},{:f}".format(*v)


def formatter1(v):
    return "{:f}".format(v)


def write_to_file(data, filename, formatter):
    with open(filename, "w") as fil:
        for vec in data:
            line = formatter(vec)
            print(line, file=fil)


if __name__ == "__main__":
    seed = 0
    means = (0, 0, 2)
    sigmas = (5, 5, 5)
    if len(sys.argv) > 1 and sys.argv[1] == "--large":
        large = True
        size = 10**6
        normal_filename = "normal_3d_large.csv"
    else:
        large = False
        size = 10
        normal_filename = "normal_3d.csv"
    xyzs = normal3_shifted(size, seed, means, sigmas)
    # xyzs = normal3_shifted(1000)
    write_to_file(xyzs,
                  os.path.join(DATADIR, normal_filename),
                  formatter3)
    if large:
        sys.exit(0)

    xs = [v[0] for v in xyzs]
    write_to_file(xs,
                  os.path.join(DATADIR, "x.csv"),
                  formatter1)

    xyzs_mc = normal3_shifted(size, seed=1, means=means, sigmas=(5, 5, 4))
    write_to_file(xyzs_mc,
                  os.path.join(DATADIR, "normal_3d_mc.csv"),
                  formatter3)

    xyzs_1 = normal3_shifted(size, seed=2, means=means, sigmas=sigmas)
    xyzs_2 = normal3_shifted(size, seed=3, means=(0,0,3), sigmas=(6,6,6))
    xyzs_double_event = list(zip(xyzs_1, xyzs_2))
    double_ev_filename = os.path.join(DATADIR, "double_ev.csv")
    with open(double_ev_filename, "w") as fil:
        for double_ev in xyzs_double_event:
            line = formatter3(double_ev[0])
            print(line, file=fil)
            line = formatter3(double_ev[1])
            print(line, file=fil)
