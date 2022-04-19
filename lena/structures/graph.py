"""A graph is a function at given coordinates."""
import copy
import functools
import operator
import re
import warnings

import lena.core
import lena.context
import lena.flow


class graph():
    """Numeric arrays of equal size."""

    def __init__(self, coords, field_names=("x", "y"), scale=None):
        """This structure generally corresponds
        to the graph of a function
        and represents arrays of coordinates and the function values
        of arbitrary dimensions.

        *coords* is a list of one-dimensional
        coordinate and value sequences (usually lists).
        There is little to no distinction between them,
        and "values" can also be called "coordinates".

        *field_names* provide the meaning of these arrays.
        For example, a 3-dimensional graph could be distinguished
        from a 2-dimensional graph with errors by its fields
        ("x", "y", "z") versus ("x", "y", "error_y").
        Field names don't affect drawing graphs:
        for that :class:`~Variable`-s should be used.
        Default field names,
        provided for the most used 2-dimensional graphs,
        are "x" and "y".

        *field_names* can be a string separated by whitespace
        and/or commas or a tuple of strings, such as ("x", "y").
        *field_names* must have as many elements
        as *coords* and each field name must be unique.
        Otherwise field names are arbitrary.
        Error fields must go after all other coordinates.
        Name of a coordinate error is "error\\_"
        appended by coordinate name. Further error details
        are appended after '_'. They could be arbitrary depending
        on the problem: "low", "high", "low_90%_cl", etc. Example:
        ("E", "time", "error_E_low", "error_time").

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
        for each point.

        **Attributes**

        :attr:`coords` is a list \
            of one-dimensional lists of coordinates.

        :attr:`field_names`

        :attr:`dim` is the dimension of the graph,
        that is of all its coordinates without errors.

        In case of incorrect initialization arguments,
        :exc:`~.LenaTypeError` or :exc:`~.LenaValueError` is raised.

        .. versionadded:: 0.5
        """
        if not coords:
            raise lena.core.LenaValueError(
                "coords must be a non-empty sequence "
                "of coordinate sequences"
            )

        # require coords to be of the same size
        pt_len = len(coords[0])
        for arr in coords[1:]:
            if len(arr) != pt_len:
                raise lena.core.LenaValueError(
                    "coords must have subsequences of equal lengths"
                )

        # Unicode (Python 2) field names would be just bad,
        # so we don't check for it here.
        if isinstance(field_names, str):
            # split(', ') won't work.
            # From https://stackoverflow.com/a/44785447/952234:
            # \s stands for whitespace.
            field_names = tuple(re.findall(r'[^,\s]+', field_names))
        elif not isinstance(field_names, tuple):
            # todo: why field_names are a tuple,
            # while coords are a list?
            # It might be non-Pythonic to require a tuple
            # (to prohibit a list), but it's important
            # for comparisons and uniformity
            raise lena.core.LenaTypeError(
                "field_names must be a string or a tuple"
            )

        if len(field_names) != len(coords):
            raise lena.core.LenaValueError(
                "field_names must have must have the same size as coords"
            )

        if len(set(field_names)) != len(field_names):
            raise lena.core.LenaValueError(
                "field_names contains duplicates"
            )

        self.coords = coords
        self._scale = scale

        # field_names are better than fields,
        # because they are unambigous (as in namedtuple).
        self.field_names = field_names

        # decided to use "error_x_low" (like in ROOT).
        # Other versions were x_error (looked better than x_err),
        # but x_err_low looked much better than x_error_low).
        try:
            parsed_error_names = self._parse_error_names(field_names)
        except lena.core.LenaValueError as err:
            raise err
            # in Python 3
            # raise err from None
        self._parsed_error_names = parsed_error_names

        dim = len(field_names) - len(parsed_error_names)
        self._coord_names = field_names[:dim]
        self.dim = dim

        # todo: add subsequences of coords as attributes
        # with field names.
        # In case if someone wants to create a graph of another function
        # at the same coordinates.
        # Should a) work when we rescale the graph
        #        b) not interfere with other fields and methods

        # Probably we won't add methods __del__(n), __add__(*coords),
        # since it might change the scale.

    def __eq__(self, other):
        """Two graphs are equal, if and only if they have
        equal coordinates, field names and scales.

        If *other* is not a :class:`.graph`, return ``False``.

        Note that floating numbers should be compared
        approximately (using :func:`math.isclose`).
        Therefore this comparison may give false negatives.
        """
        if not isinstance(other, graph):
            # in Python comparison between different types is allowed
            return False
        return (self.coords == other.coords and self._scale == other._scale
                and self.field_names == other.field_names)

    def _get_err_indices(self, coord_name):
        """Get error indices corresponding to a coordinate."""
        err_indices = []
        dim = self.dim
        for ind, err in enumerate(self._parsed_error_names):
            if err[1] == coord_name:
                err_indices.append(ind+dim)
        return err_indices

    def __iter__(self):
        """Iterate graph coords one by one."""
        for val in zip(*self.coords):
            yield val

    def __repr__(self):
        return """graph({}, field_names={}, scale={})""".format(
            self.coords, self.field_names, self._scale
        )

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
        All errors are rescaled together with their coordinate.
        """
        # this method is called scale() for uniformity with histograms
        # And this looks really good: explicit for computations
        # (not a subtle graph.scale, like a constant field (which is,
        #  however, the case in graph - but not in other structures))
        # and easy to remember (set_scale? rescale? change_scale_to?..)

        # We modify the graph in place,
        # because that would be redundant (not optimal)
        # to create a new graph
        # if we only want to change the scale of the existing one.

        if other is None:
            return self._scale

        if not self._scale:
            raise lena.core.LenaValueError(
                "can't rescale a graph with zero or unknown scale"
            )

        last_coord_ind = self.dim - 1
        last_coord_name = self.field_names[last_coord_ind]

        last_coord_indices = ([last_coord_ind] +
                self._get_err_indices(last_coord_name)
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
        for ind, arr in enumerate(self.coords):
            if ind in last_coord_indices:
                # Python lists are faster than arrays,
                # https://stackoverflow.com/a/62399645/952234
                # (because each time taking a value from an array
                #  creates a Python object)
                self.coords[ind] = list(map(partial(mul, rescale),
                                            arr))

        self._scale = other

        # as suggested in PEP 8
        return None

    def _parse_error_names(self, field_names):
        # field_names is a parameter for easier testing,
        # usually object's field_names are used.
        errors = []

        # collect all error fields and check that they are
        # strictly after other fields
        in_error_fields = False
        # there is at least one field
        last_coord_ind = 0
        for ind, field in enumerate(field_names):
            if field.startswith("error_"):
                in_error_fields = True
                errors.append((field, ind))
            else:
                last_coord_ind = ind
                if in_error_fields:
                    raise lena.core.LenaValueError(
                        "errors must go after coordinate fields"
                    )

        coords = set(field_names[:last_coord_ind+1])
        parsed_errors = []

        for err, ind in errors:
            err_coords = []
            for coord in coords:
                err_main = err[6:]  # all after "error_"
                if err_main == coord or err_main.startswith(coord + "_"):
                    err_coords.append(coord)
                    err_tail = err_main[len(coord)+1:]
            if not err_coords:
                raise lena.core.LenaValueError(
                    "no coordinate corresponding to {} given".format(err)
                )
            elif len(err_coords) > 1:
                raise lena.core.LenaValueError(
                    "ambiguous error " + err +\
                    " corresponding to several coordinates given"
                )
            # "error" may be redundant, but it is explicit.
            parsed_errors.append(("error", err_coords[0], err_tail, ind))

        return parsed_errors

    def _update_context(self, context):
        """Update *context* with the properties of this graph.

        *context.error* is appended with indices of errors.
        Example subcontext for a graph with fields "E,t,error_E_low":
        {"error": {"x_low": {"index": 2}}}.
        Note that error names are called "x", "y" and "z"
        (this corresponds to first three coordinates,
        if they are present), which allows to simplify plotting.
        Existing values are not removed
        from *context.value* and its subcontexts.

        Called on "destruction" of the graph (for example,
        in :class:`.ToCSV`). By destruction we mean conversion
        to another structure (like text) in the flow.
        The graph object is not really destroyed in this process.
        """
        # this method is private, because we encourage users to yield
        # graphs into the flow and process them with ToCSV element
        # (not manually).

        if not self._parsed_error_names:
            # no error fields present
            return

        dim = self.dim

        xyz_coord_names = self._coord_names[:3]
        for name, coord_name in zip(["x", "y", "z"], xyz_coord_names):
            for err in self._parsed_error_names:
                if err[1] == coord_name:
                    error_ind = err[3]
                    if err[2]:
                        # add error suffix
                        error_name = name + "_" + err[2]
                    else:
                        error_name = name
                    lena.context.update_recursively(
                        context,
                        "error.{}.index".format(error_name),
                        # error can correspond both to variable and
                        # value, so we put it outside value.
                        # "value.error.{}.index".format(error_name),
                        error_ind
                    )


# used in deprecated Graph
def _rescale_value(rescale, value):
    return rescale * lena.flow.get_data(value)


class Graph(object):
    """
    .. deprecated:: 0.5
       use :class:`graph`.
       This class may be used in the future,
       but with a changed interface.

    Function at given coordinates (arbitraty dimensions).

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
        warnings.warn("Graph is deprecated since Lena 0.5. Use graph.",
                      DeprecationWarning, stacklevel=2)

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
        """.. deprecated:: 0.5 in Lena 0.5 to_csv is not used.
              Iterables are converted to tables.

        Convert graph's points to CSV.

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
