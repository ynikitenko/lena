from __future__ import print_function

import cProfile
import os
import pstats

from lena.core import Sequence, Split, Source
from lena.structures import Histogram
from lena.math import mesh
from lena.output import ToCSV, Writer, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.variables import Variable

from read_data import ReadData


def main(copy_buf=True):
    # 10**6 events
    data_file = os.path.join("..", "data", "normal_3d_large.csv")
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
        ],
            copy_buf=copy_buf,
        ),
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


if __name__ == "__main__":
    copy_buf = False
    # copy_buf = True
    # with copy_buf=False total time is 105.642 s, deepcopy time (still largest) is 20.791
    # by default, total time is 128.379, deepcopy time is 31.038
    # (measured before get_data_context optimizations)
    if copy_buf:
        perf_filename = "perf_usual_split.txt"
    else:
        perf_filename = "perf_no_copybuf.txt"
    if not os.path.exists(perf_filename):
        # 1 million events, takes around 2 minutes on laptop
        cProfile.run("main(copy_buf={})".format(copy_buf), perf_filename)
    stats = pstats.Stats(perf_filename)
    stats.sort_stats("cumulative")
    # copy.deepcopy is longest
    stats.print_stats(0.2)
    stats.sort_stats("tottime")
    # get_data_context should be used
    stats.print_stats(0.2)
