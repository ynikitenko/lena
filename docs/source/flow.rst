Flow
====

**Elements:**

.. currentmodule:: lena.flow
.. autosummary::

    Cache
    Count
    DropContext
    End
    Filter
    Print
    Progress
    RunIf
    StoreFilled

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
    group_plots
    GroupScale
    MapGroup
    Selector
    And
    Or
    Not

**Iterators:**

.. currentmodule:: lena.flow.iterators
.. autosummary::

    Chain
    CountFrom
    ISlice
    Reverse
    Slice

**Split into bins:**

Since Lena 0.5 moved to :doc:`structures`.

Elements
--------
Elements form Lena sequences.
This group contains miscellaneous elements,
which didn't fit other categories.

.. module:: lena.flow
.. autoclass:: Cache
    :members:
.. autoclass:: Count
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
.. autoclass:: StoreFilled
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
.. autofunction:: group_plots
.. autoclass:: GroupScale
.. autoclass:: MapGroup

.. autoclass:: Selector
.. autoclass:: And
    :show-inheritance:
.. autoclass:: Or
    :show-inheritance:
.. autoclass:: Not
    :show-inheritance:

Iterators
---------

.. automodule:: lena.flow.iterators
    :special-members: __call__

