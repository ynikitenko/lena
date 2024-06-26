# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

def setup(app):
    app.add_js_file('copybutton.js')
    # add all custom css to this file,
    # otherwise another custom.css will overwrite it.
    app.add_css_file('custom.css')
    app.add_js_file('custom.js')
    # This is a popular repository, so it's safe to use it by a link,
    # but in case of its removal, check https://github.com/zenorocha/clipboard.js
    # It is 10 Kb, so we won't make its local copy for now.
    app.add_js_file('https://cdn.jsdelivr.net/npm/clipboard@1/dist/clipboard.min.js')

highlight_language = 'python'

# -- Project information -----------------------------------------------------

project = u'Lena'
copyright = u'2020-2024, Yaroslav Nikitenko'
author = u'Yaroslav Nikitenko'

# The short X.Y version
version = u'0.6'
# The full version, including alpha/beta/rc tags
release = u'0.6-beta'
# release = u'0.1-alpha'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# otherwise autodoc_default_options raises an error.
# needs_sphinx = '2.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    # 'sphinx.ext.intersphinx',
    # 'sphinx_automodapi.automodapi',
    'sphinx.ext.coverage',
    # 'sphinx-prompt', # doesn't show command output.
    'sphinx.ext.graphviz',
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

# automodapi seems nice, but I could't get it generate separate class pages
# automodapi_inheritance_diagram = False

# autodoc_default_flags = ['members']
# unfortunately, this gives a warning when __call__ is missing
# https://github.com/sphinx-doc/sphinx/issues/6771
autodoc_default_options = {
    # https://github.com/sphinx-doc/sphinx/issues/5459
    # for sphinx older than 2.0 None means True
    'members': None,
    'special-members': '__call__',
    # 'undoc-members': True,
    # 'exclude-members': '__weakref__'
}
# autosummary_generate = True

# Both the class' and the __init__ method's docstring are concatenated and inserted.
autoclass_content = "both"
## autodoc-skip-member('lena.core', 'module')
# sphinx.ext.autodoc.autoclass_content = "both"
add_module_names = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"
locale_dirs = ['locale/']
gettext_compact = False
gettext_uuid = False
gettext_additional_targets = ["literal-block"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['lena.math']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = "nature"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation:
# https://www.sphinx-doc.org/en/master/usage/theming.html#builtin-themes

# html_theme_options = {
#     globaltoc_maxdepth: 2,  # unavaliable for the nature theme
# }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# Hint: use only the existing source/_static;
# all new "custom.css" will overwrite the other ones.
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Lenadoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Lena.tex', u'Lena Documentation',
     u'Yaroslav Nikitenko', 
     'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'lena', u'Lena Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Lena', u'Lena Documentation',
     author, 'Lena', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
