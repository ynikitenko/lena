lena.core
=========

**Sequences:**

.. currentmodule:: lena.core
.. autosummary::

    Sequence
    Source
    FillComputeSeq
    FillRequestSeq
    Split

**Adapters:**

.. currentmodule:: lena.core.adapters
.. autosummary::

    Call
    FillCompute
    FillInto
    FillRequest
    Run
    SourceEl

**Exceptions:**

.. currentmodule:: lena.core.exceptions
.. autosummary::

    LenaAttributeError
    LenaEnvironmentError
    LenaException
    LenaIndexError
    LenaKeyError
    LenaRuntimeError
    LenaStopFill
    LenaTypeError
    LenaValueError

Sequences
---------

.. currentmodule:: lena.core
..  automodule documents many classes here, not only requested ones.
    .. automodule:: lena.core
        :no-members:
        :members: Sequence, Source, FillComputeSeq, FillRequestSeq, Split
        :special-members: __call__
        :exclude-members: Call, LenaException

.. automodule:: lena.core
    :no-members:

.. _Sequence:
.. autoclass:: Sequence
    :members:

.. _Source:
.. autoclass:: Source
    :members:
    :special-members: __call__

.. autoclass:: FillComputeSeq
    :members:

.. autoclass:: FillRequestSeq
    :members:

.. _Split:
.. autoclass:: Split
    :members:

..
    :special-members: __call__

Adapters
--------
.. automodule:: lena.core.adapters
    :special-members: __call__

..  .. _Call:
    .. autoclass:: Call
        :members:
        :special-members: __call__
    
    .. _FillCompute:
    .. autoclass:: FillCompute
        :members:
    
    .. _FillRequest:
    .. autoclass:: FillRequest
        :members:
    
    .. _Run:
    .. autoclass:: Run
        :members:

Exceptions
----------

.. automodule:: lena.core.exceptions
    :show-inheritance:

..  End
    .. _LenaException:
    .. autoclass:: LenaException 
        :show-inheritance:

    .. _LenaIndexError:
    .. autoclass:: LenaIndexError
        :show-inheritance:

    .. _LenaTypeError:
    .. autoclass:: LenaTypeError
        :show-inheritance:

    .. _LenaValueError:
    .. autoclass:: LenaValueError
        :show-inheritance:

    .. 
        .. _isclose_label:
        .. autofunction:: isclose

..  .. automodapi:: lena.core.adapters
    .. automodsumm:: lena.core.adapters
        :skip: print_function
..
    :no-inheritance-diagram:
    :no-heading:

..
    doesn't show python parent classes
    .. automod-diagram:: lena.core.exceptions

    .. automodsumm:: lena.core.exceptions
        :inherited-members:

