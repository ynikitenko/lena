import array

import lena.context
import lena.flow


def _list_to_array(coords, type_code):
    return array.array(type_code, (coord for coord in coords))


class root_graph_errors():
    """2-dimensional ROOT graph with errors.

    This is an adapter for
    `TGraphErrors <https://root.cern.ch/doc/master/classTGraphErrors.html>`_
    and contains that graph as a field *root_graph*.
    """

    def __init__(self, graph, type_code='d'):
        """*graph* is a Lena :class:`.graph`.

        *type_code* is the basic numeric type of array values
        (by default double). 'f' means floating values.
        See Python module
        `array <https://docs.python.org/3/library/array.html>`_
        for more options.

        .. versionadded:: 0.5
        """

        import ROOT

        if graph.dim != 2:
            raise lena.core.LenaValueError(
                "graph dimension must be 2"
            )

        errors = graph._parsed_error_names
        # this is not possible, because we forbid suffixes
        # if len(errors) > 2:
        #     raise lena.core.LenaValueError(
        #         "graph contains too many error fields (maximum is 2)"
        #     )

        x_coord = graph.field_names[0]
        y_coord = graph.field_names[1]

        x_error = ROOT.nullptr
        y_error = ROOT.nullptr

        error_x_ind = 0
        error_y_ind = 0
        for err in errors:
            if err[2]:
                # errors for unknown coordinates
                # are forbidden in graph itself.
                raise lena.core.LenaValueError(
                    "error suffixes are not allowed"
                )
            error_ind = err[3]
            if err[1] == x_coord:
                x_error = graph.coords[error_ind]
                error_x_ind = error_ind
            elif err[1] == y_coord:
                y_error = graph.coords[error_ind]
                error_y_ind = error_ind

        self._error_x_ind = error_x_ind
        self._error_y_ind = error_y_ind

        n_points = len(graph.coords[0])

        xs = _list_to_array(graph.coords[0], type_code)
        ys = _list_to_array(graph.coords[1], type_code)
        exs = ROOT.nullptr
        eys = ROOT.nullptr
        if x_error:
            exs = _list_to_array(x_error, type_code)
        if y_error:
            eys = _list_to_array(y_error, type_code)

        self.root_graph = ROOT.TGraphErrors(n_points, xs, ys, exs, eys)

    def _arrays(self):
        import ROOT
        # not a class field, because it can't be pickled
        rg = self.root_graph
        arrays = [
            # all these values are pointers,
            # so they can't be pickled.
            rg.GetX(),
            rg.GetY(),
        ]
        if self._error_x_ind:
            arrays.append(rg.GetEX())
        if self._error_y_ind:
            arrays.append(rg.GetEY())
        return arrays

    def __eq__(self, other):
        if not isinstance(other, root_graph_errors):
            return False
        # looks they can't be compared directly
        # return self.root_graph == other.root_graph
        # error indices are the same
        if (self._error_x_ind != other._error_x_ind
            or self._error_y_ind != other._error_y_ind):
            return False
        # pointwise comparison
        return list(self) == list(other)

    def __iter__(self):
        npoints = self.root_graph.GetN()
        for ind in range(npoints):
            res = tuple((arr[ind] for arr in self._arrays()))
            yield res

    def __len__(self):
        return self.root_graph.GetN()
    
    def _update_context(self, context):
        error_x_ind = self._error_x_ind
        error_y_ind = self._error_y_ind
        if error_x_ind:
            lena.context.update_recursively(
                context, "error.x.index", error_x_ind
            )
        if error_y_ind:
            lena.context.update_recursively(
                context, "error.y.index", error_y_ind
            )


class ROOTGraphErrors():
    """Element to convert graphs to :class:`.root_graph_errors`."""

    def __call__(self, value):
        """Convert data part of the value
        (which must be a :class:`.graph`)
        to :class:`.root_graph_errors`.

        .. versionadded:: 0.5
        """
        graph, context = lena.flow.get_data_context(value)
        return (root_graph_errors(graph), context)
