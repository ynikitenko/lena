import os
import sys

import lena.math
from lena.core import Sequence, Source, Split
from lena.variables import Variable, Combine
from lena.flow import Print, Cache, Slice
from lena.context import Context, UpdateContext
from lena.output import (
    Write, ToCSV, RenderLaTeX, LaTeXToPDF, PDFToPNG, MakeFilename
)
from lena.structures import Histogram

from lena_xs import get_filenames, GetCoordinates, data_file


def main():
    write = Write("output")

    s = Source(
        get_filenames,
        GetCoordinates(),
        Split([
            (
                Variable("x", lambda coord: coord[0]),
                Histogram(lena.math.mesh((-10, 10), 100)),
            ),
            (
                Variable("y", lambda coord: coord[1],
                         latex_name="y", unit="mm"),
                Histogram(lena.math.mesh((-10, 10), 100)),
            ),
        ]),
        MakeFilename("{{variable.name}}"),
        # UpdateContext("output.filename", "x"),
        ToCSV(),
        write,
        RenderLaTeX("histogram_1d.tex"),
        write,
        LaTeXToPDF(),
        PDFToPNG(),
    )

    return s()


if __name__ == "__main__":
    for result in main():
        print(result)

    # Python:
    # 17.09user 0.00system 0:17.10elapsed 99%CPU (0avgtext+0avgdata 18540maxresident)k
    # 0inputs+0outputs (0major+2851minor)pagefaults 0swaps
    # PyPy:
    # 6.34user 0.06system 0:06.45elapsed 99%CPU (0avgtext+0avgdata 93756maxresident)k
    # 0inputs+0outputs (0major+12357minor)pagefaults 0swaps
