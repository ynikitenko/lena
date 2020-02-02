Part 2
------
Ex. 1
^^^^^
.. code-block:: python

    import lena.flow


    class Sum():
        def __init__(self):
            self._sum = 0
            self._cur_context = {}

        def fill(self, val):
            val, context = (lena.flow.get_data(val),
                            lena.flow.get_context(val))
            self._sum += val
            self._cur_context = context

        def compute(self):
            yield (self._sum, self._cur_context)
            self._sum = 0
            self._cur_context = {}
