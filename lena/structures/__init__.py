from lena.structures.graph import Graph
from lena.structures.histogram import Histogram
from lena.structures.hist_functions import (
    check_edges_increasing,
    get_bin_on_value_1d, get_bin_on_value, get_bin_on_index,
    hist_to_graph,
    init_bins,
    integral,
    iter_bins,
    make_hist_context,
    unify_1_md
)

imported = []
try:
    from lena.structures.numpy_histogram import NumpyHistogram
except ImportError:
    pass
else:
    imported.append('NumpyHistogram')

__all__ = [
    'Graph', 'Histogram',
    'check_edges_increasing',
    'get_bin_on_value_1d', 'get_bin_on_value', 'get_bin_on_index',
    'hist_to_graph',
    'init_bins',
    'integral',
    'iter_bins',
    'make_hist_context',
    'unify_1_md'
] + imported
