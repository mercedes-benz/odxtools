Getting Started with odxtools
=============================

Welcome! 👋  
This guide will help you understand what **odxtools** is, how to install it, and how to start using it — step by step.

What is odxtools?
-----------------
**odxtools** is a Python tool for working with vehicle diagnostic data.  
It helps you read and understand `.pdx` and `.odx` files, which describe how a car's electronic control units (ECUs) communicate.

These files follow a format called **ODX (Open Diagnostic data eXchange)**, an international standard used by car manufacturers.

If you're working on car diagnostics, testing ECUs, or developing automotive tools — this library is for you!

---

Installing odxtools
-------------------

You can install it like any other Python package using pip:

.. code-block:: bash

   pip install odxtools

Want to contribute or explore the source code? Install from GitHub:

.. code-block:: bash

   git clone https://github.com/mercedes-benz/odxtools
   cd odxtools
   pip install -e .

That's it! You're ready to use odxtools. ✅

---

Basic Usage in Python
---------------------

Here’s a simple way to get started with your own `.pdx` file:

1. **Import the library**

.. code-block:: python

   import odxtools

2. **Load your database**

.. code-block:: python

   db = odxtools.load_pdx_file("my_database.pdx")

3. **Access an ECU and list its services**

.. code-block:: python

   ecu = db.ecus.my_ecu
   print("Available Services:", [s.short_name for s in ecu.services])

4. **Send a request**

.. code-block:: python

   raw_request = ecu.services.session_start()
   print(raw_request)

5. **Decode a response**

.. code-block:: python

   response = ecu.services.session_start.positive_responses[0]
   raw_response = response.encode(can_do_backward_flips="true", coded_request=raw_request)
   print(raw_response.hex())

---

Using odxtools from the Command Line
------------------------------------

If you prefer using the terminal (no coding needed!), odxtools has some built-in tools.

For example:

.. code-block:: bash

   odxtools list my_database.pdx --services

This lists all available services in your `.pdx` file.

Other useful commands:

.. code-block:: bash

   odxtools browse my_database.pdx        # Explore the database interactively
   odxtools decode --help                 # Help for decoding raw hex data
   odxtools compare old.pdx new.pdx       # Compare two files

To see all available commands:

.. code-block:: bash

   odxtools --help

---

Tip for Interactive Python Use
------------------------------

If you're working in the Python terminal (REPL), tab completion helps a lot!  
On Windows, you can install `ptpython` for a better experience:

.. code-block:: bash

   pip install ptpython
   python -m ptpython

---

Next Steps
----------

✅ Load a `.pdx` file  
✅ Explore ECUs and services  
✅ Send & decode diagnostic messages  
✅ Try command-line tools

You're all set to begin exploring what your ECU can do!

For full documentation and code examples, check the [official GitHub repo](https://github.com/mercedes-benz/odxtools).

---

Happy coding
