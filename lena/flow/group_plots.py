"""Group several plots into one.

Since data can be produced in different places,
several classes are needed to support this.
First, the plots of interest must be selected
(for example, one-dimensional histograms).
This is done by :class:`.Selector`.
Selected plots must be grouped.
For example, we may want to plot data *x* versus Monte-Carlo *x*,
but not data *x* vs data *y*. Data is grouped by :class:`.GroupBy`.
To preserve the group,
we can't yield its members to the following elements,
but have to transform the plots inside :class:`.GroupPlots`.
We can also scale (normalize) all plots to one
using :class:`.GroupScale`.

Example from real analysis:

.. code-block:: python

    Sequence(
        # ... read data and produce histograms ...
        MakeFilename(dirname="background/{{run_number}}"),
        UpdateContext("output.plot.name", "{{variable.name}}",
                      raise_on_missing=True),
        lena.flow.GroupPlots(
            group_by="variable.coordinate",
            # Select either Histograms (data) or Graphs (fit),
            # but only having "variable.coordinate" in context
            select=("variable.coordinate", [Histogram, Graph]),
            # scale to data
            scale=Not("fit"),
            transform=(
                ToCSV(),
                # scaled plots will be written to separate files
                MakeFilename(
                    "{{output.filename}}_scaled",
                    overwrite=True,
                ),
                UpdateContext("output.plot.name", "{{variable.name}}",
                              raise_on_missing=True),
                write,
                # Several prints were used during this code creation
                # Print(transform=lambda val: val[1]["plot"]["name"]),
            ),
            # make both single and combined plots of coordinates
            yield_selected=True,
        ),
        # create file names for combined plots
        MakeFilename("combined_{{variable.coordinate}}"),
        # non-combined plots will still need file names
        MakeFilename("{{variable.name}}"),
        lena.output.ToCSV(),
        write,
        lena.context.Context(),
        # here our jinja template renders a group as a list of items
        lena.output.RenderLaTeX(template_path=TEMPLATE_PATH,
                                select_template=select_template),
        # we have a single template, no more groups are present
        write,
        lena.output.LaTeXToPDF(),
    )
"""

from __future__ import print_function

import copy
import numbers

import lena.core
import lena.flow


class GroupPlots(object):
    """Group several plots."""

    def __init__(self, group_by, select, transform=(), scale=None,
                 yield_selected=False):
        """Plots to be grouped are chosen by *select*,
        which acts as a boolean function.
        If *select* is not a :class:`.Selector`, it is converted
        to that class.
        Use :class:`.Selector` for more options.

        Plots are grouped by *group_by*, which returns
        different keys for different groups.
        If it is not an instance of :class:`.GroupBy`,
        it is converted to that class.
        Use :class:`.GroupBy` for more options.

        *transform* is a sequence, which processes individual plots
        before yielding.
        For example, set ``transform=(ToCSV(), write)``.
        *transform* is called after *scale*.

        *scale* is a number or a string.
        A number means the scale, to which plots must be normalized.
        A string is a name of the plot to which other plots
        must be normalized.
        If *scale* is not an instance of :class:`.GroupScale`,
        it is converted to that class.
        If a plot could not be rescaled,
        :exc:`.LenaValueError` is raised.
        For more options, use :class:`.GroupScale`.

        *yield_selected* defines whether selected items should be
        yielded during :meth:`run`.
        By default it is ``False``: if we used a variable in a combined
        plot, we don't create a separate plot of that.
        """
        if isinstance(select, lena.flow.Selector):
            self._selector = select
        else:
            self._selector = lena.flow.Selector(select)

        if isinstance(group_by, lena.flow.group_by.GroupBy):
            self._group_by = group_by
        else:
            self._group_by = lena.flow.group_by.GroupBy(group_by)

        if (scale is None
            or isinstance(scale, lena.flow.group_scale.GroupScale)):
            self._scale = scale
        else:
            self._scale = lena.flow.group_scale.GroupScale(scale)

        if isinstance(transform, lena.core.LenaSequence):
            self._transform = transform
        else:
            self._transform = lena.core.Sequence(transform)

        self._yield_selected = yield_selected

    def run(self, flow):
        """Run the *flow* and yield final groups.

        Each item of the *flow* is checked with the selector.
        If it is selected, it is added to groups.
        Otherwise, it is yielded.

        After the *flow* is finished, groups are yielded.
        Groups are lists of items,
        which have same keys returned from *group_by*.
        Each group's context (including empty one) is inserted
        into a list in *context.group*.
        If any element's *context.output.changed* is ``True``,
        the final *context.output.changed* is set to ``True``
        (and to ``False`` otherwise).
        The resulting context is updated with the intersection
        of groups' contexts.

        If *scale* was set, plots are normalized
        to the given value or plot.
        If that plot was not selected (is missing in the captured group)
        or its norm could not be calculated,
        :exc:`.LenaValueError` is raised.
        """
        for val in flow:
            # I can't understand why, but without deep copy
            # histogram.bins (not context!) will be same
            # if several histograms update group_by
            val = copy.deepcopy(val)
            if self._selector(val):
                if self._yield_selected:
                    yield copy.deepcopy(val)
                self._group_by.update(val)
            else:
                yield val
        # flow finished

        def update_group_with_context(grp):
            # get common context
            contexts = [lena.flow.get_context(val) for val in grp]
            changed = any((lena.context.get_recursively(c, "output.changed", False)
                           for c in contexts))
            context = lena.context.intersection(*contexts)
            lena.context.update_recursively(context, "output.changed", changed)
            # add "group" to context
            context.update({"group": contexts})
            # data list contains only data part
            # todo: maybe optimize to get_data_context
            grp = [lena.flow.get_data(val) for val in grp]
            return (grp, context)

        # yield groups of selected plots
        groups = self._group_by.groups
        for group_name in groups:
            grp = groups[group_name]
            if self._scale is not None:
                grp = self._scale.scale(grp)
            # transform group items
            grp = lena.flow.functions.seq_map(self._transform, grp)
            yield update_group_with_context(grp)
