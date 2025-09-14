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


**DictTable:**

.. currentmodule:: lena.structures.dict_table
.. autosummary::

    dict_table
    DictTable


**Elements:**

.. currentmodule:: lena.structures.elements
.. autosummary::

    HistToGraph
    ScaleTo

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

    .. automethod:: __add__
    .. automethod:: __mul__
    .. automethod:: __sub__
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


DictTable
---------
A :class:`.dict_table` facilitates template rendering
of large number of values.
First, one combines the computed values into a table
with the element :class:`.DictTable`. Data parts of
the values should be dictionaries, context parts will be
automatically merged into them. The computed :class:`.dict_table`
can be easily used in a LaTeX template.
A simplified example of a jinja2 template for a table with three fit coefficients 
for six data samples:

.. code-block:: latex

    \begin{tabular}{ll*{3}{c}}
    \toprule
        &   & $a_0$ & $a_1$ & $a_2$ \\
    \midrule
    \BLOCK{ for detector in ("FDI", "FDII", "ND") }
    \BLOCK{ for data_type in ("data", "MC") }
    \BLOCK{ set dt = context["data.detector." + detector]["data.data_type." + data_type]["dt"] }
    \VAR{ detector if loop.index == 1 } & \VAR{ data_type } & \VAR{ dt.coefs[0] -}
    \VAR{ " &" } \VAR{ dt.coefs[1] } & \VAR{ dt.coefs[2] -} \\
    \BLOCK{ endfor }
    \BLOCK{ if detector != "ND" }
    \midrule
    \BLOCK{ endif }
    \BLOCK{ endfor }
    \bottomrule
    \end{tabular}

Note how the sample is selected for each row with
``context["data.detector." + detector]["data.data_type." + data_type]``,
and the nested object with needed coefficients is retrieved with its key *dt*.

.. seealso:: sophisticated selections are supported by *pandas.DataFrame.loc*; however,
   they require flattened structures and indexing the rows.

.. module:: lena.structures.dict_table

.. autoclass:: dict_table
    :members:

    .. automethod:: __getitem__

.. autoclass:: DictTable


Elements
--------

.. module:: lena.structures.elements
.. autoclass:: HistToGraph
    :members:

.. autoclass:: ScaleTo
    :members:

Split into bins
---------------

.. automodule:: lena.structures.split_into_bins

Histogram functions
-------------------
.. automodule:: lena.structures.hist_functions
