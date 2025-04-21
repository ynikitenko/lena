from .elements import HistToGraph, ScaleTo
from .graph import graph, Graph
from .histogram import histogram, Histogram
from .hist_functions import (
    cell_to_string,
    check_edges_increasing,
    get_bin_edges,
    get_bin_on_value_1d, get_bin_on_value, get_bin_on_index,
    get_example_bin,
    HistCell,
    hist_to_graph,
    init_bins,
    integral,
    iter_bins,
    iter_bins_with_edges,
    iter_cells,
    unify_1_md
)
from .numpy_histogram import NumpyHistogram
from .root_graphs import root_graph_errors, ROOTGraphErrors
from .split_into_bins import (
    IterateBins,
    MapBins,
    SplitIntoBins,
)


__all__ = [
    # structures
    'graph', 'Graph',
    'histogram',
    'HistCell',
    'Histogram',
    'HistToGraph',
    'NumpyHistogram',
    'root_graph_errors',
    'ROOTGraphErrors',
    # hist functions
    'check_edges_increasing',
    'cell_to_string',
    'get_bin_edges',
    'get_bin_on_value_1d', 'get_bin_on_value', 'get_bin_on_index',
    'get_example_bin',
    'hist_to_graph',
    'init_bins',
    'integral',
    'iter_bins',
    'iter_bins_with_edges',
    'iter_cells',
    'unify_1_md',
    # split into bins
    'SplitIntoBins',
    'IterateBins',
    'MapBins',
]
