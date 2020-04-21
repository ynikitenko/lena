"""Graph is a function at given points."""
from __future__ import print_function

import copy

import lena.core
import lena.context
import lena.flow


def _rescale_value(rescale, value):
    return rescale * lena.flow.get_data(value)


class Graph(object):
    """Function at given coordinates (arbitraty dimensions).

    Graph points can be set during the initialization and
    during :meth:`fill`. It can be rescaled (producing a new :class:`Graph`).
    A point is a tuple of *(coordinate, value)*, where both *coordinate*
    and *value* can be tuples of numbers. *Coordinate* corresponds
    to a point in N-dimensional space, while *value* is some function's
    value at this point (the function can take a value in M-dimensional
    space). Coordinate and value dimensions
    must be the same for all points.

    One can get graph points as :attr:`Graph.points` attribute.
    They will be sorted each time before return
    if *sort* was set to True.
    An attempt to change points
    (use :attr:`Graph.points` on the left of '=')
    will raise Python's :exc:`AttributeError`.
    """

    def __init__(self, points=None, scale=None, sort=True, cur_context=None):
        """*points* is an array of *(coordinate, value)* tuples.

        *scale* sets the scale of the graph.
        It is used during plotting if rescaling is needed.

        Graph coordinates are sorted by default.
        This is usually needed to plot graphs of functions.
        If you need to keep the order of insertion, set *sort* to False.

        By default, sorting is done using standard Python
        lists and functions. You can disable *sort* and provide your own
        sorting container for *points*.
        Some implementations are compared
        `here <http://www.grantjenks.com/docs/sortedcontainers/performance.html>`_.
        Note that a rescaled graph uses a default list.

        *cur_context* is the same as the most recent context
        during *fill*. Use it to provide a context
        when initializing a :class:`Graph` from existing points.

        Note that :class:`Graph` does not reduce data.
        All filled values will be stored in it.
        To reduce data, use histograms.
        """
        self._points = points if points is not None else []
        # todo: add some sanity checks for points
        self._scale = scale
        self._init_context = {"scale": scale}
        if cur_context is None:
            self._cur_context = {}
        elif not isinstance(cur_context, dict):
            raise lena.core.LenaTypeError(
                "cur_context must be a dict, {} provided".format(cur_context)
            )
        else:
            self._cur_context = cur_context
        self._sort = sort

        # todo: probably, scale from context is not needed.

        ## probably this function is not needed.
        ## it can't be copied, graphs won't be possible to compare.
        # *rescale_value* is a function, which can be used to scale
        # complex graph values.
        # It must accept a rescale parameter and the value at a data point.
        # By default, it is multiplication of rescale and the value
        # (which must be a number).
        # if rescale_value is None:
        #     self._rescale_value = _rescale_value
        self._rescale_value = _rescale_value
        self._update()

    def fill(self, value):
        """Fill the graph with *value*.

        *Value* can be a *(data, context)* tuple.
        *Data* part must be a *(coordinates, value)* pair,
        where both coordinates and value are also tuples.
        For example, *value* can contain the principal number
        and its precision.
        """
        point, self._cur_context = lena.flow.get_data_context(value)
        # coords, val = point
        self._points.append(point)

    def request(self):
        """Yield graph with context.

        If *sort* was initialized ``True``, graph points will be sorted.
        """
        # If flow contained *scale* it the context, it is set now.
        self._update()
        yield (self, self._context)

    # compute method shouldn't be in this class,
    # because it is a pure FillRequest.
    # def compute(self):
    #     """Yield graph with context (as in :meth:`request`),
    #     and :meth:`reset`."""
    #     self._update()
    #     yield (self, self._context)
    #     self.reset()

    @property
    def points(self):
        """Get graph points (read only)."""
        # sort points before giving them
        self._update()
        return self._points

    def reset(self):
        """Reset points to an empty list
        and current context to an empty dict.
        """
        self._points = []
        self._cur_context = {}

    def __repr__(self):
        self._update()
        return ("Graph(points={}, scale={}, sort={})"
                .format(self._points, self._scale, self._sort))

    def scale(self, other=None):
        """Get or set the scale.

        Graph's scale comes from an external source.
        For example, if the graph was computed from a function,
        this may be its integral passed via context during :meth:`fill`.
        Once the scale is set, it is stored in the graph.
        If one attempts to use scale which was not set,
        :exc:`~lena.core.LenaAttributeError` is raised.

        If *other* is None, return the scale.

        If a ``float`` *other* is provided, rescale to *other*.
        A new graph with the scale equal to *other*
        is returned, the original one remains unchanged.
        Note that in this case its *points* will be a simple list
        and new graph *sort* parameter will be True.

        Graphs with scale equal to zero can't be rescaled. 
        Attempts to do that raise :exc:`~lena.core.LenaValueError`.
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

            # new_init_context = copy.deepcopy(self._init_context)
            # new_init_context.update({"scale": other})

            rescale = float(other) / scale
            new_points = []
            for coord, val in self._points:
                # probably not needed, because tuples are immutable:
                # make a deep copy so that new values
                # are completely independent from old ones.
                new_points.append((coord, self._rescale_value(rescale, val)))
            # todo: not sort=self._sort?
            new_graph = Graph(points=new_points, scale=other,
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

        def unpack_pt(pt):
            coord = pt[0]
            value = pt[1]
            if isinstance(coord, tuple):
                unpacked = list(coord)
            else:
                unpacked = [coord]
            if isinstance(value, tuple):
                unpacked += list(value)
            else:
                unpacked.append(value)
            return unpacked

        def pt_to_str(pt, separ):
            return separ.join([str(val) for val in unpack_pt(pt)])

        if header is not None:
            # if one needs an empty header line, they may provide ""
            lines = header + "\n"
        else:
            lines = ""
        lines += "\n".join([pt_to_str(pt, separator) for pt in self.points])

        return lines

    #     *context* will be added to graph context.
    #     If it contains "scale", :meth:`scale` method will be available.
    #     Otherwise, if "scale" is contained in the context
    #     during :meth:`fill`, it will be used.
    #     In this case it is assumed that this scale
    #     is same for all values (only the last filled context is checked).
    #     Context from flow takes precedence over the initialized one.

    def _update(self):
        """Sort points if needed, update context."""
        # todo: probably remove this context_scale?
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

        self._context = copy.deepcopy(self._cur_context)
        self._context.update(self._init_context)
        # why this? Not *graph.scale*?
        self._context.update({"scale": self._scale})
        # self._context.update(lena.context.make_context(self, "_scale"))

        # todo: make this check during fill. Probably initialize self._dim
        # with kwarg dim. (dim of coordinates or values?)
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
            self._context["dim"] = self.dim

    def __eq__(self, other):
        if not isinstance(other, Graph):
            return False
        if self.points != other.points:
            return False
        if self._scale is None and other._scale is None:
            return True
        try:
            result = self.scale() == other.scale()
        except lena.core.LenaAttributeError:
            # one scale couldn't be computed
            return False
        else:
            return result
