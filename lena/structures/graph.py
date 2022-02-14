"""A graph is a function at given points."""
import copy
import functools
import operator
import re

import lena.core
import lena.context
import lena.flow


class graph():
    """Numeric arrays of equal size."""

    def __init__(self, points, field_names=("x", "y"), scale=None):
        """This structure generally corresponds
        to the graph of a function
        and represents arrays of coordinates and the function values
        of arbitrary dimensions.

        *points* is a list of one-dimensional
        coordinate and value sequences (usually lists).
        There is little to no distinction between them,
        and "values" can also be called "coordinates".

        *field_names* provide the meaning of these arrays.
        For example, a 3-dimensional graph could be distinguished
        from a 2-dimensional graph with errors by its fields
        ("x", "y", "z") instead of ("x", "y", "y_err"),
        or ("x", "y", "y_err_low", "y_err_high").
        Field names are used to transform Lena graphs to graphs
        from other libraries.
        Field names don't affect drawing graphs:
        for that :class:`~Variable`-s should be used.
        *field_names* can be a string separated by whitespace
        and/or commas
        or a sequence of strings, such as ["x", "y", "y_err"].
        Field names must have as many elements as *points*,
        and each field name must be unique.
        Default field names are "x" and "y",
        provided for the most used 2-dimensional graphs.

        Error fields must go after all other coordinates.
        Names of coordinate errors are those of coordinates plus "_err",
        further error details are appended after '_'
        (see the examples above).
        Otherwise field names are arbitrary.

        *scale* of the graph is a kind of its norm. It could be
        the integral of the function or its other property.
        A scale of a normalised probability density
        function would be one.
        An initialized *scale* is required if one needs
        to renormalise the graph in :meth:`scale`
        (for example, to plot it with other graphs).

        Coordinates of a function graph would usually be arrays
        of increasing values, which is not required here.
        Neither is it checked that coordinates indeed
        contain one-dimensional numeric values.
        However, non-standard graphs
        will likely lead to errors during plotting
        and will require more programmer's work and caution,
        so use them only if you understand what you are doing.

        A graph can be iterated yielding tuples of numbers
        for each point. Graph field names can be accessed
        as its *field_names* attribute.
        """
        if not points:
            raise lena.core.LenaValueError(
                "points must be a non-empty sequence "
                "of coordinate sequences"
            )

        # require points to be of the same size
        pt_len = len(points[0])
        for arr in points[1:]:
            if len(arr) != pt_len:
                raise lena.core.LenaValueError(
                    "points must have subsequences of equal lengths"
                )

        # Unicode (Python 2) field names would be just bad,
        # so we don't check for it here.
        if isinstance(field_names, str):
            # split(', ') won't work.
            # From https://stackoverflow.com/a/44785447/952234:
            # \s stands for whitespace.
            field_names = re.findall(r'[^,\s]+', field_names)

        if len(field_names) != len(points):
            raise lena.core.LenaValueError(
                "field_names must have must have the same size as points"
            )

        if len(set(field_names)) != len(field_names):
            raise lena.core.LenaValueError(
                "field_names contain duplicate names"
            )

        # todo: or just fields?..
        self.field_names = field_names
        self._points = points
        self._scale = scale

        # todo: add subsequences of points as attributes
        # with field names.
        # In case if someone wants to create a graph of another function
        # at the same coordinates.
        # Should a) work when we rescale the graph
        #        b) not interfere with other fields and methods

        # Probably we won't add methods __del__(n), __add__(*coords),
        # since it might change the scale.

    def __iter__(self):
        """Iterate graph points one by one."""
        for val in zip(*self._points):
            yield val

    def scale(self, other=None):
        """Get or set the scale of the graph.

        If *other* is ``None``, return the scale of this graph.

        If a numeric *other* is provided, rescale to that value.
        If the graph has unknown or zero scale,
        rescaling that will raise :exc:`~.LenaValueError`.

        To get meaningful results, graph's fields are used.
        Only the last coordinate is rescaled.
        For example, if the graph has *x* and *y* coordinates,
        then *y* will be rescaled, and for a 3-dimensional graph
        *z* will be rescaled.
        All errors are also rescaled together with their coordinate.
        """
        # this method is called scale() for uniformity with histograms
        # And this looks really good: explicit for computations
        # (not a subtle graph.scale, like a constant field (which is,
        #  however, the case in graph - but not in other structures))
        # and easy to remember (set_scale? rescale? change_scale_to?..)

        # Abandoned: that would be redundant (not optimal)
        # to create a new graph
        # if we only want to change the scale of the existing one.
        ## A new :class:`graph` is returned, the original is unchanged.

        if other is None:
            return self._scale

        if not self._scale:
            raise lena.core.LenaValueError(
                "can't rescale a graph with zero or unknown scale"
            )

        def get_last_coord_ind_name(field_names):
            for ind, fn in enumerate(field_names):
                if fn.endswith("_err") or "_err_" in fn:
                    ind -= 1
                    break
            return (ind, field_names[ind])

        last_coord_ind, last_coord_name = \
                get_last_coord_ind_name(self.field_names)

        def get_err_indices(coord_name, field_names):
            err_indices = []
            for ind, fn in enumerate(field_names):
                if (fn == coord_name + "_err" or
                    fn.startswith(coord_name + "_err_")):
                    err_indices.append(ind)
            return err_indices

        last_coord_indices = ([last_coord_ind] +
                get_err_indices(last_coord_name, self.field_names)
        )

        # In Python 2 3/2 is 1, so we want to be safe;
        # the downside is that integer-valued graphs
        # will become floating, but that is doubtfully an issue.
        # Remove when/if dropping support for Python 2.
        rescale = float(other) / self._scale

        mul = operator.mul
        partial = functools.partial

        # a version with lambda is about 50% slower:
        # timeit.timeit('[*map(lambda val: val*2, vals)]', \
        #     setup='vals = list(range(45)); from operator import mul; \
        #     from functools import partial')
        # 3.159
        # same setup for
        # timeit.timeit('[*map(partial(mul, 2), vals)]',...):
        # 2.075
        # 
        # [*map(...)] is very slightly faster than list(map(...)),
        # but it's unavailable in Python 2 (and anyway less readable).

        # rescale arrays of values and errors
        for ind, arr in enumerate(self._points):
            if ind in last_coord_indices:
                # Python lists are faster than arrays,
                # https://stackoverflow.com/a/62399645/952234
                # (because each time taking a value from an array
                #  creates a Python object)
                self._points[ind] = list(map(partial(mul, rescale),
                                          arr))

        self._scale = other

        # as suggested in PEP 8
        return None


def _rescale_value(rescale, value):
    return rescale * lena.flow.get_data(value)


class Graph(object):
    """Function at given coordinates (arbitraty dimensions).

    Graph points can be set during the initialization and
    during :meth:`fill`. It can be rescaled (producing a new :class:`Graph`).
    A point is a tuple of *(coordinate, value)*, where both *coordinate*
    and *value* can be tuples of numbers.
    *Coordinate* corresponds to a point in N-dimensional space,
    while *value* is some function's value at this point
    (the function can take a value in M-dimensional space).
    Coordinate and value dimensions must be the same for all points.

    One can get graph points as :attr:`Graph.points` attribute.
    They will be sorted each time before return
    if *sort* was set to ``True``.
    An attempt to change points
    (use :attr:`Graph.points` on the left of '=')
    will raise Python's :exc:`AttributeError`.
    """

    def __init__(self, points=None, context=None, scale=None, sort=True):
        """*points* is an array of *(coordinate, value)* tuples.

        *context* is the same as the most recent context
        during *fill*. Use it to provide a context
        when initializing a :class:`Graph` from existing points.

        *scale* sets the scale of the graph.
        It is used during plotting if rescaling is needed.

        Graph coordinates are sorted by default.
        This is usually needed to plot graphs of functions.
        If you need to keep the order of insertion, set *sort* to ``False``.

        By default, sorting is done using standard Python
        lists and functions. You can disable *sort* and provide your own
        sorting container for *points*.
        Some implementations are compared
        `here <http://www.grantjenks.com/docs/sortedcontainers/performance.html>`_.
        Note that a rescaled graph uses a default list.

        Note that :class:`Graph` does not reduce data.
        All filled values will be stored in it.
        To reduce data, use histograms.
        """
        self._points = points if points is not None else []
        # todo: add some sanity checks for points
        self._scale = scale
        self._init_context = {"scale": scale}
        if context is None:
            self._cur_context = {}
        elif not isinstance(context, dict):
            raise lena.core.LenaTypeError(
                "context must be a dict, {} provided".format(context)
            )
        else:
            self._cur_context = context
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
        :exc:`.LenaAttributeError` is raised.

        If *other* is None, return the scale.

        If a ``float`` *other* is provided, rescale to *other*.
        A new graph with the scale equal to *other*
        is returned, the original one remains unchanged.
        Note that in this case its *points* will be a simple list
        and new graph *sort* parameter will be ``True``.

        Graphs with scale equal to zero can't be rescaled. 
        Attempts to do that raise :exc:`.LenaValueError`.
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
            # todo: should it inherit context?
            # Probably yes, but watch out scale.
            new_graph = Graph(points=new_points, scale=other,
                              sort=self._sort)
            return new_graph

    def to_csv(self, separator=",", header=None):
        """Convert graph's points to CSV.

        *separator* delimits values, the default is comma.

        *header*, if not ``None``, is the first string of the output
        (new line is added automatically).

        Since a graph can be multidimensional,
        for each point first its coordinate is converted to string
        (separated by *separator*), then each part of its value.

        To convert :class:`Graph` to CSV inside a Lena sequence,
        use :class:`lena.output.ToCSV`.
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
