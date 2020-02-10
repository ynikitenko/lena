"""All Lena exceptions are subclasses of :exc:`LenaException`
and corresponding Python exceptions (if they exist).
"""

# pylint: disable=missing-docstring
# Most Exceptions here are familiar to Python programmers
# and are self-explanatory.


class LenaException(Exception):
    """Base class for all Lena exceptions."""
    pass


class LenaAttributeError(LenaException, AttributeError):
    pass


class LenaEnvironmentError(LenaException, EnvironmentError):
    """The base class for exceptions
    that can occur outside the Python system,
    like IOError or OSError.
    """


class LenaIndexError(LenaException, IndexError):
    pass


class LenaKeyError(LenaException, KeyError):
    pass


class LenaNotImplementedError(LenaException, NotImplementedError):
    pass


class LenaRuntimeError(LenaException, RuntimeError):
    """Raised when an error does not belong to other categories."""
    pass


class LenaStopFill(LenaException):
    """Signal that no more fill is accepted.

    Analogous to StopIteration, but control flow is reversed.
    """
    pass


class LenaTypeError(LenaException, TypeError):
    pass


class LenaValueError(LenaException, ValueError):
    pass


class LenaZeroDivisionError(LenaException, ZeroDivisionError):
    # raised when, for example, mean can't be calculated
    pass
