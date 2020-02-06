class Add(object):

    def __init__(self, num):
        self.num = num

    def __call__(self, x):
        return self.num + x
