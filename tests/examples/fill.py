class StoreFilled(object):
    """Store filled items."""

    def __init__(self, yield_sequentially=False):
        """If *yield_sequentially* is ``True``,
        values are yielded one by one in :meth:`compute`.
        Otherwise they are yielded in one list.
        """
        self.list = []
        self._yield_sequentially = yield_sequentially

    def fill(self, val):
        self.list.append(val)

    def __eq__(self, l):
        return self.list == l

    def reset(self):
        self.list = []

    def compute(self):
        if self._yield_sequentially:
            for val in self.list:
                yield val
        else:
            yield self.list  # [:]
