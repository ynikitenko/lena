import string

from lena.core import Source, Sequence
from lena.flow import Cache


class ASCIILowercase(object):
    """abcdefghijklmnopqrstuvwxyz"""
    def __call__(self):
        for s in string.ascii_lowercase:
            yield s


class ASCIIUppercase(object):
    def __call__(self):
        for s in string.ascii_uppercase:
            yield s


ascii_lowercase = Source(ASCIILowercase())
ascii_uppercase = Source(ASCIIUppercase())

# The Sequence's cache will be in the directory
# from which the module is called, not where this file is!
lowercase_cached_filename = "lowercase_cached.pkl"
lowercase_cached_seq = Sequence(Cache(lowercase_cached_filename))
## fill the cache - need to convert to list that first.
#lowercase_cached_seq.run(list(ascii_lowercase()))

id_ = lambda val: val
