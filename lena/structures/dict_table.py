from copy import deepcopy

from lena.core import LenaKeyError, LenaValueError

from lena.context import (
    contains, get_recursively, intersection, update_recursively
)
from lena.flow import get_data_context


class dict_table():
    """A list of dictionaries with easy selection."""

    def __init__(self, rows):
        """The table content is a list of *rows*,
        where each row is a dictionary.
        A row typically contains context metadata
        with values of interest.

        Example:
        
        >>> d1 = {"detector": "FD",  "mean": 3, "mean_err": 2}
        >>> d2 = {"detector": "ND",  "mean": 2.5, "mean_err": 3}
        >>> 
        >>> dt = dict_table([d1, d2])
        >>> # filtering rows returns a dictionary
        >>> dt["detector.FD"]  # d1
        {'detector': 'FD', 'mean': 3, 'mean_err': 2}
        >>> dt["detector.FD"]["mean"]
        3

        One can iterate a *dict_table* yielding contained rows,
        get its length and perform its boolean testing.
        Table length is the number of rows it contains.
        Tables with equal rows in the same order
        are considered equal.
        Sort rows in advance if needed for equality testing.
        """
        self._table = list(rows)

    def filter_columns(self, key):
        """Get the value of the *key* from the table.

        *key* is a string. If it contains a dot
        it corresponds to a nested dictionary .

        .. note::
            *key* is the same as an *item*
            in :meth:`filter_rows` with a semantic distinction:
            an *item* is typically a fixed expression for filtering
            ("detector", "ND"), while a *key* is for getting
            calculated values ("variable", float); we omit
            the unknown last part of the *key* during the retrieval.

        If the table contains one element,
        return the value corresponding to the *key*.
        If there are several elements with *key*,
        return a list of those values.
        If no rows have been found, raise :exc:`.LenaKeyError`.

        Example:

        >>> dt["mean"]  # doctest: +SKIP
        [3, 2.5]

        Returned list informs us that we forgot to make
        a proper row selection before getting the value.
        We have to update our selections when extending the results
        with new values (adding new filters, data sources, etc.).
        """
        values = []

        # getting several columns looks overhead for our task,
        # but it was already implemented and looks natural for a table.
        def get_tuple_recursively(d, keys):
            vals = []
            for key in keys:
                vals.append(get_recursively(d, key))
            return tuple(vals)

        if isinstance(key, tuple):
            getr = get_tuple_recursively
        else:
            getr = get_recursively

        for d in self._table:
            try:
                val = getr(d, key)
            except LenaKeyError as err:
                pass
                # if some rows don't have the key, ignore.
                # raise err
            else:
                values.append(val)

        if len(values) == 0:
            # Our priority is getting one single value,
            # therefore we raise in case of missing.
            # No ignore, no default.
            raise LenaKeyError(
                "The key {} could be found in the table.".format(key)
            )
        elif len(values) == 1:
            return values[0]
        else:
            # we can not create a dict_table here,
            # since the values are detached from their keys (names).
            # We return a list, since that was produced in our algorithm
            return values

    def filter_rows(self, item):
        """Get a subtable (slice) of rows containing *item*.

        *item* is a string corresponding to an item
        of a Python dict (a (key, value) pair) joined by a dot.
        Dictionary items can be nested.
        Example: ``filter_rows("data.detector.FD")``.

        Return a new non-empty dict_table.
        If it contains only one element, return that element instead.
        If no elements have been found, :exc:`.LenaKeyError` is raised.
        """
        # if not isinstance(item, str):
        #     # todo: allow contains to work with tuples.
        #     item = ".".join(item)
        slice_ = []
        for d in self._table:
            if contains(d, item):
                slice_.append(d)

        if not slice_:
            # much better than silently returning an empty table
            raise LenaKeyError(
                "{} not found in dict_table".
                format(item)
            )
        elif len(slice_) == 1:
            # a single dictionary has more methods than dict_table.
            # a single value or a subtable are also explicitly different
            return slice_[0]
        else:
            return dict_table(slice_)

    def __getitem__(self, key):
        """Get a selection of rows or columns of the table.

        If the *key* corresponds to an item ("detector.FD"),
        return a selection with :meth:`filter_rows`.
        If the *key* has a value ("mean"),
        return :meth:`filter_columns` with *key*.
        In case of errors, use the corresponding functions.

        Example: ``dt["detector.FD"]["mean"]`` returns 3,
        ``dt["detector"]`` returns ``["FD", "ND"]``.
        """
        # *key* can be a tuple of keys. In that case a tuple of values
        # corresponding to each key is returned
        # for each element of the table.

        if isinstance(key, tuple):
            return self.filter_columns(key)

        # if the key has a value, return those values.
        # If the key has no corresponding value ("detector", "FD"),
        # then this branch will fail.
        try:
            values = self.filter_columns(key)
        except LenaKeyError:
            pass
        else:
            return values

        # If the key has no corresponding values,
        # it is a selection.
        # will raise LenaKeyError if not found
        return self.filter_rows(key)

    def __bool__(self):
        return bool(self._table)

    def __eq__(self, other):
        # order matters. We can't use a set,
        # since dicts are not hashable
        # and it's very hard to make them such.
        # Moreover, tables in different order
        # would return results in different order.
        if isinstance(other, dict_table):
            return self._table == other._table
        return NotImplemented

    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        # we don't implement other sequence functions
        # like concatenation or __contains__, since
        # we don't want to mutate or directly search our table.
        return len(self._table)

    def __repr__(self):
        return "dict_table({})".format(self._table)


class DictTable():
    """Element to create :class:`.dict_table`-s.

    Example:

    .. code-block:: python

        s = Source(
            # read data
            Sum(),
            # put data part into a dictionary
            # thus naming incoming values
            Data(lambda val: {"sum": val}),
            DictTable(),
            # use a custom function to render LaTeX
            # from data part of values
            # my_render_latex("mytable.tex"),
            # write rendered tables
        )
    """

    def __init__(self):
        self._rows = []
        self._contexts = []
        # self._data_name = data_name

    def fill(self, value):
        """Update data part of *value* with its context part and add
        to the table.
        """
        data, context = get_data_context(value)
        if not isinstance(data, dict):
            raise LenaValueError(
                "input values must be dictionaries, {} provided.".format(data)
            )
            # values should be explicitly nested into dictionaries
            # right in sequences, for better readability
            # data = {self._data_name: data}
        update_recursively(data, context)
        self._rows.append(data)
        self._contexts.append(context)

    def compute(self):
        """Yield :class:`.dict_table` with context from filled values.

        Resulting context is the intersection of all contexts.
        Each row in the table retains its own context.
        """
        # subcontexts of intersecion are deeply copied
        context = intersection(*self._contexts)
        yield (dict_table(self._rows), context)
        # make a deep copy if going to reuse this table
        # yield (dict_table(deepcopy(self._rows)), context)

    def reset(self):
        self._rows = []
        self._contexts = []

    def __eq__(self, other):
        if isinstance(other, DictTable):
            # the order matters
            return self._rows == other._rows
        return NotImplemented

    def __repr__(self):
        if not self._rows:
            return "DictTable()"
        # we won't be able to initialise a DictTable
        # with an argument, but it is good for introspection.
        return "DictTable({})".format(self._rows)
