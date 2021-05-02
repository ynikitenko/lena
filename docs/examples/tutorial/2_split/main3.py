from __future__ import print_function

import os

from lena.core import Sequence, Split, Source
from lena.structures import Histogram
from lena.math import mesh
from lena.output import ToCSV, Write, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.variables import Variable

from read_data import ReadData


def main():
    data_file = os.path.join("..", "data", "normal_3d.csv")
    write = Write("output")
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
        MakeFilename("{{variable.name}}"),
        ToCSV(),
        write,
        RenderLaTeX("histogram_1d.tex", "templates"),
        write,
        LaTeXToPDF(),
        PDFToPNG(),
    )
    results = s.run([data_file])
    for res in results:
        print(res)


if __name__ == "__main__":
    main()
