class StoreFilled(object):
    """Store filled items."""

    def __init__(self):
        self.list = []

    def fill(self, val):
        self.list.append(val)

    def __eq__(self, l):
        return self.list == l

    def reset(self):
        self.list = []

    def compute(self):
        yield self.list[:]
