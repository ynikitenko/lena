"""Lena combines calculations using *sequences*.
*Sequences* consist of *elements*.
Basic Lena sequences and element types are defined in this module.
"""
from .exceptions import (
    LenaException,
    LenaAttributeError, LenaEnvironmentError, LenaIndexError, LenaKeyError,
    LenaNotImplementedError,
    LenaRuntimeError, LenaStopFill, LenaTypeError, LenaValueError,
    LenaZeroDivisionError,
)
from .lena_sequence import LenaSequence

from .adapters import (
    Call, FillCompute, FillInto, FillRequest, Run, SourceEl
)
from .sequence import Sequence
from .source import Source
from .fill_compute_seq import FillComputeSeq
from .fill_seq import FillSeq
from .fill_request_seq import FillRequestSeq
from .split import Split, LenaSplit
from .meta import alter_sequence, flatten
from .check_sequence_type import (
    is_source,
    is_fill_compute_seq, is_fill_request_seq,
    is_fill_compute_el, is_fill_request_el,
    is_run_el,
)


__all__ = [
    'Call', 'FillCompute', 'FillInto', 'FillRequest', 'Run', 'SourceEl',
    'LenaSequence', 'Sequence', 'Source', 'Split', 'LenaSplit',
    'FillSeq',
    'FillComputeSeq', 'FillRequestSeq',
    'LenaException',
    'LenaAttributeError',
    'LenaEnvironmentError',
    'LenaIndexError', 'LenaKeyError', 'LenaNotImplementedError',
    'LenaRuntimeError', 'LenaStopFill', 'LenaTypeError',
    'LenaValueError', 'LenaZeroDivisionError',
    'is_source',
    'is_fill_compute_seq', 'is_fill_request_seq',
    'is_fill_compute_el', 'is_fill_request_el', 'is_run_el',
    'alter_sequence', 'flatten',
]
