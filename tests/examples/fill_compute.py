from __future__ import print_function

from lena.core import FillCompute


class Sum():
    def __init__(self):
        self.sum = 0

    def fill(self, val):
        if isinstance(val, tuple):
            val = val[0]
        self.sum += val

    def compute(self):
        yield self.sum

    # not used
    # def run(self, flow):
    #     fc = FillCompute(self)
    #     return fc.run(flow)


class Count():
    def __init__(self):
        self.sum = 0

    def fill(self, val):
        if isinstance(val, tuple):
            val = val[0]
        self.sum += 1

    def compute(self):
        yield self.sum

    # not used
    # def run(self, flow):
    #     fc = FillCompute(self)
    #     return fc.run(flow)

