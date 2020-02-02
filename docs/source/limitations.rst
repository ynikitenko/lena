:orphan:

.. no toctree needed

Limitations
===========

Performance
-----------
not for number crunching

Python is high level

But: most time is spent on reading data and making plots
No serious performance measurements (and hence optimizations) were made yet.

Development status
------------------
small user base,
may have bugs

but tested
and used by the author
This limitation on the second place

General
-------
No global settings exist, everything is defined during the initialization.
No configuration options can be passed via the command line.

In fact, the first feature may be more useful for large projects
than for simple scripts. The second one seems more important.
This features are waiting to be implemented.

Flow
----

Missing Filter and Zip
^^^^^^^^^^^^^^^^^^^^^^
Functional programming may seem weird without a filter,
but in fact the author didn't need to use that,
and when he needed, a better solution was found.
Moreover, Lena's design suggests that one should expect
any unknown values from the flow (if that's not during histogram fill),
and pass that unchanged.
One can very simply implement a filter using a :class:`Selector`.

Zip may also not fit well with Lena's design, because it would
impose limitations on the order of flow elements (if that is important).
It may also be duplication of some :class:`Split`'s logic.

These classes may be implemented,
if good non-trivial example uses for them is given.

Split into bins
^^^^^^^^^^^^^^^

If the analysis produced not equal number of data during *compute()*,
in Python 3 the minimum number will be used,
while in Python 2 some bins will be filled with None.

Waiting to provide general settings for that.

Output
------

Only one engine can be used to create pdf (``pdflatex``)
and convert pdf to png (``pdftoppm``).
No html (or other) plots are used.

Waiting to be implemented by people who use alternative tools.

LaTeXToPDF
^^^^^^^^^^

It has an option to support multiprocess execution,
but can't limit the number of these processes.

Waiting to be implemented.

Development
-----------

No logging system is present.
For example, :class:`HistToCSV` prints a warning to ``stdout``
when it can't convert a 3-dimensional histogram.
This will be implemented not earlier
than at least after one other example is found.

