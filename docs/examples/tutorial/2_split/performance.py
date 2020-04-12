from __future__ import print_function

import cProfile
import os
import pstats
import sys

from lena.core import Sequence, Split, Source
from lena.structures import Histogram
from lena.math import mesh
from lena.output import ToCSV, Writer, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.variables import Variable

from read_data import ReadData


def main_copybuf(data_file):
    writer = Writer("output")
    s = Sequence(
        ReadData(),
        Split([
            (
                Variable("x", lambda vec: vec[0]),
                Histogram(mesh((-10, 10), 10)),
            ),
            (
                Variable("y", lambda vec: vec[1]),
                Histogram(mesh((-10, 10), 10)),
            ),
            (
                Variable("z", lambda vec: vec[2]),
                Histogram(mesh((-10, 10), 10)),
            ),
        ]),
        MakeFilename("{variable.name}"),
        ToCSV(),
        # writer,
        # RenderLaTeX("histogram_1d.tex", "templates"),
        # writer,
        # LaTeXToPDF(),
        # PDFToPNG(),
    )
    results = s.run([data_file])
    for res in results:
        print(res)


def main_no_copybuf(data_file):
    s = Sequence(
        ReadData(),
        Split([
            (
                lambda vec: vec[0],
                Histogram(mesh((-10, 10), 10)),
                MakeFilename("x"),
            ),
            (
                lambda vec: vec[1],
                Histogram(mesh((-10, 10), 10)),
                MakeFilename("y"),
            ),
            (
                lambda vec: vec[2],
                Histogram(mesh((-10, 10), 10)),
                MakeFilename("z"),
            ),
            ],
            copy_buf=False,
        ),
        MakeFilename("{variable.name}"),
        ToCSV(),
    )
    results = s.run([data_file])
    for res in results:
        print(res)


if __name__ == "__main__":
    # 10**6 events
    data_file = os.path.join("..", "data", "normal_3d_large.csv")
    if not os.path.exists(data_file):
        print("you have to generate the data file "
              "with ../generate_data/generate_normal.py"
        )
        raise RuntimeError("data file missing")
    copy_buf = False
    # copy_buf = True

    # with copy_buf=True Python2 in 84.255 seconds, 20.827 for deepcopy (all as earlier)
    # with copy_buf=False Python2 in 17.758 seconds (OMG)
    # with copy_buf=False PyPy3 in 3.812 seconds.
    ###
    # with no deepcopy in variables
    # (however, there were some optimizations concerning get_data_context)
    # it's not possible to call this code with copy_buf=False.
    # But with copy_buf=True total time is 81.992 seconds (!!), deepcopy time (still largest) is 20.421 seconds.
    # with python 3 it is 71.249 seconds
    # with pypy it is 22.564 seconds (second time 18.802 seconds).
    # pypy3: 16.199 seconds
    # Probably total time is connected with other optimizations.
    ###
    # (measured before get_data_context optimizations)
    # with copy_buf=False total time is 105.642 s, deepcopy time (still largest) is 20.791
    # by default, total time is 128.379, deepcopy time is 31.038
    if "PyPy" in sys.version:
        pyver = "pypy"
    else:
        pyver = "python"
    pyver += str(sys.version_info.major)
    if copy_buf:
        perf_filename = "perf_copybuf_{}.bin".format(pyver)
        # perf_filename = "perf_no_deepcopy_in_variables.bin"
        # perf_filename = "perf_usual_split.bin"
    else:
        perf_filename = "perf_no_copybuf_{}.bin".format(pyver)
    # print(perf_filename)
    if not os.path.exists(perf_filename):
        # 1 million events, takes more than 1 minute on laptop
        if copy_buf:
            cProfile.run("main_copybuf(data_file)", perf_filename)
        else:
            cProfile.run("main_no_copybuf(data_file)", perf_filename)
    stats = pstats.Stats(perf_filename)
    stats.sort_stats("cumulative")
    # copy.deepcopy is longest
    stats.print_stats(0.2)
    stats.sort_stats("tottime")
    stats.print_stats(0.2)
