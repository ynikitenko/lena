.. Lena documentation master file, created by
   sphinx-quickstart on Mon May  6 17:12:27 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

========
Overview
========

Lena is an architectural framework for data analysis. It is written in Python and works with Python versions 2, 3 and PyPy.

These are Lena features from programming point of view:

- modularity, weak coupling. Algorithms can be easily added, replaced or reused.

- performance. Lazy evaluation is good for memory and speed. Several analyses can be done reading data once. PyPy with just-in-time compiler can be used if needed.

- code reuse. Logic is separated from presentation. One template can be used for several plots.

- rapid development. One can run only those elements which already work. During development only a small subset of data can be analysed. Results of heavy calculations can be easily saved.

- easy to understand, structured and beautiful code.

From data analysis perspective:

- comparison of analyses with arbitrary changes (including different input data or algorithms).

- algorithm reuse for a subset of data (for example, to see how an algorithm works at different coordinates in the detector).

- analysis consistency. When we run several algorithms for same data or reuse an algorithm, we are sure that we use same data and algorithm.

- algorithms can be combined into a more complex analysis.

Lena originated from experimental neutrino physics and is named after a great Siberian river.

.. .. rst-class:: hidden

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   Tutorial <tutorial>
   Reference <reference>

..
   Q & A <questions_and_answers>

Installation
------------

From pip
^^^^^^^^
Lena core modules depend only on Python standard libraries.
Other python extensions can be installed from pip:

::

    pip install lena
    # if you plan to render LaTeX templates
    pip install jinja2

..
    # without jinja2
    # unfortunately, now jinja2 seems to be not
    # in the default requirements.
    pip install --no-deps lena
    # or, for Python 3
    pip3 install lena

From github
^^^^^^^^^^^
::

    git clone https://github.com/ynikitenko/lena
    # most of requirements are for development only
    pip install -r lena/requirements.txt

Replace *<path-to-lena>* with the actual path to the directory *lena*
and add

.. code-block:: console

    export PYTHONPATH=$PYTHONPATH:<path-to-lena>

to your profile 
(e.g. ``.profile`` or ``.bashrc`` on Linux).

.. .bashrc is for non-interactive shells, which are used with 'ssh command'.

Additional programs
^^^^^^^^^^^^^^^^^^^

To fully use all available tools, you may need the following programs:

* *pdflatex* to produce pdf files from LaTeX.
* *pgfplots* and *TikZ* to produce LaTeX plots.
* *pdftoppm* to convert pdf files to png.

.. * *# ssh-agent* to use Lena on remote servers.

They are not necessary if you don't need to make plots or want to provide your own tools for that.

Documentation
-------------
To get started, read the :doc:`tutorial`.

.. Other tutorials are: ...

Complete documentation on Lena classes and specific topics can be found in the :doc:`reference`.

..
    For general questions, see :doc:`Questions & Answers <questions_and_answers>`.

..
    Limitations
    -----------
    :doc:`limitations`.

    Usage
    -----
    Get help
    ^^^^^^^^
    If you don't know how to get specific results using Lena, you can write to the author (:ref:`contacts <contacts>`),
    include *Lena* in the topic. For help on programming, use a general site like *stackoverflow*.

    .. ** to check ** : maybe Lena questions are possible on SO?

    Report bugs
    ^^^^^^^^^^^
    Submitted bugs are listed on *github issues*.
    If you found a bug, check whether it was already listed there. 

    .. If you are not sure whether a component really has a bug, you may see tests for that.
       If tests work normally, this may be an issue of your code.

    If it is new, make a possibly minimal working example and open an issue.

    Lena is tested during development, and it has **?** test coverage. 
    If you are not sure whether the error is in your code and not in Lena's component, 
    you may check tests for that component (in lena/tests directory).

    For any minor bug in the documentation (including orthography and punctuation), 
    please write to the author (:ref:`contacts <contacts>`).

    Request features 
    ^^^^^^^^^^^^^^^^
    If you believe a feature will be useful to many people and should be added to Lena, use *github issues*.

    Contribute
    ^^^^^^^^^^
    .. Participate, Development,...

    Contributions are welcome. 

    If you developed some non-trivial code which adds value to the existing framework,
    is documented and has some tests, please create a pull request

    .. Check.

        You may want to read the :doc:`internals`.

    .. English. And of general interest?

License
-------
Lena is free software licensed under Apache software license (version 2).
You can use it freely for your data analysis, read its source code and modify it.

.. It is tested and actively used, but we take no responsibility 

It is intended to help people in their data analysis, 
but we don't take responsibility if something goes wrong.

.. English. It is intended?

..
    .. _contacts:

    Contacts
    --------
    *metst13 at gmail dot com*

Alternatives
------------
`Ruffus <http://www.ruffus.org.uk/index.html>`_ 
is a Computation Pipeline library for python used in science and bioinformatics. 
It connects program components by writing and reading files.

..
    Lena is simple, beautiful, transparent (but understandable).
    These are not alternatives, I see few of them in Python, or they do different things.
    `Computational Data Analysis Workflow Systems <https://github.com/common-workflow-language/common-workflow-language/wiki/Existing-Workflow-systems>`_
    `A curated list of awesome pipeline toolkits <https://github.com/pditommaso/awesome-pipeline>`_

