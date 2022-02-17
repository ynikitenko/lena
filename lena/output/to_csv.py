"""Functions and a class to convert data to CSV."""
import lena.context
import lena.core
import lena.flow 
import lena.structures
import lena.structures.hist_functions as hf

# pylint: disable=invalid-name


def iterable_to_table(
        iterable, format_=None, header="", header_fields=(),
        row_start="", row_end="", row_separator=",",
        footer=""
    ):
    r"""Create a table from an *iterable*.

    The resulting table is yielded line by line.
    If the *header* or *footer* is empty, it is not yielded.

    *format_* controls the output of individual cells in a row.
    By default, it uses standard Python representation.
    For finer control, one should provide a sequence
    of formatting options for each column.
    For floating values it is recommended to output
    only a finite appropriate number of digits,
    because this would allow the output to be immutable
    between calls despite technical reasons.
    Default formatting allows an arbitrary number of columns
    in each cell. For tables to be well-formed, substitute
    missing values in the *iterable* for some placeholder
    like \"\", *None*, etc.

    Each row is prepended with *row_start* and appended with *row_end*.
    If it consists of several columns, they are joined by
    *row_separator*.
    Separators between rows can be added while iterating the result.

    This function can be used to convert structures
    to different formats: *csv*, *html*, *xml*, etc.

    Examples:

    >>> angles = [(3.1415*i/4, 180*i/4) for i in range(1, 5)]
    >>> format_ = ("{:.2f}", "{:.0f}")
    >>> header_fields = ("rad", "deg")
    >>>
    >>> csv_rows = iterable_to_table(
    ...    angles, format_=format_,
    ...    header="{},{}", header_fields=header_fields,
    ...    row_separator=",",
    ... )
    >>> print("\n".join(csv_rows))
    rad,deg
    0.79,45
    1.57,90
    2.36,135
    3.14,180
    >>>
    >>> html_rows = iterable_to_table(
    ...    angles, format_=format_,
    ...    header="<table>\n" + " "*4 + "<tr><td>{}</td><td>{}</td></tr>",
    ...    header_fields=header_fields,
    ...    row_start=" "*4 + "<tr><td>", row_end="</td></tr>",
    ...    row_separator="</td><td>",
    ...    footer="</table>"
    ... )
    >>> print("\n".join(html_rows))
    <table>
        <tr><td>rad</td><td>deg</td></tr>
        <tr><td>0.79</td><td>45</td></tr>
        <tr><td>1.57</td><td>90</td></tr>
        <tr><td>2.36</td><td>135</td></tr>
        <tr><td>3.14</td><td>180</td></tr>
    </table>
    >>>

    For more complex formatting use templates
    (see :class:`~.RenderLaTeX`).
    """
    if header:
        if header_fields:
            header = header.format(*header_fields)
        yield header

    # one value per line may be not such a useful case
    # to be treated separately.
    # if isinstance(format_, str):
    #     format_str = format_
    if format_ is not None:
        format_str = row_separator.join(format_)

    for row in iterable:
        try:
            cols = iter(row)
        except TypeError:
            cols = (row,)

        if format_ is None:
            yield row_start + row_separator.join(map(repr, cols)) + row_end
        else:
            yield row_start + format_str.format(*cols) + row_end

    if footer:
        yield footer


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
        * :class:`.histogram`
          (implemented only for 1- and 2-dimensional histograms).
        * any object (including :class:`.Graph`)
          with *to_csv* method.
    """

    def __init__(self, separator=",", header=None, duplicate_last_bin=True):
        """*separator* delimits values in the output text.

        *header* is a string which becomes the first line of the output.

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
            data, context = lena.flow.get_data_context(val)
            return isinstance(data, lena.structures.histogram)
            ## If *context.type* is "extended histogram", it is skipped,
            ## because it has non scalar bin content.
            # seems it's not used anywhere.
            # if lena.context.get_recursively(context, "type", None) == "extended histogram":
            #     return False

        for val in flow:
            data, context = lena.flow.get_data_context(val)

            # output.to_csv set to False
            if not lena.context.get_recursively(context, "output.to_csv", True):
                yield val
                continue

            if hasattr(data, "to_csv") and callable(data.to_csv):
                try:
                    # some classes (like Graph) can have to_csv
                    # without duplicate_last_bin keyword.
                    # If it is present, use it.
                    text = data.to_csv(
                        separator=self._separator, header=self._header,
                        duplicate_last_bin=self._duplicate_last_bin
                    )
                except TypeError:
                    text = data.to_csv(
                        separator=self._separator, header=self._header
                    )
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
