from .pdf_to_png import PDFToPNG
from .latex_to_pdf import LaTeXToPDF
from .make_filename import MakeFilename
from .write import Writer, Write
from .to_csv import ToCSV, hist1d_to_csv, hist2d_to_csv


def raise_on_usage(clsname, modname):
    def stub(*args, **kwargs):
        raise ImportError("{} can't be used because {} is not found".
                          format(clsname, modname))
    return stub


# we do it here, because jinja2 is used at top level in render_latex.py
# (in classes' parents)
try:
    # will raise if jinja2 is not installed
    from lena.output.render_latex import RenderLaTeX  #, Template, Environment
except ImportError:
    RenderLaTeX = raise_on_usage("RenderLaTeX", "jinja2")


__all__ = [
    'PDFToPNG',
    'LaTeXToPDF',
    'MakeFilename',
    'RenderLaTeX',
    'Write',
    'Writer',
    'ToCSV', 'hist1d_to_csv', 'hist2d_to_csv',
    'RenderLaTeX'
]
