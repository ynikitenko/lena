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

Example from a real analysis:

.. code-block:: python

    Sequence(
        # ... read data and produce histograms ...
        MakeFilename(dirname="background/{{run_number}}"),
        UpdateContext("output.plot.name", "{{variable.name}}",
                      raise_on_missing=True),
        lena.flow.GroupPlots(
            group_by="variable.coordinate",
            # Select either histograms (data) or Graphs (fit),
            # but only having "variable.coordinate" in context
            select=("variable.coordinate", [histogram, Graph]),
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
        lena.output.RenderLaTeX(template_dir=TEMPLATE_DIR,
                                select_template=select_template),
        # we have a single template, no more groups are present
        write,
        lena.output.LaTeXToPDF(),
    )
"""

import copy
import warnings

import lena.core
import lena.flow


# group common context transform should update value context
def _update_with_group(context, new_grp_context, old_inter_context):
    # can context.output.changed be any different value?
    context_changed = lena.context.get_recursively(
        context, "output.changed", None
    )
    # copied from GroupPlots
    all_changed = set(
        (lena.context.get_recursively(c, "output.changed", None)
             for c in new_grp_context)
    )
    all_changed.add(context_changed)
    if any(all_changed):
        changed = True
    elif False in all_changed:
        # at least one is not changed
        # (this is known, not None)
        changed = False
    else:
        changed = None
    # output.changed is unlikely in the intersection,
    # but it will work if so.
    if changed is not None:
        lena.context.update_recursively(
            context, "output.changed", changed
        )

    new_inter_context = lena.context.intersection(*new_grp_context)
    context_update = lena.context.difference(new_inter_context,
                                             old_inter_context)
    # hopefully there is no "group" in these context intersection.
    lena.context.update_recursively(context,
                                    copy.deepcopy(context_update))
    context["group"] = new_grp_context


class MapGroup(object):
    """Apply a sequence to groups."""

    def __init__(self, *seq, **map_scalars):
        """Arguments *seq* must form a *Sequence*.
        
        Set a keyword argument *map_scalars* to ``False``
        to ignore scalar values (those that are not groups).
        Other keyword arguments raise :exc:`.LenaTypeError`.

        .. versionadded:: 0.5
        """
        # todo: could be made a FillCompute element, depending on *seq*
        try:
            seq = lena.core.Sequence(*seq)
        except lena.core.LenaTypeError as err:
            raise err

        self._seq = seq
        # in Python 2 we can't put a kwarg after args
        ms = map_scalars.pop("map_scalars", True)
        if map_scalars:
            raise lena.core.LenaTypeError(
                "unknown keyword arguments {}".format(map_scalars)
            )
        self._map_scalars = bool(ms)

    def run(self, flow):
        """Map *seq* to every group from *flow*.

        A value represents a group if its context has
        a key *group* and its data part is iterable
        (for example, a list of values).
        If length of data is different from the length of
        *context.group*, :exc:`LenaRuntimeError` is raised.

        *seq* must produce an equal number of results
        for each item of group, or :exc:`LenaRuntimeError` is raised.
        These results are yielded in groups one by one.

        Common changes of group context update common context
        (that of the value).
        *context.output.changed* is set appropriately.
        """
        get_data = lena.flow.get_data
        get_context = lena.flow.get_context

        for val in flow:
            data, context = lena.flow.get_data_context(val)
            # single value
            # can't see "isiterable" or similar in inspect
            if "group" not in context or not hasattr(data, "__iter__"):
                if not self._map_scalars:
                    yield val
                else:
                    # process scalars
                    for res in self._seq.run([val]):
                        yield res
                continue

            if len(data) != len(context["group"]):
                raise lena.core.LenaRuntimeError(
                    "data size must be same as that of context.group"
                )

            # a real group.
            old_inter_context = lena.context.intersection(*context["group"])

            # apply seq to each value from group
            new_vals = []
            for i, dt in enumerate(data):
                res_i = list(self._seq.run([(dt, context["group"][i])]))
                new_vals.append(res_i)

            # check that new values have same length
            n_new_vals = len(new_vals[0])
            for new_val in new_vals[1:]:
                if len(new_val) != n_new_vals:
                    raise lena.core.LenaRuntimeError(
                        "resulting groups must be of the same length, "
                        "not {}".format(new_vals)
                    )

            # new_vals[j] is the result for j-th value in group.
            # Join them in a different order.
            results = []
            for i in range(n_new_vals):
                new_data = [get_data(val[i]) for val in new_vals]
                new_group_context = [get_context(val[i]) for val in new_vals]
                results.append((new_data, new_group_context))

            for new_val in results[:-1]:
                newc = copy.deepcopy(context)
                _update_with_group(newc, new_val[1], old_inter_context)
                yield (new_val[0], newc)

            if not results:
                warnings.warn(
                    "empty results produced in MapGroup({}) for {}"\
                     .format(self._seq, context),
                    RuntimeWarning, stacklevel=2
                )
                continue

            # save one deep copy if there is only one resulting value
            _update_with_group(context, results[-1][1], old_inter_context)
            yield (results[-1][0], context)


def group_plots(group):
    """Return data parts of the *group* and set context["group"]
    to their intersection.

    If any of values has been changed,
    *context.output.changed* of the group is set to ``True``.
    """
    # todo: in this function only output.changed refers to plots.
    # Could be made more general, if needed.
    contexts = [lena.flow.get_context(val) for val in group]
    # if we wrongly assumed that a plot was unchanged,
    # that will still be overwritten by Write
    changed = any((lena.context.get_recursively(c, "output.changed", False)
                   for c in contexts))
    context = lena.context.intersection(*contexts)
    lena.context.update_recursively(context, "output.changed", changed)
    context.update({"group": contexts})
    # data list contains only data part
    # todo: maybe optimize to get_data_context
    group = [lena.flow.get_data(val) for val in group]
    return (group, context)


class GroupPlots(object):
    """Group several plots."""

    def __init__(self, group_by, select=None, transform=(), scale=None,
                 yield_selected=False):
        """Plots to be grouped are chosen by *select*,
        which acts as a boolean function.
        By default everything is selected.
        If *select* is not a :class:`.Selector`, it is converted
        to that class.
        Use :class:`.Selector` for more options.

        .. deprecated:: 0.5
           use :class:`RunIf` instead of *select*.

        Plots are grouped by *group_by*, which returns
        different keys for different groups.
        It can be a function of a value or a formatting string
        for its context (see :class:`.GroupBy`).
        Example: *group_by="{{value.variable.name}}_{{variable.name}}"*.

        *transform* is a sequence that processes individual plots
        before yielding. Example: ``transform=(ToCSV(), write)``.
        *transform* is called after *scale*.

        .. deprecated:: 0.5
           use :class:`MapGroup` instead of *transform*.

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
        # deprecated
        # we don't have an object "all", so we use None for all.
        # This doesn't interfere with Selector semantics,
        # because None is not a type.
        if select is None:
            self._selector = lambda _: True
        elif isinstance(select, lena.flow.Selector):
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

        # deprecated
        if isinstance(transform, lena.core.LenaSequence):
            self._transform = transform
        else:
            self._transform = lena.core.Sequence(*transform)

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
            if self._selector(val):
                if self._yield_selected:
                    yield copy.deepcopy(val)
                self._group_by.update(val)
            else:
                yield val

        # yield groups of selected plots
        groups = self._group_by.groups
        for group_name in groups:
            grp = groups[group_name]
            if self._scale is not None:
                self._scale(grp)
            # transform group items
            grp = lena.flow.functions.seq_map(self._transform, grp)
            # we must apply update after transform,
            # because otherwise output.changed logic may fail.
            yield group_plots(grp)
