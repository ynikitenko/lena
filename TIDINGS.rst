====================
  Lena release 0.2
====================

Lena v0.2 was released on May 9, 2020.

What's new
----------

* Adds Russian translation (partial).
* Adds documentation for math.refine_mesh and math.flatten.

* lena.context changes:

  * str_to_dict allows empty string and can accept a dictionary.
  * Adds str_to_list.
  * Adds UpdateContext.
  * Renames *check_context_str* to *contains*.
    It accepts strings without dots and allows values to be compared with a string.
    Adds it to the documentation.

* lena.flow changes:

  * GroupPlots yields unchanged values if yield_selected is True.
  * Adds Not, a negative Selector.

* lena.output changes:

  * Writer corrects absolute paths runtime where relative paths must be present.
  * ToCSV uses duplicate_last_bin option for to_csv method when possible.

* lena.structures changes:

  * Adds cur_context keyword argument to Graph. Rescaled Graph retains the same *sort*.
  * Adds histogram functions get_bin_edges and iter_cells.
  * Adds HistCell class.
  * Adds *context* keyword argument to Histogram.


Bug fixes
---------

* Fixes context.get_recursively.
* Fixes context.update_context.
* Fixes structures.Graph.to_csv.

Deprecations and backward incompatible changes
----------------------------------------------

* Renames flow.GroupPlots initialization keyword argument *scale_to* to *scale*.
* structures.Histogram is no longer a subclass of FillCompute.

* lena.output changes:

  * MakeFilename accepts only a string for its make\_ keyword arguments
    (which are renamed to filename, dirname and fileext),
    and it no longer accepts a Sequence.
    MakeFilename requires double braces in context formatting strings.
    Its run method becomes __call__.
  * Moves format_context from output to context.
    format_context accepts a single string argument and
    only double braces instead of single ones.
  * Removes HistToCSV (deprecated since Lena 0.1).

Technical changes
-----------------

* Adds pytest.ini. Ignores warnings irrelevant to Lena.
* Adds TIDINGS.rst (release notes).
* Recommended Jinja2 version becomes 2.11.0 or newer.


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
