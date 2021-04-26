"""Cache (pickle) flow."""
from __future__ import print_function

import sys
import os
import pickle

import lena.core 

if sys.version_info.major == 2:
    import cPickle


class Cache(object):
    """Cache flow passing through.

    On the first run, dump all flow to file
    (and yield the flow unaltered).
    On subsequent runs, load all flow from that file
    in the original order.

    Example::

        s = Source(
                 ReadFiles(),
                 ReadEvents(),
                 MakeHistograms(),
                 Cache("histograms.pkl"),
                 MakeStats(),
                 Cache("stats.pkl"),
              )

    If *stats.pkl* exists,
    :class:`Cache` will read data flow from that file
    and no other processing will be done.
    If the *stats.pkl* cache doesn't exist,
    but the cache for histograms exist, it will be used
    and no previous processing (from *ReadFiles* to *MakeHistograms*)
    will occur.
    If both caches are not filled yet, processing will run as usually.

    Only pickleable objects can be cached
    (otherwise a *pickle.PickleError* is raised).

    Warning
    -------
        The pickle module is not secure against erroneous
        or maliciously constructed data.
        Never unpickle data from an untrusted source.
    """

    def __init__(self, filename, method="cPickle", protocol=2):
        """*filename* is the name of file where to store the cache.
        You can give it *.pkl* extension.

        *method* can be *pickle* or *cPickle* (faster pickle).
        For Python 3 they are same.

        *protocol* is pickle protocol.
        Version 2 is the highest supported by Python 2.
        Version 0 is "human-readable" (as noted in the documentation).
        3 is recommended if compatibility
        between Python 3 versions is needed.
        4 was added in Python 3.4.
        It adds support for very large objects,
        pickling more kinds of objects,
        and some data format optimizations.
        """
        if method == "pickle" or sys.version_info.major > 2:
            self._dump = pickle.dump
            self._load = pickle.load
        elif method == "cPickle":
            self._dump = cPickle.dump
            self._load = cPickle.load
        else:
            raise lena.core.LenaValueError(
                "Cache method should be one of pickle of cPickle."
            )

        self._filename = filename
        self._method = method
        self._protocol = protocol

    def cache_exists(self):
        """Return ``True`` if file with cache exists and is readable."""
        return os.access(self._filename, os.R_OK)

    def drop_cache(self):
        """Remove file with cache if that exists, pass otherwise.

        If cache exists and is readable, but could not be deleted,
        :exc:`.LenaEnvironmentError` is raised."""
        try:
            os.remove(self._filename)
        except OSError:
            if self.cache_exists():
                raise lena.core.LenaEnvironmentError(
                    "Cache {}".format(self._filename) +
                    " exists and readable, but can't be removed"
                )

    def run(self, flow):
        """Load cache or fill it.

        If we can read *filename*, load flow from there.
        Otherwise use the incoming *flow* and fill the cache.
        All loaded or passing items are yielded.
        """
        if self.cache_exists():
            # race condition in this implementation
            # (if file is changed or deleted right after the check)
            return self._load_flow()
        else:
            return self._pass_and_dump_flow(flow)

    @staticmethod
    def alter_sequence(seq):
        """If the Sequence *seq* contains a :class:`Cache`,
        which has an up-to-date cache,
        a :class:`.Source` is built
        based on the flattened *seq* and returned.
        Otherwise the *seq* is returned unchanged.
        """
        # it will check for any Caches, not just this one
        import lena.flow, lena.core
        orig_seq = seq
        seq = lena.core.flatten(seq)
        last_cache_filled_ind = None
        if hasattr(seq, '__iter__'):
            for ind in reversed(range(len(seq))):
                el = seq[ind]
                if isinstance(el, lena.flow.Cache):
                    if el.cache_exists():
                        last_cache_filled_ind = ind
                        break
            if last_cache_filled_ind is not None:
                return lena.core.Source(
                    lena.core.SourceEl(seq[last_cache_filled_ind], call="_load_flow"),
                    *seq[last_cache_filled_ind+1:]
                )
        else:
            # Cache element
            if isinstance(seq, Cache):
                if seq.cache_exists():
                    return lena.core.Source(
                        lena.core.SourceEl(seq, call="_load_flow")
                    )

        return orig_seq


    def _load_flow(self):
        """Load flow from self.filename."""
        with open(self._filename, "rb") as f:
            while True:
                try:
                    val = self._load(f)
                    yield val
                except EOFError:
                    break

    def _pass_and_dump_flow(self, flow):
        """Dump flow into self.filename.

        Flow is simultaneously yielded.
        """
        with open(self._filename, "wb") as f:
            dump = lambda val: self._dump(val, f, self._protocol)
            for val in flow:
                dump(val)
                yield val
