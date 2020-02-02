from __future__ import print_function

import os

from lena.core import Sequence, Source
from lena.math import mesh
from lena.output import HistToCSV, Writer, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.structures import Histogram

from read_data import ReadData


def main():
    data_file = os.path.join("..", "data", "normal_3d.csv")
    s = Sequence(
        ReadData(),
        lambda dt: (dt[0][0], dt[1]),
        Histogram(mesh((-10, 10), 10)),
        HistToCSV(),
        MakeFilename("x"),
        Writer("output"),
        RenderLaTeX("histogram_1d.tex"),
        Writer("output"),
        LaTeXToPDF(),
        PDFToPNG(),
    )
    results = s.run([data_file])
    print(list(results))

if __name__ == "__main__":
    main()
