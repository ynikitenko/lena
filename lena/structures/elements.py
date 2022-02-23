import copy

import lena.context
import lena.core
import lena.flow
import lena.variables

from .histogram import histogram
from .hist_functions import hist_to_graph


class HistToGraph():
    """Transform a :class:`.histogram` to a :class:`.graph`."""

    def __init__(self, make_value, get_coordinate="left",
                 field_names=("x", "y"), scale=None):
        """*make_value* is a :class:`.Variable`
        that creates graph value from the bin value.

        *get_coordinate* defines the coordinate of the graph point.
        By default, it is the left bin edge. Other allowed values are
        "right" and "middle".

        *field_names* set field names of resulting graphs.

        *scale* sets scales of resulting graphs. If it is ``True``,
        the scale is computed from the histogram.

        See :func:`hist_to_graph` for details and examples.

        Incorrect values for *make_value* or *get_coordinate* raise,
        respectively, :exc:`.LenaTypeError` or :exc:`.LenaValueError`.
        """
        if isinstance(make_value, lena.variables.Variable):
            self._make_value = make_value
        else:
            raise lena.core.LenaTypeError(
                "make_value must be a Variable, "
                "{} given".format(make_value)
            )
        # todo? functions for coordinates should be allowed
        # -- see comment in hist_to_graph
        # todo: do we need a run method, or should it be just __call__?
        # -- see comment in the method! It should.
        # todo: allow passing a scale(histogram, context?) function
        #       to create initial scales of graphs
        if get_coordinate not in ["left", "right", "middle"]:
            raise lena.core.LenaValueError(
                'get_coordinate must be one of "left", "right" or "middle"; '
                '"{}" provided'.format(get_coordinate)
            )
        self._get_coordinate = get_coordinate
        self._field_names = field_names
        self._scale = scale

    def run(self, flow):
        """Iterate the *flow* and transform histograms to graphs.

        *context.value* is updated with *make_value* context.
        If histogram bins contained context
        (which is assumed to be the same for all bins),
        *make_value* context is composed with that.

        Not histograms or histograms with
        *context.histogram.to_graph* set to ``False``
        pass unchanged.
        """
        from lena.flow import get_data_context
        from lena.flow import get_context
        # don't know differences between these two ways of imports
        get_example_bin = lena.structures.get_example_bin
        update_nested = lena.context.update_nested
        # why can't it be a Call element, which just returns
        # unchanged values for non-histograms?
        # It could be used in a FillCompute sequence then,
        # but probably might have some design flaws.
        # -- in fact, Run elements can be used as FillInto.
        #
        # Yes: FillCompute element would expect a uniform flow.
        # Odd values (not histograms) should be filtered
        # in the beginning, and not get to this element at all.
        # A separate fill_into (or better __call__) method would be fine.
        for val in flow:
            hist, context = get_data_context(val)
            if (not isinstance(hist, histogram) or
                not lena.context.get_recursively(context,
                                                 "histogram.to_graph", True)
                ):
                yield val
                continue

            bin_context = get_context(get_example_bin(hist))
            # bin context is ignored in hist_to_graph,
            # so we can safely skip its copying
            self._make_value._update_context(
                bin_context, copy.deepcopy(self._make_value.var_context)
            )
            lena.context.update_nested("value", context, bin_context)

            graph = hist_to_graph(
                hist,
                make_value=self._make_value.getter,
                field_names=self._field_names,
                get_coordinate=self._get_coordinate,
                scale=self._scale
            )
            yield (graph, context)
