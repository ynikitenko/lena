import os
import sys

import lena.math
from lena.core import Sequence, Source
from lena.flow import Print, Cache, Slice
from lena.context import Context, UpdateContext
from lena.output import Write, ToCSV, RenderLaTeX, LaTeXToPDF, PDFToPNG
from lena.structures import Histogram


data_path = os.path.join("..", "tutorial", "data")
data_file = os.path.join(data_path, "normal_3d_large.csv")


def get_filenames():
    filenames = [data_file]
    for filename in filenames:
        yield filename


class GetCoordinates():
    """Read coordinates from CSV files."""
    def __init__(self):
        pass

    def run(self, flow):
        for file_ in flow:
            with open(file_) as fil:
                for line in fil:
                    yield [float(coord) for coord in line.split(',')]

## note that there is no coupling between these functions


def main():
    filenames = get_filenames()
    write = Write("output")

    s = Sequence(
        GetCoordinates(),
        lambda coord: coord[0],  # x
        Histogram(lena.math.mesh((-10, 10), 100)),
        UpdateContext("output.filename", "x"),
        # output
        ToCSV(),
        write,
        RenderLaTeX("histogram_1d_simple.tex"),
        write,
        LaTeXToPDF(),
        PDFToPNG(),
    )

    return s.run(filenames)
    # return s()
    # /bin/time with already produced plot:
    # 3.26user 0.00system 0:03.27elapsed 99%CPU (0avgtext+0avgdata 18000maxresident)k
    # 0inputs+0outputs (0major+2735minor)pagefaults 0swaps
    # PyPy:
    # 1.11user 0.03system 0:01.21elapsed 93%CPU (0avgtext+0avgdata 92996maxresident)k
    # 12168inputs+736outputs (59major+12457minor)pagefaults 0swaps


def read_data(file_):
    """Read lines of a file, used only for performance measurement."""
    with open(file_) as fil:
        for line in fil:
            coord_ = [float(coord) for coord in line.split(',')]


if __name__ == "__main__":
    if "read_data" in sys.argv:
        read_data(data_file)
        sys.exit(0)
        # without split and float():
        # Python results (PyPy slower):
        # 0.13user 0.01system 0:00.14elapsed 99%CPU (0avgtext+0avgdata 17840maxresident)k
        # 0inputs+0outputs (0major+2709minor)pagefaults 0swaps
        # with split and float():
        # Python results (PyPy similar):
        # 0.81user 0.02system 0:00.84elapsed 99%CPU (0avgtext+0avgdata 18084maxresident)k
        # 0inputs+0outputs (0major+2713minor)pagefaults 0swaps

    for result in main():
        print(result)
