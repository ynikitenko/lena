"""Graph is a function at given points."""
from __future__ import print_function

import copy

import lena.core
import lena.context
import lena.flow


def _rescale_value(rescale, value):
    return rescale * lena.flow.get_data(value)


class Graph(lena.core.FillCompute):
    """Function at given points.

    Warning
    -------
        Under construction. Scale, initialization and docs will be rethought.

    Graph can be set during the initialization and
    during :meth:`fill`. It can be rescaled (producing a new graph).

    One can get graph points as :attr:`Graph.points` attribute.
    They will be sorted each time before return
    if *sort* was set to True.
    An attempt to change points
    (use :attr:`Graph.points` on the left of '=')
    will raise Python's :exc:`AttributeError`.

    Warning
    -------
    *Graph* does not reduce data.
    All filled values will be stored in it.
    To reduce data, use histograms.
    """

    def __init__(self, points=None, context=None, sort=True, rescale_value=None):
        """*points* is an array of *(coordinate, value)* tuples.

        *context* will be added to graph context.
        If it contains "scale", :meth:`scale` method will be available.
        Otherwise, if "scale" is contained in the context
        during :meth:`fill`, it will be used.
        In this case it is assumed that this scale
        is same for all values (only the last filled context is checked).
        Context from flow takes precedence over the initialized one.

        Graph coordinates are sorted by default.
        This is usually needed to plot graphs of functions.
        If you need to keep the order of insertion, set *sort* to False.

        *rescale_value* is a function, which can be used to scale
        complex graph values.
        It must accept a rescale parameter and the value at a data point.
        By default, it is multiplication of rescale and the value
        (which must be a number).

        By default, sorting is done using standard Python
        lists and functions. You can disable *sort* and provide your own
        sorting container for *points*.
        Some implementations are compared
        `here <http://www.grantjenks.com/docs/sortedcontainers/performance.html>`_.
        Note that a rescaled graph uses a default list.
        """
        self._points = points if points is not None else []
        context = context if context is not None else {}
        self._scale = context.get("scale") # or None
        self._context = context
        self._cur_context = {}
        self._sort = sort

        if rescale_value is None:
            self._rescale_value = _rescale_value
        self._update()
        # run method is inherited automatically from FillCompute
        super(Graph, self).__init__(self)

    def fill(self, value):
        """Fill the graph with *value*.

        *Value* can be a *(data, context)* tuple.
        *Data* part must be a *(coordinates, value)* pair,
        where both coordinates and value are also tuples.
        For example, *value* can contain the principal number
        and the precision.
        """
        point = lena.flow.get_data(value)
        self._cur_context = lena.flow.get_context(value)
        # coords, val = point
        self._points.append(point)

    def request(self):
        """Yield graph with context.

        If *sort* was initialized True, graph points will be sorted.
        If flow contained *scale* it the context, it is set now.
        """
        self._update()
        yield (self, self._context)

    def compute(self):
        """Yield graph with context (as in :meth:`request`),
        and :meth:`reset`."""
        self._update()
        yield (self, self._context)
        self.reset()

    @property
    def points(self):
        """Get graph points (read only)."""
        # sort points before giving them
        self._update()
        return self._points

    def reset(self):
        """Reset points to empty list and context to empty dict."""
        self._points = []
        self._context = {}

    def __repr__(self):
        self._update()
        return ("Graph(points={}, context={}, sort={})"
                .format(self._points, self._context, self._sort))

    def scale(self, other=None):
        """Get or set the scale.

        Graph's scale comes from an external source.
        For example, if the graph was computed from a function,
        this may be its integral passed via context during :meth:`fill`.
        Once the scale is set, it is stored in the graph.
        If one attempts to use scale which was not set,
        :exc:`LenaAttributeError` is raised.

        If *other* is None, return the scale.

        If a ``float`` *other* is provided, rescale to *other*.
        A new graph with the scale equal to *other*
        is returned, the original one remains unchanged.
        Note that in this case its *points* will be a simple list
        and new graph *sort* parameter will be True.

        Graphs with scale equal to zero can't be rescaled.
        :exc:`LenaValueError` is raised if one tries to do that.
        """
        if other is None:
            # return scale
            self._update()
            if self._scale is None:
                raise lena.core.LenaAttributeError(
                    "scale must be explicitly set before using that"
                )
            return self._scale
        else:
            # rescale from other
            scale = self.scale()
            if scale == 0:
                raise lena.core.LenaValueError(
                    "can't rescale graph with 0 scale"
                )
            new_context = copy.deepcopy(self._context)
            new_context.update({"scale": other})
            rescale = float(other) / scale
            new_points = []
            for coord, val in self._points:
                # make a deep copy so that new values
                # are completely independent from old ones.
                new_points.append((coord, self._rescale_value(rescale, val)))
            new_graph = Graph(points=new_points, context=new_context,
                              sort=True)
            return new_graph

    def to_csv(self, separator=",", header=None):
        """Convert graph's points to CSV.

        *separator* delimits values, default is a comma.

        *header*, if not ``None``, is the first string of the output
        (new line is added automatically).

        Since a graph can be multidimensional,
        for each point first its coordinate is converted to string
        (separated by *separator*), than each part of its value.

        To convert :class:`Graph` to CSV inside a Lena sequence,
        use :class:`~lena.output.ToCSV`.
        """
        if self._sort:
            self._update()

        # no explicit separator provided
        if separator is None:
            separator = ","
        def pt_to_str(pt, separ):
            return separ.join([str(coord) for coord in pt[0]] +
                              [str(val) for val in pt[1]])

        if header is not None:
            # if one needs an empty header line, they may provide ""
            lines = header + "\n"
        else:
            lines = ""
        lines += "\n".join([pt_to_str(pt, separator) for pt in self.points])
        return (lines, self._context)

    def _update(self):
        """Sort points if needed, update context."""
        context_scale = self._cur_context.get("scale")
        if context_scale is not None:
            # this complex check is fine with rescale,
            # because that returns a new graph (this scale unchanged).
            if self._scale is not None and self._scale != context_scale:
                raise lena.core.LenaRuntimeError(
                    "Initialization and context scale differ, "
                    "{} and {} from context {}"
                    .format(self._scale, context_scale, self._cur_context)
                )
            self._scale = context_scale
        if self._sort:
            self._points = sorted(self._points)
        context = self._context
        context.update(self._cur_context)
        context.update(lena.context.make_context(self, "dim", "_scale"))
        if self._points:
            # check points correctness
            points = self._points
            def coord_dim(coord):
                if not hasattr(coord, "__len__"):
                    return 1
                return len(coord)
            first_coord = points[0][0]
            dim = coord_dim(first_coord)
            same_dim = all(coord_dim(point[0]) == dim for point in points)
            if not same_dim:
                raise lena.core.LenaValueError(
                    "coordinates tuples must have same dimension, "
                    "{} given".format(points)
                )
            self.dim = dim
            context["dim"] = self.dim

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return False
        if self.points != other.points:
            return False
        if self._scale is None and other._scale is None:
            return True
        try:
            result = self.scale() == other.scale()
        except lena.core.LenaException:
            # one scale couldn't be computed
            return False
        else:
            return result
