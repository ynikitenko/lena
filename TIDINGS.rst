====================
  Lena release 0.4
====================

Lena v0.4 was released on 7th November 2021.

What's new
----------

Histograms and related algorithms get great refactoring.

Logic and interface of SplitIntoBins, MapIntoBins and IterateBins
has largely improved.
These elements allow analysis to be reused for data subsamples
defined by arbitrary values (mapped into bins).

Histogram structure becomes more robust and can be used in other
Python code (outside Lena framework).

Vector3 gets a stable initialization interface
(not from a list, but from 3 coordinate values).

Histogram structure becomes more robust and can be used in other
Python code (outside Lena framework).

Vector3 gets a stable initialization interface
(not from a list, but from 3 coordinate values).

Adds new elements and a new module input.

* lena.flow changes:

  * Adds Filter (a standard functional instrument).
  * IterateBins adds a keyword argument *select_bins*.
  * Adds Progress (estimate processed / remaining data).
  * Adds an iterator Reverse (reverse the flow).
  * Adds RunIf (conditionally run a sequence for selected values from the flow).
    It existed earlier as TransformIf, but was unused and deprecated.
  * Slice supports negative *start* and *stop* parameters during run.
  * Selector gets *raise_on_error* keyword argument
    (previously always returned ``False``).

* lena.math changes:

  * vector3 supports cylindrical coordinates *rho* and *rho2*.

* lena.output changes:

  * LaTeXToPDF reprocesses pdf files
    if their tex templates were modified after pdf creation.
  * Adds *prefix* and *suffix* keyword arguments to MakeFilename.
    They can be used to create parts of file names
    before they are created (e.g. suffix="_log").
  * RenderLaTeX accepts keyword argument *verbose*.

* lena.structures changes:

  * Adds HistToGraph.
  * Adds histogram class.
    Histograms are separated into a structure histogram
    and an element Histogram (allowing great conceptual decoupling).
    Should not affect user code in Sequences.

A new module *input* was created.
Its context name is suggested "input".
At the moment it contains several ROOT bindings:
*read_root_file* and *read_root_tree*
(ROOT is a data analysis framework used by physicists, https://root.cern).

*lena.output* adds a submodule *write_root_tree*.
Unfortunately, this class is not thoroughly tested
and is not included into the documentation yet.

Bug fixes
---------

* lena.flow fixes:

  * Fixes Slice.
  * Fixes split_into_bins._iter_bins_with_edges
    (had problems with multidimensional bins; used in IterateBins).
  * Numerous fixes in IterateBins (related to context).
  * Numerous fixes in MapBins (related to context).
  * Numerous fixes in SplitIntoBins (related to context).

* lena.output fixes:

  * Fixes LaTeXToPDF (didn't print output in case of errors even with verbosity set).
  * Fixes LaTeXToPDF (iteration on a mutated dictionary,
    leading to a runtime error with tens of plots).
  * Fixes RenderLaTeX (didn't work with context.output.template).

Deprecations and backward incompatible changes
----------------------------------------------

* lena.context changes:

  * Context.formatter is now private.
  * str_to_dict no longer accepts a dictionary.
  * Refactor update_nested.
    *other* is no longer required to be a dictionary with one key:
    the key is now provided as the first argument.

* lena.flow changes:

<<<<<<< HEAD
  * Renames flow.ISlice to Slice. ISlice is deprecated.
  * Renames TransformBins to IterateBins.
    Completely rework its context handling.
  * Renames ReduceBinContent to MapBins.
    Changes semantics of a keyword argument drop_bins_context.
    Renames its keyword argument *transform* to *seq*.
    Renames keyword argument *select* to *select_bins*,
    change order of keyword arguments.
    Completely rework its context handling.
  * SplitIntoBins adds context to *histogram* and *variable*
    (not to *split_into_bins*).
    This allows unification of SplitIntoBins
    with common analysis using histograms and variables
    (useful when creating plots from one template).
    SplitIntoBins is no longer a descendant of FillCompute
    (it is not needed because of structural subtyping).
    Removes initialization keyword argument *transform*,
    because it can be equally inserted later in the sequence.
    Renames keyword argument *arg_func* to *arg_var*
    (since it is a Variable).

* lena.output changes:

  * Renames Writer to Write. Writer is deprecated.
  * Renames RenderLaTeX keyword argument
    *template_path* to *template_dir* (to improve clarity).
    Adds hash symbols to its verbose output.

* math.vector3 is initialized not from a vector, but from 3 values x, y and z.
  vector3 no longer transforms its components to floats.
  Thus it behaves like a number in Python
  (if it was integer, it is converted to float only when needed).
  Removes its __cmp__ method (not used).
* Renames structures.hist_to_graph keyword arguments
  to coincide with those of HistToGraph
  (*make_graph_value* to *make_value*, *bin_coord* to *get_coordinate*).
  Changes requirements for its *make_value* argument
  (now accepts one value instead of two).

Technical changes
-----------------

* Lena is tested and works with Python 3.10.
  Tox fails for Python 3.5-3.8 (unrelated to Lena).
  Tox uses correct pytest.
* Move sphinx requirements to docs/requirements.txt.
  Update documentation for newer Sphinx.
* Add .readthedocs.yaml config (fixes build fails on readthedocs).
* Change absolute imports to relative ones in __init__.py in packages.
* Import of NumpyHistogram becomes more robust
  (less prone to numpy import errors).
* Improves deprecation messages.
* ISlice.fill_into is tested with Hypothesis.
* Adds a private method variable.Variable._update_context.
* Pytest ignores ROOT tests if ROOT is not installed.
  ROOT tests are marked.
  Add tests/root/conftest.py with rootfile fixture,
  so that ROOT tests will be run in correct order
* Code improvement and refactoring.
* Documentation updates and improvements.
* Several new classes / modules become 100% tested.
* New tests added. Test coverage is 91% (286/3215 missing vs total).


====================
  Lena release 0.3
====================

Lena v0.3 was released on 23rd February 2021.

What's new
----------

Existing unchanged plots are no longer reprocessed.
This not only allows large time savings when adding new plots to existing ones,
but also improves code quality: the analyst is not tempted to comment out
already built plots in order to save processing time.

* Adds an example to GroupPlots.

* context changes:

  * Writer, LaTeXToPDF and PDFToPNG from lena.output and GroupPlots from lena.flow
    use and modify *context.output.changed*.

* lena.context changes:

  * Context attributes can be got and set with dot notation.
  * str_to_dict allows a new keyword argument *value*.
  * update_recursively allows a new keyword argument *value*.

* lena.output changes:

  * Adds *overwrite* keyword argument to LaTeXToPDF.
  * Adds *overwrite* keyword argument to PDFToPNG.
  * Adds *verbose*, *existing_unchanged* and *overwrite*
    initialization keyword arguments to Writer.

* variables.Combine now creates a *range* attribute if all its variables have range.

Bug fixes
---------

* Fixes var_context in variables.Combine.

Deprecations and backward incompatible changes
----------------------------------------------

* lena.context changes:

  * Context.formatter is now private.
  * str_to_dict no longer accepts a dictionary.

Technical changes
-----------------

* Lena is tested to work with Python 3.9, which was released in October 2020.
* New tests added. Test coverage is 92% (232/2776 missing vs total).


====================
  Lena release 0.2
====================

Lena v0.2 was released on May 9th, 2020.

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
