from __future__ import print_function

import os

from lena.core import Sequence, Split, Source
from lena.flow import Print
from lena.math import mesh
from lena.output import ToCSV, Write, LaTeXToPDF, PDFToPNG
from lena.output import RenderLaTeX
from lena.structures import Histogram

from read_data import ReadData


def main():
    data_file = os.path.join("..", "data", "normal_3d.csv")
    s = Sequence(
        ReadData(),
        Split([
            (
                lambda vec: vec[0],
                Histogram(mesh((-10, 10), 10)),
                ToCSV(),
                Print(),
                Write("output", "x"),
            ),
            (
                lambda vec: vec[1],
                Histogram(mesh((-10, 10), 10)),
                ToCSV(),
                Write("output", "y"),
            ),
            # (
            #     lambda vec: vec[2],
            #     Histogram(mesh((-10, 10), 10)),
            #     ToCSV(),
            #     Write("output", ("z", "csv")),
            # ),
        ]),
        RenderLaTeX("histogram_1d.tex", "templates"),
        Write("output"),
        LaTeXToPDF(),
        PDFToPNG(),
    )
    results = s.run([data_file])
    for res in results:
        print(res)


if __name__ == "__main__":
    main()
