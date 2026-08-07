API reference
=============

This section documents the public Python API of ``odxtools``. Docstrings are
extracted with Sphinx autodoc. Prefer the helpers exported from the top-level
``odxtools`` package for everyday use.

Package overview
----------------

.. automodule:: odxtools
   :members:
   :undoc-members:
   :imported-members:

Core class: Database
--------------------

``Database`` is the in-memory representation of a diagnostic description
loaded from one or more ODX/PDX inputs.

.. autoclass:: odxtools.database.Database
   :members:
   :undoc-members:
   :show-inheritance:

Loading helpers
---------------

The following functions are re-exported from :mod:`odxtools` and are the
usual entry points:

* :func:`odxtools.load_pdx_file` — load a ``.pdx`` archive
* :func:`odxtools.load_odx_file` — load a single ``.odx`` / ``.odx-*`` file
* :func:`odxtools.load_file` — load a file by path (PDX or ODX)
* :func:`odxtools.load_files` — load multiple files into one database
* :func:`odxtools.load_directory` — load all ODX files from a directory
* :func:`odxtools.write_pdx_file` — write a database back to a PDX file

See also :mod:`odxtools.loadfile` for the underlying implementations.
