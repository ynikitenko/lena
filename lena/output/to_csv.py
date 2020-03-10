"""Functions and a class to convert data to CSV."""
from __future__ import print_function

import lena.context
import lena.core
import lena.flow 
import lena.structures
import lena.structures.hist_functions as hf

# pylint: disable=invalid-name


def hist1d_to_csv(hist, header=None, separator=',', duplicate_last_bin=True):
    """Yield CSV-formatted strings for a one-dimensional histogram."""
    bins_ = hist.bins
    edges_ = hist.edges
    bin_content = None
    if header:
        yield header
    for x_ind, x in enumerate(edges_[:-1]):
        bin_content = bins_[x_ind]
        try:
            bin_content = float(bin_content)
        except TypeError:
            raise lena.core.LenaTypeError(
                "Wrong type passed as float bin content: {}"
                .format(bin_content)
            )
        line = "{:f}{}{:f}".format(x, separator, bin_content)
        yield line
    if duplicate_last_bin:
        bin_content = bins_[-1]
        try:
            bin_content = float(bin_content)
        except TypeError:
            raise lena.core.LenaTypeError(
                "Wrong type passed as float bin content: {}"
                .format(bin_content)
            )
        x = edges_[-1]
        try:
            line = "{:f}{}{:f}".format(x, separator, bin_content)
        except ValueError:
            raise lena.core.LenaValueError(
                "Could not format values: {}, {}, {}".
                format(x, separator, bin_content)
            )
        yield line


def hist2d_to_csv(hist, header=None, separator=',', duplicate_last_bin=True):
    """Yield CSV-formatted strings for a two-dimensional histogram."""
    edges = hist.edges
    bins = hist.bins
    if header:
        yield header
    # todo: this can be passed as a parameter.
    def format_line(x, y, bin_content):
        return "{:f}{}{:f}{}{:f}".format(x, separator, y, separator, bin_content)
    for x_ind, x in enumerate(edges[0][:-1]):
        for y_ind, y in enumerate(edges[1][:-1]):
            bin_content = bins[x_ind][y_ind]
            yield format_line(x, y, bin_content)
        if duplicate_last_bin:
            y = edges[1][-1]
            yield format_line(x, y, bin_content)
    if duplicate_last_bin:
        x = edges[0][-1]
        for y_ind, y in enumerate(edges[1][:-1]):
            bin_content = bins[x_ind][y_ind]
            yield format_line(x, y, bin_content)
        y = edges[1][-1]
        yield format_line(x, y, bin_content)


class ToCSV(object):
    """Convert data to CSV text.

    These objects are converted:
        * :class:`~lena.structures.Histogram`
          (implemented only for 1- and 2-dimensional histograms).
        * any object (including :class:`~lena.structures.Graph`)
          with *to_csv* method.
    """

    def __init__(self, separator=",", header=None, duplicate_last_bin=True):
        """*separator* delimits values in the output text,

        *header* is a string which becomes the first line of the output,

        If *duplicate_last_bin* is ``True``,
        contents of the last bin will be written in the end twice.
        This may be useful for graphical representation:
        if last bin is from 9 to 10, then the plot may end on 9,
        while this parameter allows to write bin content at 10,
        creating the last horizontal step.
        """
        self._separator = separator
        self._header = header
        self._duplicate_last_bin = duplicate_last_bin

    def run(self, flow):
        """Convert values from *flow* to CSV text.

        *Context.output* is updated with {"filetype": "csv"}.
        All not converted data is yielded unchanged.

        If *data* has *to_csv* method, it must accept
        keyword arguments *separator* and *header*
        and return text.

        If *context.output.to_csv* is False,
        the value is skipped.

        Data is yielded as a whole CSV block.
        To generate CSV line by line,
        use :func:`hist1d_to_csv` and :func:`hist2d_to_csv`.
        """
        def is_writable_hist(val):
            """Test whether a value from flow can be converted to CSV."""
            data, context = lena.flow.get_data(val), lena.flow.get_context(val)
            return isinstance(data, lena.structures.Histogram)
            ## If *context.type* is "extended histogram", it is skipped,
            ## because it has non scalar bin content.
            # seems it's not used anywhere.
            # if lena.context.get_recursively(context, "type", None) == "extended histogram":
            #     return False

        for val in flow:
            data, context = lena.flow.get_data(val), lena.flow.get_context(val)

            # output.to_csv set to False
            if not lena.context.get_recursively(context, "output.to_csv", True):
                yield val
                continue

            if hasattr(data, "to_csv") and callable(data.to_csv):
                text = data.to_csv(separator=self._separator,
                                      header=self._header)
                ## *data.to_csv* may produce context,
                ## which in this case updates the current context.
                # no need to allow this. All necessary context
                # must be contained in the data and provided with that.
                # new_val = data.to_csv(separator=self._separator,
                #                       header=self._header)
                # new_data, new_context = (lena.flow.get_data(new_val),
                #                          lena.flow.get_context(new_val))
                # lena.context.update_recursively(context, new_context)
                # yield (new_data, new_context)
                lena.context.update_recursively(context, "output.filetype.csv")
                yield (text, context)
            elif is_writable_hist(val):
                if data.dim == 1:
                    lines_iter = hist1d_to_csv(
                        data, header=self._header, separator=self._separator,
                        duplicate_last_bin=self._duplicate_last_bin,
                    )
                elif data.dim == 2:
                    lines_iter = hist2d_to_csv(
                        data, header=self._header, separator=self._separator,
                        duplicate_last_bin=self._duplicate_last_bin,
                    )
                else:
                    # todo: warning here
                    print(
                        "{}-dimensional hist_to_csv not implemented"
                        .format(data.dim)
                    )
                    yield val
                    continue
                lena.context.update_recursively(context, "output.filetype.csv")
                lines = "\n".join(list(lines_iter))
                yield (lines, context)
            else:
                yield val


class HistToCSV(ToCSV):
    """Deprecated. Use :class:`ToCSV` instead."""
    def __init__(self, **kwargs):
        print("HistToCSV is deprecated. Use ToCSV instead.")
        super(HistToCSV, self).__init__(**kwargs)
