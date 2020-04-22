"""Group several plots into one.

Since data can be produced in different places,
several classes are needed to support this.
First, the plots of interest must be selected
(for example, one-dimensional histograms).
This is done by :class:`Selector`.
Selected plots must be grouped.
For example, we may want to plot data *x* versus Monte-Carlo *x*,
but not data *x* vs data *y*. Data is grouped by :class:`GroupBy`.
To preserve the group, we can't yield it to the following elements,
but have to transform the plots inside :class:`GroupPlots`.
We can also scale (normalize) all plots to one
using :class:`GroupScale`.
"""
from __future__ import print_function

import copy
import numbers

import lena.core
import lena.flow


class GroupPlots(object):
    """Group several plots."""

    def __init__(self, group_by, select, transform=(), scale_to=None,
                 yield_selected=False):
        """Plots to be grouped are chosen by *select*,
        which acts as a boolean function.
        If *select* is not a :class:`Selector`, it is converted
        to that class.
        See :class:`Selector` for more options.

        Plots are grouped by *group_by*, which returns
        different keys for different groups.
        If it is not an instance of :class:`GroupBy`,
        it is converted to that class.
        See :class:`GroupBy` for more options.

        *scale_to* is a number or a string.
        A number means the scale, to which plots must be normalized.
        A string is a name of the plot to which other plots
        must be normalized.
        If *scale_to* is not an instance of :class:`GroupScale`,
        it is converted to that class.
        If a plot could not be rescaled,
        :exc:`~lena.core.LenaValueError` is raised.
        For more options, use :class:`GroupScale`.

        *transform* is a sequence, which processes individual plots
        before yielding.
        For example, ``transform=(ToCSV(), writer)``.
        *transform* is called after *scale_to*.

        *yield_selected* defines whether selected items should be
        yielded during *run* like other items.
        Use it if you want to have both single and combined plots.
        By default, selected plots are not yielded.
        """
        if isinstance(select, lena.flow.Selector):
            self._selector = select
        else:
            self._selector = lena.flow.Selector(select)

        if isinstance(group_by, lena.flow.group_by.GroupBy):
            self._group_by = group_by
        else:
            self._group_by = lena.flow.group_by.GroupBy(group_by)

        if (scale_to is None
            or isinstance(scale_to, lena.flow.group_scale.GroupScale)):
            self._scale_to = scale_to
        else:
            self._scale_to = lena.flow.group_scale.GroupScale(scale_to)

        if isinstance(transform, lena.core.LenaSequence):
            self._transform = transform
        else:
            self._transform = lena.core.Sequence(transform)

        self._yield_selected = yield_selected

    def run(self, flow):
        """Run the flow and yield final groups.

        Each item of the flow is checked with the selector.
        If it is selected, it is added to groups.
        Otherwised it is yielded.

        After the flow is finished, groups are yielded.
        Groups are lists of items,
        which have same keys from *group_by*.
        Each group's context (including empty) is inserted
        into a list in *context.group*.
        The resulting context is updated with the intersection
        of groups' contexts.
        For uniformity, if *yield_selected* is True,
        single values are also updated:
        data is put into a list of one element, and context
        is updated with *group* key. Its value is copy
        (not deep copy) of context's values, so future updates
        to subdictionaries which existed during this run
        will be effective in *context.group*.

        If *scale_to* was set, plots are normalized
        to the given value or plot.
        If that plot was not selected (is missing in the captured group)
        or its norm could not be calculated,
        :exc:`~lena.core.LenaValueError` is raised.
        """
        def update_group_with_context(grp):
            if isinstance(grp, list):
                # get common context
                contexts = [lena.flow.get_context(val) for val in grp]
                context = lena.context.intersection(*contexts)
                # add 'group' to context
                context.update({"group": contexts})
                # data list contains only data part
                grp = [lena.flow.get_data(val) for val in grp]
                return (grp, context)
            else:
                # single element
                context = lena.flow.get_context(grp)
                context.update({"group": [copy.copy(context)]})
                # context.update({"group": [copy.deepcopy(context)]})
                return (lena.flow.get_data(grp), context)

        for val in flow:
            # I can't understand why, but without deep copy
            # histogram.bins (not context!) will be same
            # if several histograms update group_by
            val = copy.deepcopy(val)
            if self._selector(val):
                if self._yield_selected:
                    yield update_group_with_context(copy.deepcopy(val))
                self._group_by.update(val)
            else:
                yield val
        # flow finished

        # yield groups of selected plots
        groups = self._group_by.groups
        for group_name in groups:
            grp = groups[group_name]
            if self._scale_to is not None:
                grp = self._scale_to.scale(grp)
            # transform group items
            grp = lena.flow.functions.seq_map(self._transform, grp)
            yield update_group_with_context(grp)
