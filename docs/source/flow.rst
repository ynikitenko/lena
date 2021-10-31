Flow
====

**Elements:**

.. currentmodule:: lena.flow
.. autosummary::

    Cache
    DropContext
    End
    Filter
    Print
    Progress
    RunIf

..     Count
..    Transform

**Functions:**

.. currentmodule:: lena.flow.functions
.. autosummary::

    get_context
    get_data
    get_data_context
    seq_map

**Group plots:**

.. currentmodule:: lena.flow
.. autosummary::

    GroupBy
    GroupPlots
    GroupScale
    Not
    Selector

**Iterators:**

.. currentmodule:: lena.flow.iterators
.. autosummary::

    Chain
    CountFrom
    Reverse
    Slice

**Split into bins:**

.. currentmodule:: lena.flow.split_into_bins
.. autosummary::

    ReduceBinContent
    SplitIntoBins
    TransformBins
    cell_to_string
    get_example_bin

Elements
--------
Elements form Lena sequences.
This group contains miscellaneous elements,
which didn't fit other categories.

.. module:: lena.flow
.. autoclass:: Cache
    :members:
.. .. autoclass:: Count
    :members:
.. autoclass:: DropContext
    :members:
.. autoclass:: End
    :members:
.. autoclass:: Filter
    :members:
.. autoclass:: Print
    :members:
.. autoclass:: Progress
    :members:
.. autoclass:: RunIf
    :members:

Functions
---------
.. automodule:: lena.flow.functions
    :members:
.. .. automodule:: lena.flow.shell
    :members:

Group plots
-----------
.. automodule:: lena.flow.group_plots
    :no-members:
    :no-special-members:

.. currentmodule:: lena.flow
.. autoclass:: GroupBy
.. autoclass:: GroupPlots
.. autoclass:: GroupScale

.. autoclass:: Not
    :show-inheritance:
.. autoclass:: Selector

Iterators
---------

.. automodule:: lena.flow.iterators
    :special-members: __call__

Split into bins
---------------

.. automodule:: lena.flow.split_into_bins
