====================
  Lena release 0.1
====================

Lena v0.1 was released on April 12-13, 2020.

What's new
----------

* Lena added to PyPI.
* Adds tutorial part 2 (Split).

* lena.context changes:

  * lena.context.update_recursively accepts a string as *other* argument.
  * Adds lena.context.difference.
  * Adds a parameter *level* to lena.context.intersection.

* lena.core changes:

  * FillCompute can be explicitly cast from FillRequest.
  * Adds *reset* method and keyword argument to FillRequest.
  * FillInto adapter now has a keyword *explicit*.
  * Adds *copy_buf* parameter to Split.
  * Adds LenaZeroDivisionError.

* lena.flow changes:

  * Adds lena.flow.Zip.
  * Adds lena.flow.get_data_context.

* lena.math changes:

  * Adds lena.math.Sum.
  * Adds parameter *pass_on_empty* to Mean.

* Adds performance measurements to tutorial/2_split/
* Adds performance optimizations.
* Adds *timeout* parameter to PDFToPNG.
* Adds *reset* method and *make_bins* keyword argument to Histogram.
* Adds example data files to tutorial.
* Adds multiple tests, license and documentation.

Bug fixes
---------

* Fixes setup.py.
* Fixes Graph and its documentation.
* Fixes lena.context.intersection.

Deprecations and backward incompatible changes
----------------------------------------------

* Makes lena.flow.Print a *Call* element (not *Run*).
* Removes lena.run (unused).
* Removes *rescale_value* kwarg from Graph.

* lena.context changes:

  * Renames str_to_context to str_to_dict, adds that to documentation.
  * Undocuments several context functions (probably unuseful).

* lena.math changes:

  * Numpy histogram no longer has a compute method.
  * lena.math.Mean now raises LenaZeroDivisionError instead of LenaRuntimeError.

* lena.output changes:

  * Removes 'repeat' from RenderLaTeX. Makes Template and Environment private.
  * If data has *to_csv* method, that must support kwargs *separator* and *header*.
  * Creates ToCSV. Deprecates HistToCSV.
