"""Functions and a class to convert histograms to CSV.

Only 1- and 2-dimensional histograms containing scalar values
can be converted.
"""
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


class HistToCSV(object):
    """Convert :class:`~lena.structures.Histogram` to text."""

    def __init__(self, separator=",", header=None, duplicate_last_bin=True):
        """*separator* delimits values in the output text,

        *header* is a string which becomes the first line of the output,

        If *duplicate_last_bin* is True,
        contents of the last bin will be written in the end twice.
        This may be useful for graphical representation:
        if last bin is from 9 to 10, then the plot may end on 9.
        This parameter allows to write bin content at 10,
        creating a horizontal step.

        Currently only 1- or 2-dimensional histograms can be dumped to CSV.
        """
        self.separator = separator
        self.header = header
        self.duplicate_last_bin = duplicate_last_bin
        # todo: header and format should be derived from histogram itself.
        # format should be passed as an option (maybe as a function).

    def run(self, flow):
        """Convert Histograms to CSV text.

        If context.type is "extended histogram", it is skipped,
        because it has non scalar bin content.

        Data is yielded as a whole CSV block.
        Context.output is updated with "filetype" = "csv".
        To generate CSV line by line,
        use *hist1d_to_csv* and *hist2d_to_csv*.

        All not converted data is yielded unchanged.
        """
        def is_writable_hist(val):
            """Test whether a value from flow can be converted to CSV."""
            data, context = lena.flow.get_data(val), lena.flow.get_context(val)
            if isinstance(data, lena.structures.Histogram):
                if "type" in context \
                    and context["type"] == "extended histogram":
                    # Not all Histograms can be written to CSV.
                    # Only those containing scalars.
                    return False
                return True
            return False
        for val in flow:
            data, context = lena.flow.get_data(val), lena.flow.get_context(val)
            if hasattr(data, "to_csv") and callable(data.to_csv):
                new_val = data.to_csv()
                new_data, new_context = (lena.flow.get_data(new_val),
                                         lena.flow.get_context(new_val))
                lena.context.update_recursively(
                    new_context, {"output": {"filetype": "csv"}}
                )
                yield (new_data, new_context)
            elif is_writable_hist(val):
                if data.dim == 1:
                    lines_iter = hist1d_to_csv(
                        data, header=self.header, separator=self.separator,
                        duplicate_last_bin=self.duplicate_last_bin,
                    )
                elif data.dim == 2:
                    lines_iter = hist2d_to_csv(
                        data, header=self.header, separator=self.separator,
                        duplicate_last_bin=self.duplicate_last_bin,
                    )
                else:
                    # todo: warning here?
                    print(
                        "{}-dimensional hist_to_csv not implemented"
                        .format(data.dim)
                    )
                    continue
                lena.context.update_recursively(context, {"output": {"filetype": "csv"}})
                # todo: rewrite without this access.
                # Why do I need this update,
                # why wasn't it in context?
                context.update(hf.make_hist_context(data, {}))
                lines = "\n".join(list(lines_iter))
                yield (lines, context)
            else:
                yield (data, context)
