Flow
====

**Elements:**

.. currentmodule:: lena.flow
.. autosummary::

    Cache
    DropContext
    End
    Print

..     Count
..    Transform

**Functions:**

.. currentmodule:: lena.flow.functions
.. autosummary::

    get_context
    get_data
    seq_map

**Group plots:**

.. currentmodule:: lena.flow
.. autosummary::

    GroupBy
    GroupPlots
    GroupScale
    Selector

**Iterators:**

.. currentmodule:: lena.flow.iterators
.. autosummary::

    Chain
    CountFrom
    ISlice

**Split into bins:**

.. currentmodule:: lena.flow.split_into_bins
.. autosummary::

    SplitIntoBins

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
.. autoclass:: Print
    :members:
..
    .. autoclass:: Transform
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

.. currentmodule:: lena.flow
.. autoclass:: GroupBy
.. autoclass:: GroupPlots
.. autoclass:: GroupScale
.. autoclass:: Selector
    :special-members: __call__

Iterators
---------

.. automodule:: lena.flow.iterators
    :special-members: __call__

Split into bins
---------------

.. automodule:: lena.flow.split_into_bins



..  the end
    .. autoclass:: ISlice
        :members:

    .. autoclass:: CountFrom
        :special-members: __call__
