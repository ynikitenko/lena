"""Lena combines calculations using *sequences*.

*Sequences* consist of *elements*.
Basic Lena sequences and element types are defined in this module.
"""
from lena.core.exceptions import (
    LenaException,
    LenaAttributeError, LenaEnvironmentError, LenaIndexError, LenaKeyError,
    LenaNotImplementedError,
    LenaRuntimeError, LenaStopFill, LenaTypeError, LenaValueError
)
from lena.core.lena_sequence import LenaSequence

from lena.core.adapters import (
    Call, FillCompute, FillInto, FillRequest, Run, SourceEl
)
from lena.core.sequence import Sequence
from lena.core.source import Source
from lena.core.fill_compute_seq import FillComputeSeq
from lena.core.fill_seq import FillSeq
from lena.core.fill_request_seq import FillRequestSeq
from lena.core.split import Split
from .meta import alter_sequence, flatten
from .check_sequence_type import (
    is_source,
    is_fill_compute_seq, is_fill_request_seq,
    is_fill_compute_el, is_fill_request_el,
    is_run_el,
)


__all__ = [
    'Call', 'FillCompute', 'FillInto', 'FillRequest', 'Run', 'SourceEl',
    'LenaSequence', 'Sequence', 'Source', 'Split',
    'FillSeq',
    'FillComputeSeq', 'FillRequestSeq',
    'LenaException',
    'LenaAttributeError',
    'LenaEnvironmentError',
    'LenaIndexError', 'LenaKeyError', 'LenaNotImplementedError',
    'LenaRuntimeError', 'LenaStopFill', 'LenaTypeError',
    'LenaValueError',
    'is_source',
    'is_fill_compute_seq', 'is_fill_request_seq',
    'is_fill_compute_el', 'is_fill_request_el', 'is_run_el',
    'alter_sequence', 'flatten',
]
