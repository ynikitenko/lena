import collections


class Progress(object):
    """Print progress (how much data was processed and remains)."""

    def __init__(self, name="", format=""):
        """*name*, if set, customizes the output
        with the collective name of values being processed
        (for example, "events").

        *format* is a formatting string for the output.
        It will be passed keyword arguments *percent*, *index*,
        *total* and *name*.

        Use :class:`Progress` when large processing will
        be done after that. For example, if you have files
        with much data, put this element after generating file
        names, but before reading files.
        To print indices without reading the whole flow,
        use :class:`CountFrom` and :class:`Print`.

        Progress is estimated based on the number of items processed
        by this element.
        It does not take into account the creation of final plots
        or the difference in the processing time for different values.

        Warning
        -------
            To measure progress, the whole flow is consumed.
        """
        if format:
            self._format = format
        else:
            # we put the exact formatting string here
            # (not as default arg) only to free the method description.
            # Don't know how to get rid of the first printed space.
            self._format = "{percent:> 4.0f}% [{index}/{total}] {name}"
        self._name = name
        # To take into account plurals nouns,
        # use a special class for the format string.
        # If you need to estimate the remaining time,
        # make a feature request.
        # Other ideas:
        # - add options for printing on_each_nth_event,
        #   on_each_nth_percent=5 (or 0.5)
        # -- think they are not needed,
        #    because files are supposed to be big:
        #    output after every file won't clutter.

    def run(self, flow):
        """Consume the *flow*, then yield values one by one
        and print progress.
        """
        format = self._format
        name = self._name
        values = collections.deque(flow)
        total = len(values)
        for index in range(1, total+1):
            # we use the range from 1, since otherwise
            # it would output like "2 events from 3",
            # which is not correct: that is 3/3.
            # We use a deque to empty it faster
            yield values.popleft()
            percent = 100.*index / total
            print(format.format(percent=percent, index=index, total=total,
                                name=name))
