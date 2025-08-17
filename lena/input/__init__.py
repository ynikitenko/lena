import warnings

warnings.warn("lena.input is deprecated. Use lena.ROOT instead.")

from ..ROOT.read_root_file import ReadROOTFile
from ..ROOT.read_root_tree import ReadROOTTree


__all__ = [
    'ReadROOTFile',
    'ReadROOTTree',
]
