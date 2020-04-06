from __future__ import print_function

import cProfile
import os
import pstats

from lena.core import Sequence, Split, Source
from lena.structures import Histogram
from lena.math import mesh
from lena.output import HistToCSV, Writer, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.variables import Variable

from read_data import ReadData


def main():
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
        ]),
        MakeFilename("{variable.name}"),
        HistToCSV(),
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
    perf_filename = "perf_usual_split.txt"
    if not os.path.exists(perf_filename):
        # 1 million events, takes around 2 minutes on laptop
        cProfile.run("main()", perf_filename)
    stats = pstats.Stats(perf_filename)
    stats.sort_stats("cumulative")
    # copy.deepcopy is longest
    stats.print_stats(0.2)
    stats.sort_stats("tottime")
    # get_data_context should be used
    stats.print_stats(0.2)
