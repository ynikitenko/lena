Structures
==========
**Histograms:**

.. currentmodule:: lena.structures
.. autosummary::

    histogram
    Histogram
    NumpyHistogram

**Graph:**

.. currentmodule:: lena.structures.graph
.. autosummary::

    Graph

.. currentmodule:: lena.structures.elements
.. autosummary::

    HistToGraph

**Split into bins:**

.. currentmodule:: lena.structures.split_into_bins
.. autosummary::

    IterateBins
    MapBins
    SplitIntoBins
    cell_to_string
    get_example_bin

**Histogram functions:**

.. currentmodule:: lena.structures.hist_functions
.. autosummary::

    HistCell
    check_edges_increasing
    get_bin_edges
    get_bin_on_index
    get_bin_on_value
    get_bin_on_value_1d
    hist_to_graph
    init_bins
    integral
    iter_bins
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
.. autoclass:: Graph
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
