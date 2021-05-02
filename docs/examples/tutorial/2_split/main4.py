from __future__ import print_function

import os

import lena.context
import lena.flow
from lena.core import Sequence, Split, Source
from lena.structures import Histogram
from lena.math import mesh
from lena.output import ToCSV, Write, LaTeXToPDF, PDFToPNG
from lena.output import MakeFilename, RenderLaTeX
from lena.variables import Variable, Compose, Combine

from read_data import ReadDoubleEvents


positron = Variable(
    "positron", latex_name="e^+",
    getter=lambda double_ev: double_ev[0], type="particle"
)
neutron = Variable(
    "neutron", latex_name="n",
    getter=lambda double_ev: double_ev[1], type="particle"
)
x = Variable("x", lambda vec: vec[0], latex_name="x", unit="cm", type="coordinate")
y = Variable("y", lambda vec: vec[1], latex_name="y", unit="cm", type="coordinate")
z = Variable("z", lambda vec: vec[2], latex_name="z", unit="cm", type="coordinate")

coordinates_1d = [
    (
        coordinate,
        Histogram(mesh((-10, 10), 10)),
    )
    for coordinate in [
        Compose(particle, coord)
            for coord in x, y, z
            for particle in positron, neutron
    ]
]


def select_template(val):
    data, context = lena.flow.get_data_context(val)
    if lena.context.get_recursively(context, "histogram.dim", None) == 2:
        return "histogram_2d.tex"
    else:
        return "histogram_1d.tex"


def main():
    data_file = os.path.join("..", "data", "double_ev.csv")
    write = Write("output")
    s = Sequence(
        ReadDoubleEvents(),
        Split(
            coordinates_1d
            + 
            [(
                particle,
                Combine(x, y, name="xy"),
                Histogram(mesh(((-10, 10), (-10, 10)), (10, 10))),
                MakeFilename("{{variable.particle}}/{{variable.name}}"),
             )
             for particle in positron, neutron
            ]
        ),
        MakeFilename("{{variable.particle}}/{{variable.coordinate}}"),
        ToCSV(),
        write,
        RenderLaTeX(select_template, template_path="templates"),
        write,
        LaTeXToPDF(),
        PDFToPNG(),
    )
    results = s.run([data_file])
    for res in results:
        print(res)


if __name__ == "__main__":
    main()
