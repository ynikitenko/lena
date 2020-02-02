import sys


def flow_to_iter(flow):
    """Convert *flow* to support both ``__iter__`` and ``next``.

    *flow* must be iterable.
    If that doesn't support ``next`` (for example, a list),
    it will be converted to *iter(flow)*.
    
    Works for Python versions 2 and 3 (where next is different).
    """
    if ((sys.version_info.major == 3 and hasattr(flow, "__next__"))
        or (sys.version_info.major == 2 and hasattr(flow, "next"))):
        return flow
    else:
        return iter(flow)
