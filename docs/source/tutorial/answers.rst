Answers to exercises
====================
Part 1
------
Ex. 1
^^^^^
*End.run* in this case is not a generator.
To make it a generator, add a *yield* statement somewhere.
Also note that since Python 3.7
all *StopIteration* are considered to be errors
according to PEP 479. Use a simple *return* instead.
This is the implementation in *lena.flow*:

.. code-block:: python

    class End(object):
        """Stop sequence here."""

        def run(self, flow):
            """Exhaust all preceding flow and stop iteration
            (yield nothing to the following flow).
            """
            for val in flow:
                pass
            return
            # otherwise it won't be a generator
            yield "unreachable"

Ex. 2
^^^^^
.. code-block:: python

    >>> def my_generator():
    ...    print("enter my generator")
    ...    yield True
    ...
    >>> results = my_generator()
    >>> list(results)
    enter my generator
    [True]

Ex. 3
^^^^^
An implementation of *Count* is given below.
An important consideration is that there may be several *Counts*
in the sequence, so give them different names to distinguish.

.. code-block:: python

    class Count(object):
        """Count items that pass through.

        After the flow is exhausted, add {*name*: count} to the *context*.
        """

        def __init__(self, name="counter"):
            """*name* is this counter's name."""
            self._name = name
            self._count = 0
            self._cur_context = {}

        def run(self, flow):
            """Yield incoming values and increase counter.

            When the incoming flow is exhausted,
            update last value's context with *(count, context)*.

            If the flow was empty, nothing is yielded
            (so *count* can't be zero).
            """
            try:
                prev_val = next(flow)
            except StopIteration:
                # otherwise it will be an error since PEP 479
                # https://stackoverflow.com/a/51701040/952234
                return
                # raise StopIteration
            count = 1
            for val in flow:
                yield prev_val
                count += 1
                prev_val = val
            val = prev_val
            data, context = lena.flow.get_data(val), lena.flow.get_context(val)
            context.update({self._name: count})
            yield (data, context)

Ex. 4
^^^^^
A simple output function could be the following:

.. code-block:: python

    def output(output_dir="output"):
        writer = lena.output.Writer(output_dir)
        s = lena.core.Sequence(
            lena.output.HistToCSV(),
            writer,
            lena.context.Context(),
            lena.output.RenderLaTeX(), # initialize properly here
            writer,
            lena.output.LaTeXToPDF(),
            lena.output.PDFToPNG(),
        )
        return s

Then place *output()* in a sequence,
and new initialized elements will be put there.

This approach is terse, but less flexible and explicit.
In practice verbosity of several output elements
was never a problem for the author.

Ex. 5
^^^^^
It is probably impossible in Python
to stop a function and resume it at the given point.
Inform the author if you know how to do that.

..
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
