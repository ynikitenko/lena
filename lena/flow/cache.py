"""Cache (pickle) the flow."""
import os
import pickle
import sys

import lena.core 
import lena.context

if sys.version_info.major == 2:
    import cPickle


class Cache(object):
    """Cache the flow passing through.

    On the first run, dump the whole flow to a file
    (and yield the flow unaltered).
    On subsequent runs, load the flow from that file
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
    :class:`Cache` will read the data from that file
    and no other processing will be done.
    If the *stats.pkl* cache doesn't exist,
    but the cache for histograms exists, it will be used
    and no previous processing (from *ReadFiles* to *MakeHistograms*)
    will occur.
    If both caches were not filled yet, processing will go as usual.

    Only pickleable objects can be cached
    (otherwise a *pickle.PickleError* will be raised).

    Warning
    -------
        The pickle module is not secure against erroneous
        or maliciously constructed data.
        Never unpickle data from an untrusted source.
    """

    def __init__(self, filename, recompute=False,
                 method="cPickle", protocol=2):
        """*filename* is the name of file where to store the cache.
        It can be given *.pkl* extension.

        If *recompute* is ``True``,
        an existing cache will always be overwritten.
        This option is typically used if one wants to define
        cache behaviour from the command line.

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
        self._orig_filename = filename
        if '{' in filename:
            self._format_context = lena.context.format_context(filename)

        self.protocol = protocol
        self._recompute = recompute
        # used by meta elements
        self.is_cache = True

        cache_dir = os.path.dirname(self._filename)
        if cache_dir:
            # could be empty for files in current directory
            if sys.version_info.major == 2:
                # race condition, no good solution in Python 2.
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir)
            else:
                # Python 3 optimal way
                os.makedirs(cache_dir, exist_ok=True)

    def cache_exists(self):
        """Return ``True`` if file with cache exists and is readable.

        If *recompute* was ``True`` during the initialization,
        pretend that cache does not exist (return ``False``).
        """
        if self._recompute:
            return False
        return os.access(self._filename, os.R_OK)

    def drop_cache(self):
        """Remove file with cache if that exists, pass otherwise.

        If cache exists and is readable, but could not be deleted,
        :exc:`.LenaEnvironmentError` is raised."""
        try:
            os.remove(self._filename)
        except OSError as err:
            if self.cache_exists():
                raise lena.core.LenaEnvironmentError(
                    "Cache {}".format(self._filename) +
                    " exists and readable, but can't be removed"
                )
            raise err

    def run(self, flow):
        """Load cache or fill it.

        If we can read *filename*, load flow from there.
        Otherwise use the incoming *flow* and fill the cache.
        All loaded or passing items are yielded.
        """
        if self.cache_exists():
            # Load cache, ignore flow.
            # Race condition
            # (if file is changed or deleted right after the check),
            # but it will be always present because of lazy evaluation.
            return self._load_flow()

        # can't copy code here due to unknown reasons (stops working)
        return self._dump_flow_and_yield(flow)

    def _set_context(self, context):
        # copied from output.Write
        if '{' not in self._orig_filename:
            return
        try:
            filename = self._format_context(context)
        except lena.core.LenaKeyError:
            pass
        else:
            self._filename = filename

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
        if hasattr(seq, '__iter__'):
            last_cache_filled_ind = None
            for ind in reversed(range(len(seq))):
                el = seq[ind]
                if isinstance(el, lena.flow.Cache):
                    if el.cache_exists():
                        last_cache_filled_ind = ind
                        break
            if last_cache_filled_ind is not None:
                return lena.core.Source(
                    lena.core.SourceEl(seq[last_cache_filled_ind],
                                       call="_load_flow"),
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

    def _dump_flow_and_yield(self, flow):
        # fill cache and yield values
        with open(self._filename, "wb") as f:
            dump = lambda val: self._dump(val, f, self.protocol)
            for val in flow:
                # if there were an error in a next element,
                # our value will be saved first (before yielding)
                dump(val)
                yield val


    def _load_flow(self):
        """Load flow from self.filename."""
        with open(self._filename, "rb") as f:
            while True:
                try:
                    val = self._load(f)
                    yield val
                except EOFError:
                    break
