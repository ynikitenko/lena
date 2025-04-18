"""Functions and a class to convert data to CSV."""
import warnings

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

    .. versionadded:: 0.5
    """
    # todo: change this interface or maybe remove this function.
    # rename row_separator to field_sep, if we use this.
    if header:
        if header_fields:
            # the downside of this design: header is coupled with
            # header_fields.
            # The upside: we can easier switch
            # to new formats (leaving header fields intact).
            header = header.format(*header_fields)
        # the downside of this header implementation is also that
        # header structure can be different from row structure.
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

    Can be converted:
        * :class:`.histogram` (implemented only for 1- and 2-dimensional histograms),
        * any object with a method *rows* (for example, :class:`.Graph`).
    """
    # * any iterable object (including :class:`.graph`).

    def __init__(self, separator=",", header=None,
                 row_end="", last_row_end="",
                 duplicate_last_bin=True):
        """*separator* delimits values in the output text.
        Every row except the last one
        is ended with *row_end* and a newline.
        The last row is ended with *last_row_end* (by default empty).
        The result is yielded as one string starting from *header*.

        If *duplicate_last_bin* is ``True``, then for histograms
        contents of the last bin will be written in the end twice.
        This may be useful for graphical representation:
        if last bin is from 9 to 10, then the plot may end on 9,
        while this parameter allows to write bin content at 10,
        creating the last horizontal step.

        .. versionadded:: 0.6
           keyword arguments *row_end* and *last_row_end*.
        """
        self._separator = separator
        # todo: remove header. It should be different for each value.
        self._header = header
        # note that row_end is not allowed by RFC 4180,
        # "Common Format and MIME Type for Comma-Separated Values (CSV) Files"
        # https://datatracker.ietf.org/doc/html/rfc4180
        # However, we need it for some TeX packages to work well
        # with our tables: memoize joins them into one line,
        # so a new line would not be sufficient (causes an error).
        self._row_end = row_end
        self._last_row_end = last_row_end
        self._duplicate_last_bin = duplicate_last_bin

    def run(self, flow):
        """Convert values from *flow* to CSV text.

        Convertible data types are histograms and those that implement
        a method *rows()*, which returns an iterable of tuples
        of columns for each row.

        *context.output* is updated with {"filetype": "csv"}.
        If a data structure has a method *\\_update_context(context)*,
        it also updates the current context during the transform.
        All not converted data is yielded unchanged.
        If *output.duplicate_last_bin* is present in context,
        it takes precedence over this element's value.
        To force the common behaviour,
        one can manually update context before this element.

        If *context.output.to_csv* is ``False``, the value is skipped.

        Data is yielded as a whole CSV block.
        To generate CSV line by line,
        use :func:`hist1d_to_csv`, :func:`hist2d_to_csv`
        or :func:`iterable_to_table`.
        """
        _sentinel = object()
        for val in flow:
            data, context = lena.flow.get_data_context(val)

            # context allows conversion
            if not lena.context.get_recursively(context, "output.to_csv", True):
                yield val
                continue

            ## histogram
            if isinstance(data, lena.structures.histogram):
                # context duplicate_last_bin has higher priority
                # than that of ToCSV
                duplicate_last_bin = lena.context.get_recursively(
                    context, "output.duplicate_last_bin", _sentinel
                )
                if duplicate_last_bin is _sentinel:
                    duplicate_last_bin = self._duplicate_last_bin
                if data.dim == 1:
                    lines_iter = hist1d_to_csv(
                        data, header=self._header, separator=self._separator,
                        duplicate_last_bin=duplicate_last_bin,
                    )
                elif data.dim == 2:
                    lines_iter = hist2d_to_csv(
                        data, header=self._header, separator=self._separator,
                        duplicate_last_bin=duplicate_last_bin,
                    )
                else:
                    warnings.warn(
                        "{}-dimensional hist_to_csv not implemented"
                        .format(data.dim)
                    )
                    yield val
                    continue

                row_sep = self._row_end + "\n"
                csv = row_sep.join(lines_iter) + self._last_row_end
                data._update_context(context)
                lena.context.update_recursively(context, "output.filetype.csv")
                yield (csv, context)
                continue

            # strings can be produced by previous elements
            # (for example, they can contain file names).
            # It is an important exception for iterables, when the user
            # doesn't have to set to_csv to False explicitly.
            # There is no way to convert a string to csv
            # (even with explicit to_csv set to True),
            # because if really needed, this could be done elsewhere.
            # if isinstance(data, str):
            #     yield val
            #     continue

            rows = None
            ## provides rows property.
            # rows is a method (not a property), as it is
            # in dict.keys(), items(), etc.
            try:
                rows_iter = data.rows()
            except AttributeError:
                pass
            else:
                # todo: add a header method.
                try:
                    rows = iterable_to_table(
                        rows_iter, row_separator=self._separator, header=self._header,
                        row_end=self._row_end,
                    )
                except TypeError:
                    pass

            if rows:
                csv = "\n".join(rows) + self._last_row_end
                if (hasattr(data, "_update_context") and
                        callable(data._update_context)):
                    data._update_context(context)
                lena.context.update_recursively(context, "output.filetype.csv")
                yield (csv, context)
                continue
            # to prevent an iterable from writing, probably add
            # context.to_csv = False (however, this may be bad design).
            # Just don't pass such iterables (which won't be written)
            # to the output part, or use filters like RunIf.

            ## unknown type
            # We yield value (not (data, context)), because
            # if there was no context, we do not change that value.
            # Inserting ToCSV does not affect output
            # for irrelevant values.
            yield val
