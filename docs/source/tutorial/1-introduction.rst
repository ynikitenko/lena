Introduction to Lena
====================

In our data analysis we often face changing data or algorithms.
For example, we may want to see how our analysis works
for another dataset or for a specific subset of the data.
We may also want to use different algorithms and compare their results.

To handle this gracefully, we must be able to easily change
or extend our code at any specified point.
The idea of Lena is to split our code into small independent blocks,
which are later composed together.
The tutorial will show us how to do that
and what implications this idea will have for our code.

.. 
    .. note::
        If you find yourself overwhelmed with information, 
        you can omit sections like this during the first reading.

.. contents:: Contents
    :local:

.. .. toctree::

The three ideas behind Lena
---------------------------

1. Sequences and elements
^^^^^^^^^^^^^^^^^^^^^^^^^
The basic idea of *Lena* is to join our computations into sequences.
Sequences consist of elements.

The simplest *Lena* program may be the following.
We use a sequence with one element,
an anonymous function, which is created in Python by *lambda* keyword:

>>> from __future__ import print_function
>>> from lena.core import Sequence
>>> s = Sequence(
...     lambda i: pow(-1, i) * (2 * i + 1),
... )
>>> results = s.run([0, 1, 2, 3])
>>> for res in results:
...     print(res)
1 -3 5 -7

Lena supports both Python versions, 2 and 3.
It is simple to do it in your code, if you want.
The first line allows to use *print()* for any version of Python.
The next line imports a *Lena* class.

A *Sequence* can be initialized from several elements.
To make the *Sequence* do the actual work, we use its method *run*.
*Run*'s argument is an iterable (in this case a list of four numbers). 

To obtain all results, we iterate them in the cycle *for*.

Let us move to a more complex example.
It is often convenient not to pass any data to a function,
which gets it somewhere else itself.
In this case use a sequence *Source*:

.. code-block:: python

    from lena.core import Sequence, Source
    from lena.flow import CountFrom, Slice

    s = Sequence(
        lambda i: pow(-1, i) * (2 * i + 1),
    )
    spi = Source(
        CountFrom(0),
        s,
        Slice(10**6),
        lambda x: 4./x,
        Sum(),
    )
    results = list(spi())
    # [3.1415916535897743]

The first element in *Source* must have a *__call__* special method,
which accepts no arguments and generates values itself.
These values are propagated by the sequence:
each following element receives as input the results of the previous element,
and the sequence call gives the results of the last element.

A *CountFrom* is an element, which produces an infinite series of numbers.
*Elements* must be functions or objects, but not classes [#f1]_.
We pass the starting number to *CountFrom* during its initialization
(in this case zero).
The initialization arguments of *CountFrom* are 
*start* (by default zero) and *step* (by default one).

The following elements of a *Source* (if present)
must be callables or objects with a method called *run*.
They can form a simple *Sequence* themselves.

Sequences can be joined together.
In our example, we use our previously defined sequence *s*
as the second element of *Source*.
There would be no difference if we used the lambda from *s*
instead of *s*. 

A *Sequence* can be placed before, after or inside another *Sequence*.
A *Sequence* can't be placed before a *Source*,
because it doesn't accept any incoming flow.

.. note::
    If we try to instantiate a *Sequence* with a *Source* in the middle,
    the initialization will instantly fail and throw a *LenaTypeError*
    (a subtype of Python's *TypeError*).

    All *Lena* exceptions are subclassed from *LenaException*.
    They are raised as early as possible
    (not after a long analysis was fulfilled and discarded).

Since we can't use an infinite series in practice,
we must stop it at some point. 
We take the first million of its items using a *Slice* element.
*Slice* and *CountFrom* are similar to *islice* and *count* functions
from Python's standard library module *itertools*.
*Slice* can also be initialized with *start, stop[, step]* arguments,
which allow to skip some initial or final subset of data (defined by its index),
or take each *step*-th item
(if the *step* is two, use all even indices from zero).

We apply a further transformation of data with a *lambda*,
and sum the resulting values.

Finally, we materialize the results in a *list*,
and obtain a rough approximation of *pi*.

2. Lazy evaluation
^^^^^^^^^^^^^^^^^^
Let us look at the last element of the previous sequence.
Its class has a method *run*, which accepts the incoming *flow*:

.. _1_sum:

.. code-block:: python

    class Sum():
        def run(self, flow):
            s = 0
            for val in flow:
                s += val
            yield s

Note that we give the final number not with *return*,
but with *yield*.
*Yield* is a Python keyword,
which turns a usual function into a *generator*.

*Generators* are Python's implementation of *lazy evaluation*.
In the very first example we used a line

>>> results = s.run([0, 1, 2, 3])

The method *run* of a *Sequence* is a generator.
When we call a generator, we obtain the result,
but no computation really occurs,
no statement from the generator's code is executed.
To actually calculate the results, the generator must be materialized.
This can be done in a container (like a *list* or *tuple*) or in a cycle:

>>> for res in results:
...     print(res)

Lazy evaluation is good for:

* performance. 
  Reading data files may be one of the longest steps in simple data analysis.
  Since lazy evaluation uses only one value at a time,
  this value can be used immediately without waiting
  when the reading of the whole data set is finished. 
  This allows us to make a complete analysis in almost the same time
  as just to read the input data.
* low memory impact.
  Data is immediately used and not stored anywhere.
  This allows us to analyse data sets larger than the physical memory,
  and thus makes our program *scalable*.

Lazy evaluation is very easy to implement in Python using a *yield* keyword.
Generators must be carefully distinguished from ordinary functions in Lena.
If an object inside a sequence has a *run* method, it is assumed to be a generator.
Otherwise, if the object is callable, it is assumed to be a function,
which makes some simple transformation of the input value.

Generators can yield zero or multiple values.
Use them to alter or reduce data *flow*.
Use functions or callable objects for calculations
that accept and return a single *value*.

.. todo?
    - example of Sequence.run

3. Context
^^^^^^^^^^
Lena's goal is to cover the data analysis process
from beginning to end.
The final results of an analysis are tables and plots,
which can be used by people.

Lena doesn't draw anything itself, but relies on other programs.
It uses a library *Jinja* to render text templates.
There are no predefined templates or magic constants in Lena,
and users have to write their own ones.
An example for a one-dimensional LaTeX plot is:

.. code-block:: LaTeX
    :emphasize-lines: 13

    % histogram_1d.tex
    \documentclass{standalone}
    \usepackage{tikz}
    \usepackage{pgfplots}
    \pgfplotsset{compat=1.15}

    \begin{document}
    \begin{tikzpicture}
    \begin{axis}[]
    \addplot [
        const plot,
    ]
    table [col sep=comma, header=false] {\VAR{ output.filepath }};
    \end{axis}
    \end{tikzpicture}
    \end{document}

This is a simple TikZ template except for one line:
*\\VAR{ output.filepath }*.
*\\VAR{ var }* is substituted with the actual value of *var*
during rendering.
This allows to use one template for different data,
instead of creating many identical files for each plot.
In that example, variable *output.filepath*
is passed in a rendering *context*.

A more sophisticated example could be the following:

.. code-block:: LaTeX

    \BLOCK{ set var = variable if variable else '' }
    \begin{tikzpicture}
    \begin{axis}[
        \BLOCK{ if var.latex_name }
            xlabel = { $\VAR{ var.latex_name }$
            \BLOCK{ if var.unit }
                [$\mathrm{\VAR{ var.unit }}$]
            \BLOCK{ endif }
            },
        \BLOCK{ endif }
    ]
    ...

If there is a *variable* in *context*, it is named *var* for brevity.
If it has a *latex_name* and *unit*,
then these values will be used to label the x axis.
For example, it could become *x [m]* or *E [keV]* on the plot.
If no name or unit were provided,
the plot will be rendered without a label,
but also without an error or a crash.

*Jinja* allows very rich programming possibilities.
Templates can set variables, use conditional operators and cycles.
Refer to Jinja documentation [#f2]_ for details.

To use *Jinja* with LaTeX, Lena slightly changed its default syntax [#f3]_:
blocks and variables are enclosed in *\\BLOCK* and *\\VAR* environments
respectively.

A *context* is a simple Python dictionary or its subclass.
*Flow* in Lena consists of tuples of *(data, context)* pairs.
It is usually not called *dataflow*, because it also has context.
As it was shown earlier, context is not necessary for Lena sequences.
However, it greatly simplifies plot creation
and provides complementary information with the main data.
To add context to the flow, simply pass it with data
as in the following example:

.. code-block:: python

    class ReadData():
        """Read data from CSV files."""

        def run(self, flow):
            """Read filenames from flow and yield vectors.

            If vector component could not be cast to float,
            *ValueError* is raised.
            """
            for filename in flow:
                with open(filename, "r") as fil:
                    for line in fil:
                        vec = [float(coord)
                               for coord in line.split(',')]
                        # (data, context) pair
                        yield (vec, {"data": {"filename": filename}})

We read names of files from the incoming *flow* and yield coordinate vectors.
We add file names to a nested dictionary "data"
(or whatever we call it).
*Filename* could be referred in the template as *data["filename"]*
or simply *data.filename*.

Template rendering is widely used
in a well developed area of web programming,
and there is little difference between rendering
an HTML page or a LaTeX file, or any other text file.
Even though templates are powerful,
good design suggests using their full powers only when necessary.
The primary task of templates is to produce plots,
while any nontrivial calculations should be contained in data itself
(and provided through a context).

Context allows *separation of data and presentation* in Lena.
This is considered a good programming practice,
because it makes parts of a program focus on their primary tasks
and avoids code repetition.

.. This is not a benefit, just a consequence

Since all data flow is passed inside sequences of the framework,
context is also essential
if one needs to pass some additional data to the following elements.
Different elements update the context from flow with their own context,
which persists unless it is deleted or changed.

A real analysis example
-----------------------
Now we are ready to do some real data processing.
Let us read data from a file and make a histogram of *x* coordinates.

.. note::
    The complete example with other files for this tutorial can be found
    in *docs/examples/tutorial* directory of the framework's tree
    or `online <https://github.com/ynikitenko/lena/tree/master/docs/examples/tutorial>`_.

.. _main_py:

.. literalinclude:: ../../examples/tutorial/1_intro/main.py
    :caption: main.py

If we run the script, the resulting plots and intermediate files
will be written to the directory *output/*,
and the terminal output will be similar to this:

.. container:: noscrollbar

    | $ python main.py
    | pdflatex -halt-on-error -interaction batchmode -output-directory output output/x.tex
    | pdftoppm output/x.pdf output/x -png -singlefile
    | [('output/x.png', {'output': {'filetype': 'png'}, 'data': {'filename': '../data/normal_3d.csv'}, 'histogram': {'ranges': [(-10, 10)], 'dim': 1, 'nbins': [10]}})]

During the run, the element *LaTeXToPDF* called *pdflatex*, and *PDFToPNG* called *pdftoppm* program.
The commands are printed with all arguments, so that if there was an error during LaTeX rendering,
you can run this command manually until the rendered file *output/x.tex* is fixed (and then fix the template).

The last line of the output is the data and context,
which are the results of the sequence run.
The elements which produce files usually yield *(file path, context)* pairs.
In this case there is one resulting value, which has a string *output/x.png* as its *data* part.

Let us return to the script to see the sequence in more details.
The sequence *s* runs one data file (the list could easily contain more).
Since our *ReadData* produces a *(data, context)* pair, the following lambda
leaves the *context* part unchanged, and gets the zeroth index of each incoming vector
(which is the zeroth part of the *(data, context)* pair).

This lambda is not very readable,
and we'll see a better and more general approach in the next part of the tutorial.
But it shows how the *flow* can be intercepted and transformed
at any point within a sequence.

The resulting *x* components fill a *Histogram*,
which is initialized with *edges*
defined a *mesh* from *-10* to *10* with 10 bins.

This histogram, after it has been fed with the complete *flow*,
is transformed to a *CSV* (comma separated values) text.
In order for external programs (like *pdflatex*) to use the resulting table,
it must be written to a file.

*MakeFilename* adds file name to *context["output"]* dictionary.
*context.output.filename* is the file name without path and extension
(the latter will be set by other elements depending on the format of data:
first it is a *csv* table, then it may become a *pdf* plot, etc.)
Since there is only one file expected, we can simply call it *x*.

*Write* element writes text data to the file system.
It is initialized with the name of the output directory.
To be written, the context of a value must have an “output” subdictionary.

After we have produced the *csv* table,
we can render our LaTeX template *histogram_1d.tex* with that table and *context*,
and convert the plot to *pdf* and *png*.
As earlier, *RenderLaTeX* produces text,
which must be written to the file system before used.

Congratulations: now you can do a complete analysis
using the framework, from the beginning to the final plots.
In the end of this part of the tutorial we'll show several Lena elements
which may be useful during development.

Elements for development
------------------------
Let us use the structure of the previous analysis
and add some more elements to the sequence:

.. code-block:: python

    from lena.context import Context
    from lena.flow import Cache, End, Print

    s = Sequence(
        Print(),
        ReadData(),
        # Print(),
        Slice(1000),
        lambda val: val[0][0], # data.x
        Histogram(mesh((-10, 10), 10)),
        Context(),
        Cache("x_hist.pkl"),
        # End(),
        ToCSV(),
        # ...
    )

*Print* outputs values, which pass through it in the *flow*.
If we suspect an error or want to see exactly what is happening at a given point,
we can put any number of *Print* elements anywhere we want.
We don't need to search for other files and add print statements there
to see the input and output values.

*Slice*, which we met earlier when approximating *pi*,
limits the flow to the specified number of items.
If we are not sure that our analysis is already correct,
we can select only a small amount of data to test that.

*Context* is an element, which is a subclass of *dictionary*,
and it can be used as a context when a formatted output is needed.
If a *Context* object is inside a sequence,
it transforms the *context* part of the flow to its class,
which is indented during output (not in one line, as a usual dict).
This may help during manual analysis of many nested contexts.

*Cache* stores the incoming flow or loads it from file.
Its initialization argument is the file name to store the flow.
If the file is missing, then *Cache* creates that, runs the previous elements,
and stores values from the flow into the file.
On subsequent runs it loads the flow from file, and no previous elements are run.
*Cache* uses *pickle*,
which allows serialization and deserialization of most Python objects
(except function’s code).
If you have some lengthy calculation and want to save the results
(for example, to improve plots, which follow in the sequence),
you can use *Cache*.
If you changed the algorithm before *Cache*,
simply delete the file to refill that with the new flow.

*End* runs all previous elements and stops analysis here.
If we enabled that in this example,
*Cache* would be filled or read (as without the *End* element),
but nothing would be passed to *ToCSV* and further.
One can use *End* if they know for sure, that the following analysis is incomplete and will fail.

-----------

.. rubric::
    Summary

Lena encourages to split analysis into small independent *elements*,
which are joined into *sequences*.
This allows to substitute, add or remove any element
or transform the *flow* at any place,
which may be very useful for development.
Sequences can be elements of other sequences,
which allows their *reuse*.

*Elements* can be callables or *generators*.
Simple callables can be easily added to transform each value from the *flow*,
while generators can transform the *flow*,
adding more values or reducing that.
Generators allow lazy evaluation, which benefits memory impact
and generalizes algorithms to use potentially many values instead of one.

Complete information about the analysis is provided through the *context*.
It is the user's responsibility to add the needed context
and to write templates for plots.
The user must also provide some initial context for naming files and plots,
but apart from that the framework transfers and updates context itself.

We introduced two basic sequences.
A *Sequence* can be placed before, after or inside another *Sequence*.
A *Source* is similar to a *Sequence*, but no other sequence can precede that.

.. this option doesn't work:
..     :width: 50%

.. list-table:: Sequences
    :header-rows: 1
    :widths: 15 70 15
    :align: center

    * - Sequence
      - Initialization
      - Usage
    * - Sequence
      - Elements with a *__call__(value)* or *run(flow)* method (or callables)
      - s.run(*flow*)
    * - Source
      - The first element has a *__call__()* method (or is callable),
        others form a *Sequence*
      - s()

In this part of the tutorial
we have learnt how to make a simple analysis of data read from a file
and how to produce several plots using only one template.
In the next part we'll learn about
new types of elements and sequences
and how to make several analyses
reading a data file only once.

.. rubric::
    Exercises

#. Ivan wants to become more familiar with generators and implements an element *End*.
   He writes this class:

   .. code-block:: python

       class End(object):
           """Stop sequence here."""

           def run(self, flow):
               """Exhaust all preceding flow and stop iteration."""
               for val in flow:
                   pass
               raise StopIteration()

   and adds this element to :ref:`main.py <main_py>` example above.
   When he runs the program, he gets

   .. container:: noscrollbar

       | Traceback (most recent call last):
       |   File "main.py", line 46, in <module>
       |     main()
       |   File "main.py", line 42, in main
       |     results = s.run([data_file])
       |   File "lena/core/sequence.py", line 70, in run
       |     flow = elem.run(flow)
       |   File "main.py", line 24, in run
       |     raise StopIteration()
       | StopIteration

   It seems that no further elements were executed, indeed.
   However, Ivan recalls that *StopIteration* inside a generator
   should lead to a normal exit and should not be an error. What was done wrong?

#. Svetlana wants to make sure
   that no statement is really executed during a generator call.
   Write a simple generator to check that.

#. *Count* counts values passing through that.
   In order for that not to change the data flow,
   it should add results to the context.
   What other design decisions should be considered?
   Write its simple implementation and check that it works as a sequence element.

#. Lev doesn't like how the output in previous examples is organised.

   "In our object-oriented days,
   I could use only one object to make the whole analysis", - he says.
   "Histogram to CSV, Write, Render, Write again,...:
   if our output system remains the same,
   and we need to repeat that in every script,
   this is a code bloat".

   How to make only one element for the whole output process?
   What are advantages and disadvantages of these two approaches?

    ..
        #. \* Lev feels that the framework is limiting his code.

           "Why do I need to name a generator a *run* method of some class?",- he says.
           "If an object makes some work, it should be called appropriately: run, or go, or fly,
           or paint - depending on the object itself.
           And, definitely, Python must allow to distinguish between a function and a generator.
           Why then should a programmer manually choose appropriate names to satisfy some framework?"

           In the next part we will say about adapters,
           that allow to use elements with methods named differently (not *run* or *__call__*).
           Do you know whether generators and simple functions can be distinguished in Python?

#. \*\* Remember the implementation of :ref:`Sum <1_sum>` earlier.
   Suppose you need to split one flow into two to make two analyses,
   so that you don't have to read the flow several times
   or store it completely in memory.

   Will this *Sum* allow that, why? How should it be changed?
   These questions will be answered in the following part of the tutorial.

The answers to the excercises are given in the end of the tutorial.

.. rubric:: Footnotes

.. [#f1] This possibility may be added in the future.
.. [#f2] Jinja documentation: https://jinja.palletsprojects.com/
.. [#f3] To use Jinja to render LaTeX was proposed `here <http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs>`__ and `here <https://web.archive.org/web/20121024021221/http://e6h.de/post/11/>`__, template syntax was taken from the original article.

..
    todo:
    Add an excercise on context (with get_context, get_data, probably).
