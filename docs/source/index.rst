.. Lena documentation master file, created by
   sphinx-quickstart on Mon May  6 17:12:27 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. |br| raw:: html

   <br />

..
    todo:
    - Lena is intended to... - we can write about its mission
      (create good and beautiful software).
    -- - in the very end of the tutorial. from philosophical point of view.
      Ready to analyse several issues at once.
      Data analysis is comparison of different entities (expected and observed).
    - Add Thanks subsection
    - add release notes somewhere in the future.
    - create When should I use Lena? Make Overwiew small.

========
Overview
========

Lena is an architectural framework for data analysis.
It is written in a popular programming language Python
and works with Python versions 2, 3 and PyPy (2 and 3).

Lena features from programming point of view include:

- simple and powerful programming language.

- modularity, weak coupling. Algorithms can be easily added, replaced or reused.

- code reuse. Logic is separated from presentation. One template can be used for several plots.

- rapid development. One can run only those elements which already work.
  During development only a small subset of data can be analysed (to check the code).
  Results of heavy calculations can be easily saved.

- performance. Lazy evaluation is good for memory and speed. Several analyses can be done reading data once. PyPy with just-in-time compiler can be used if needed.

- easy to understand, structured and beautiful code.

From data analysis perspective:

- comparison of analyses with arbitrary changes (including different input data or algorithms).

- algorithm reuse for a subset of data
  (for example, to see how an algorithm works at different positions in the detector).

- analysis consistency.
  When we run several algorithms for same data or reuse an algorithm,
  we are confident that we use same data and algorithm.

- algorithms can be combined into a more complex analysis.

Lena was created in experimental neutrino physics and is named after a great Siberian river.

.. .. rst-class:: hidden

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   Tutorial <tutorial>
   Reference <reference>

..
   Q & A <questions_and_answers>

    When to use Lena
    ----------------

    Your choice may start with the programming language.
    Here are the advantages of Python
    (adapted from this `post <https://medium.com/crowdbotics/when-to-use-django-and-when-not-to-9f62f55f693b>`_, where you can find the sources of information):

    - Python is one of the most popular and growing languages in the world.
    - Python is really easy to learn. It is usually first language of choice for developers.
    - Don't let the previous statement misguide you in believing that it's only for beginners. Python is used in cutting edge tech as well. Many giants including Google use Python in their tech stack extensively.
    - It plays nice with other languages.
    - Developing with Python does not mean that you have to stick with everything that's built with Python only. You may use libraries built with many other languages, including C/C++/Java.
    - Python is portable, and easy to read.
    - Python can even run on JVM. Check out Jython.
    - Python is extensively used and supported in cutting-edge tech like Big Data, Machine Learning, etc.
    - Access to huge PyPI library.

    "Program development using Python is 5–10 times faster than using C/C++,
    and 3–5 times faster than using Java", -
    `estimates <https://www.python.org/doc/essays/omg-darpa-mcc-position/>`_ the author of Python. 


    .. A general programming language is a tool that allows to express

    A general programming language can be used to express
    a vast range of commands and ideas.
    An architectural framework limits what can be done within that.

    OTOH definite structure allows very complex algorithms


    Actually easier than cmake

    A software library provides data and algorithms that you can use in your programs.
    An architectural framework 


Installation
------------

Minimal
^^^^^^^

Install the latest official version from PyPI:

.. code-block:: console

    pip install lena

Lena core modules have no dependencies except Python standard libraries.

Recommended
^^^^^^^^^^^

.. code-block:: console

    pip install lena jinja2

*jinja2* is used to create templates for plots.
Also install the following programs:

* *pdflatex* to produce pdf files from LaTeX,
* *pgfplots* and *TikZ* to produce LaTeX plots,
* *pdftoppm* to convert pdf files to png.

.. * *# ssh-agent* to use Lena on remote servers.

These programs can be found in your OS packages.
For example, in Fedora Core 29 install them with

.. code-block:: console

    dnf install texlive-latex texlive-pgfplots poppler-utils

..
    pdflatex from texlive-latex
    pgfplots from texlive-pgfplots
    pdftoppm from poppler-utils

*pdflatex* and *pgfplots* are contained in the standard
`TeX Live <https://www.ctan.org/pkg/texlive>`_ distribution.

Full
^^^^
This installation is needed only if you want to extend and develop Lena.
Download the full repository (with history) from GitHub
and install all development dependencies:

..
    # without jinja2
    # unfortunately, now jinja2 seems to be not
    # in the default requirements.
    pip install --no-deps lena

.. code-block:: console

    git clone https://github.com/ynikitenko/lena
    pip install -r lena/requirements.txt

Install command line programs from the previous subsection and adjust PYTHONPATH
as shown in the next subsection.

GitHub or PyPI
^^^^^^^^^^^^^^

PyPI contains the last official release, which was tested for more Python versions.
GitHub contains the most recent development code for experienced users.
Usually it is well tested too,
but there is a chance that a newly introduced interface will be changed.

For most users *pip* install should be easier.
If for some reasons you can't do that, you can get an archive
of an official release
from GitHub `releases <https://github.com/ynikitenko/lena/releases>`_.

*pip* installs the framework into a system directory, while to install with *git*
you need to adjust the PYTHONPATH.  
Add to your profile (e.g. ``.profile`` or ``.bashrc`` on Linux)

.. .bashrc is for non-interactive shells, which are used with 'ssh command'.

.. code-block:: console

    export PYTHONPATH=$PYTHONPATH:<path-to-lena>

and replace *<path-to-lena>* with the actual path to the cloned repository.

Documentation
-------------
To get started, read the :doc:`tutorial`.

Complete documentation for Lena modules can be found in the :doc:`reference`.

.. and specific topics
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

Lena is free software released under
`Apache <https://github.com/ynikitenko/lena/blob/master/LICENSE>`_
software license (version 2).
You can use it freely for your data analysis, read its source code and modify it.

It is intended to help people in data analysis, 
but we don't take responsibility if something goes wrong.

..
    .. _contacts:

    Contacts
    --------
    *metst13 at gmail dot com*

Alternatives
------------
`Ruffus <http://www.ruffus.org.uk/index.html>`_ 
is a Computation Pipeline library for Python used in science and bioinformatics. 
It connects program components by writing and reading files.

..
    These are not alternatives, I see few of them in Python, or they do different things.
    `Computational Data Analysis Workflow Systems <https://github.com/common-workflow-language/common-workflow-language/wiki/Existing-Workflow-systems>`_
    `A curated list of awesome pipeline toolkits <https://github.com/pditommaso/awesome-pipeline>`_

