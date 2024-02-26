Structures
==========
**Histograms:**

.. currentmodule:: lena.structures.histogram
.. autosummary::

    histogram
    Histogram

.. currentmodule:: lena.structures.numpy_histogram
.. autosummary::
    NumpyHistogram

**Graph:**

.. currentmodule:: lena.structures.graph
.. autosummary::

    graph
    Graph

.. currentmodule:: lena.structures.root_graphs
.. autosummary::

    root_graph_errors
    ROOTGraphErrors

.. currentmodule:: lena.structures.elements
.. autosummary::

    HistToGraph

**Split into bins:**

.. currentmodule:: lena.structures.split_into_bins
.. autosummary::

    IterateBins
    MapBins
    SplitIntoBins

**Histogram functions:**

.. currentmodule:: lena.structures.hist_functions
.. autosummary::

    HistCell
    cell_to_string
    check_edges_increasing
    get_bin_edges
    get_bin_on_index
    get_bin_on_value
    get_bin_on_value_1d
    get_example_bin
    hist_to_graph
    init_bins
    integral
    iter_bins
    iter_bins_with_edges
    iter_cells
    make_hist_context
    unify_1_md

..
    Seems there is no way to generate the list above automatically.
    :recursive: doesn't work.

Histograms
----------

.. module:: lena.structures.histogram
.. _Histogram:

.. autoclass:: histogram
    :members:

    .. automethod:: __eq__
..
    Sphinx: it doesn't work with
    :special-members: __eq__
    Filed a bug to
    https://github.com/sphinx-doc/sphinx/issues/9818

.. autoclass:: Histogram
    :members:
    :inherited-members:
..  :members: fill, compute, run

.. module:: lena.structures
.. autoclass:: NumpyHistogram
    :members:

Graph
-----

.. module:: lena.structures.graph
.. autoclass:: graph
    :members:

.. autoclass:: Graph
    :members:

.. module:: lena.structures.root_graphs
.. autoclass:: root_graph_errors
    :members:

.. autoclass:: ROOTGraphErrors
    :members:

.. module:: lena.structures.elements
.. autoclass:: HistToGraph
    :members:

Split into bins
---------------

.. automodule:: lena.structures.split_into_bins

Histogram functions
-------------------
.. automodule:: lena.structures.hist_functions
