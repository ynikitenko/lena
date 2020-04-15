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
            lena.output.ToCSV(),
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
The author is unaware of a simple for a user way
to stop a function and resume it at the given point.
Inform the author if you know better answers to any of these exercises.

Mikhail Zelenyi gives this
`explanation <https://habr.com/ru/post/490518/#comment_21342580>`_
(translated from Russian):

There are two types of models: push and pull.
If you have a sequence, then in the case of a *push* model
the calculations are initiated by the first member of the sequence,
which pushes data further. In this case fork could be done easily,
just at a certain moment it pushes data not into one sequence, but into two.

In the case of a *pull* model
the calculations are initiated by the last member of the sequence.
Consequently, if we want to branch the sequence, we need to think
what to do: to start only when all consumers asked,
to use a buffer, or to start with one consumer
and to push the rest of the data conforming to the *push* model.

Part 2
------
Ex. 1
^^^^^
This is the *Sum* implementation from *lena.math*:

.. code-block:: python

    class Sum(object):
        """Calculate sum of input values."""

        def __init__(self, start=0):
            """*start* is the initial value of sum."""
            # start is similar to Python's builtin *sum* start.
            self._start = start
            self.reset()

        def fill(self, value):
            """Fill *self* with *value*.

            The *value* can be a *(data, context)* pair.
            The last *context* value (considered empty if missing)
            sets the current context.
            """
            data, context = lena.flow.get_data_context(value)
            self._sum += data
            self._cur_context = context

        def compute(self):
            """Calculate the sum and yield.

            If the current context is not empty, yield *(sum, context)*.
            Otherwise yield only *sum*.
            """
            if not self._cur_context:
                yield self._sum
            else:
                yield (self._sum, copy.deepcopy(self._cur_context))

        def reset(self):
            """Reset sum and context.

            Sum is reset to the *start* value and context to {}.
            """
            self._sum = copy.deepcopy(self._start)
            self._cur_context = {}

Ex. 2
^^^^^
Delete the first *MakeFilename* and change the second one to

.. code-block:: python

   MakeFilename("{variable.particle}/{variable.name}")

Ex. 3
^^^^^
We believe that the essence of data is captured in
the function with which it was obtained.
Histogram is just its presentation.
It may be tempting to name a histogram just for convenience,
but a general *MakeFilename* would be more powerful.

Functional programming suggests that larger functions should be 
decomposed into smaller ones, while object-oriented design
praises code cohesion.
The decisions above were made by choosing between these principles.
There are cases when a histogram is data itself.
In such situations, however,
the final result is often not a histogram but a function of that,
like a mean or a mode (which again suggests a different name).

Ex. 4
^^^^^
In part 1 of the tutorial there was introduced an element *End*,
which stops the flow at its location. 
However, if there are *Histograms* in the following flow,
they will be yielded even if nothing was filled into them.
Empty histogram is a legitimate histogram state.
It may be also filled, but the result may fall out of the histogram's range.
It is possible to write a special element if needed to check
whether the flow was empty.

In the next chapter we will present a specific analysis
during which a histogram may not be filled, but it must be produced.
A *FillCompute* element is more general than a histogram
(which we use here just for a concrete example).

Note also that if a histogram was not filled,
preceding variables weren't called.
The histogram will have no context,
probably won't have a name and won't be plotted correctly.
Take an empty flow into account when creating
your own *FillCompute* elements.

Ex. 5
^^^^^
It depends on the student's priorities.
If he wants to finish the diploma never to return to programming,
or if he has a lot of work to do apart from writing code,
the fastest option might be the best.
General algorithms have a more complicated interface.
However, if one decides to rely upon a "friendly" library,
there is a risk that the programmer will have to rewrite
all code when more functionality becomes needed.

Architectural choices rise for middle-sized or large projects.
If the student's personal code becomes large and more time is spent
on supporting and extending that, it may be a good time to define
the architecture.
Here the author estimates "large" programs to start from
one thousand lines.

Another distinction is that when using a library one learns
how to use a library. When using a good framework, one learns
how to write good code. Many algorithms in programming are simple,
but to choose a good design may be much more difficult,
and to learn how to create good programs yourself may take years
of studying and experience.
When you feel difficulties with making programming decisions,
it's time to invest into design skills.
