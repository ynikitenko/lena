collect_ignore = []

try:
    import numpy
except ImportError:
    collect_ignore.append("lena/structures/numpy_histogram.py")
