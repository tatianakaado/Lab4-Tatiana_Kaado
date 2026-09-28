Docstrings and Sphinx workflow
==============================

Why docstrings?
---------------

A docstring is the first string literal in a module, class, or function. Python
exposes it through ``__doc__`` and ``help()``. A ``#`` comment explains source
lines but is not available through those interfaces. This submission uses
triple-double-quoted docstrings and reStructuredText field lists.

The annotated function below illustrates parameters, types, return values, and
an exception. Classes describe their responsibilities and constructor fields;
methods explain side effects and error behavior.

.. literalinclude:: ../school_mgmt/models.py
   :language: python
   :pyobject: validate_email

Inspect documentation directly::

   python -c "from school_mgmt.models import validate_email; print(validate_email.__doc__)"
   python -c "from pyqt_app import SchoolManagementQt; help(SchoolManagementQt.load_json)"

Bootstrap inherited from Lab 3
-------------------------------

In Lab 3, after installing its requirements, the initial documentation directory was
created with the non-interactive equivalent of the lab's quickstart wizard::

   sphinx-quickstart -q -p "School Management System — PyQt5" -a "Tatiana Kaado" -v 1.0 -r 1.0.0 -l en --no-sep --ext-autodoc --ext-viewcode --makefile --batchfile docs

Quickstart creates ``conf.py``, ``index.rst``, ``Makefile``, and ``make.bat``.
The configuration was then completed with Napoleon and the Read the Docs theme.
Do not rerun quickstart over the submitted documentation.

Configuration
-------------

The project root is inserted into ``sys.path`` using the configuration file's
location. Autodoc can therefore import the GUI and shared package independently
of the current working directory. The real PyQt5 dependency is installed;
no application modules are mocked. The entry-point guard prevents a GUI
from launching while Sphinx imports its classes.

.. literalinclude:: conf.py
   :language: python
   :caption: docs/conf.py

Generate the module pages
-------------------------

From the project root, the following command scans Python sources while omitting
tests, evidence tools, and local environments::

   sphinx-apidoc -f -o docs . docs tests .venv venv tk_app.py demo.py

This creates ``pyqt_app.rst``, ``school_mgmt.rst``, and ``modules.rst``. The root
page includes ``modules`` in its toctree, as required in the lab handout:

.. literalinclude:: index.rst
   :language: rst
   :start-at: .. toctree::
   :end-at:    verification

Build and rebuild
-----------------

From the project root::

   python -m sphinx -b html -W --keep-going docs docs/_build/html

Or use the generated Makefile with the environment activated::

   cd docs
   make html
   make clean html

On Windows use ``make.bat html``; use ``make.bat clean`` followed by
``make.bat html`` for a clean rebuild. The Python command works across platforms.
Warnings are treated as errors in the verified build. After a successful build,
open ``docs/_build/html/index.html``. After editing a docstring, rebuild so
HTML reflects the new source. Rerun apidoc when adding or removing modules.

Run the Lab 4 tests separately::

   python -m unittest discover -s tests -v

If a shell reports an unsupported locale on macOS, run the Sphinx commands
with ``LC_ALL=en_US.UTF-8``. This was needed by the environment used here.

References
----------

* Course handout: ``Lab 3-Documentation.docx``, supplied with the assignment.
* `Sphinx autodoc documentation <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
* `Sphinx apidoc command <https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html>`_
