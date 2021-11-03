import lena.context
import lena.core
import lena.flow

from .histogram import Histogram
from .hist_functions import hist_to_graph


class HistToGraph():
    """Transform a :class:`.Histogram` to a :class:`.Graph`."""

    def __init__(self, make_value=None, get_coordinate="left"):
        """*make_value* is a function, that creates graph's value
        from the bin's value. By default, it is simply bin value.

        *get_coordinate* defines the coordinate of the graph's point.
        By default, it is the left bin edge. Other allowed values are
        "right" and "middle".
        An incorrect value raises :exc:`.LenaValueError`
        during the initialization.
        """
        self._make_value = make_value
        # todo: functions for coordinates should be allowed
        if get_coordinate not in ["left", "right", "middle"]:
            raise lena.core.LenaValueError(
                'get_coordinate must be one of "left", "right" or "middle"; '
                '"{}" provided'.format(get_coordinate)
            )
        self._get_coordinate = get_coordinate

    def run(self, flow):
        """Iterate the *flow* and transform histograms to graphs.
        
        Not histograms and histograms with the context
        *histogram.to_graph* set to ``False``
        are yielded unchanged.
        """
        # why can't it be a Call element, which just returns
        # unchanged values for non-histograms?
        # It could be used in a FillCompute sequence then,
        # but probably might have some design flaws.
        for val in flow:
            hist, context = lena.flow.get_data_context(val)
            if (not isinstance(hist, Histogram) or
                not lena.context.get_recursively(context,
                                                 "histogram.to_graph", True)
                ):
                yield val
                continue

            graph = hist_to_graph(
                hist,
                # context kwarg should be removed.
                context={},
                make_value=self._make_value,
                get_coordinate=self._get_coordinate
            )
            yield (graph, context)
