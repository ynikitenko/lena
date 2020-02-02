from operator import add

class Add(object):
    def __init__(self, num):
        self.num = num
    # def __add__(self, x):
    #     return x + self.num
    def __call__(self, x):
        return self.num + x
