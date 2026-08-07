Getting started
===============

This tutorial-style guide walks through installing ``odxtools``, loading a
diagnostic database, and performing common encode/decode tasks. For a broader
overview of use cases, see the project ``README.md``.

What is odxtools?
-----------------

``odxtools`` is a Python toolkit for working with automotive diagnostic
descriptions based on the `ODX <https://www.asam.net/standards/detail/mcd-2-d/>`_
(Open Diagnostic data eXchange) standard. ODX is typically used together with
UDS to describe ECU diagnostic services in a machine-readable way.

With ``odxtools`` you can:

* parse ODX / PDX diagnostic databases
* explore ECUs, services, and parameters from Python
* encode requests and decode responses
* use command-line helpers for listing, browsing, finding, decoding, and comparing databases

Installation
------------

From PyPI::

   python3 -m pip install odxtools

For development from a git checkout::

   git clone https://github.com/mercedes-benz/odxtools.git
   cd odxtools
   python3 -m pip install -e .

Optional extras (examples, browse UI, tests)::

   python3 -m pip install -e ".[all]"

Verify the installation::

   python3 -m odxtools --version

Load a diagnostic database
--------------------------

The repository ships a small sample database at ``examples/somersault.pdx``.
From the repository root::

   import odxtools

   db = odxtools.load_pdx_file("examples/somersault.pdx")

You can also load a single ODX file or a directory of ODX files::

   db = odxtools.load_file("path/to/description.odx")
   db = odxtools.load_directory("path/to/odx/dir")

Explore ECUs and services
-------------------------

ECU variants are available through ``db.ecus`` (alias of ``db.ecu_variants``)::

   ecu = db.ecus.somersault_lazy
   print(f"Available services for {ecu.short_name}: {ecu.services}")

Inspect communication identifiers used by the ECU::

   print(f"ECU {ecu.short_name} listens on CAN ID 0x{ecu.get_can_receive_id():x}")
   print(f"ECU {ecu.short_name} transmits on CAN ID 0x{ecu.get_can_send_id():x}")

Encode and decode messages
--------------------------

Encode a ``session_start`` request::

   raw_request_data = ecu.services.session_start()
   print(f"Request: {raw_request_data}")
   # -> bytearray(b'\x10\x00')

Inspect mutable parameters of the first positive response::

   ecu.services.session_start.positive_responses[0].print_free_parameters_info()

Encode a positive response::

   raw_response_data = ecu.services.session_start.positive_responses[0].encode(
       can_do_backward_flips="true",
       coded_request=raw_request_data,
   )
   print(raw_response_data.hex(" "))
   # -> 50 01

Decode a request payload::

   decoded_message = ecu.decode(b"\x10\x00")
   for x in decoded_message:
       print(f"decoded as '{x.coding_object.short_name}': {x.param_dict}")

Decode a response in the context of a request::

   decoded_response = ecu.decode_response(
       bytes.fromhex("5001"),
       bytes.fromhex("1000"),
   )
   for x in decoded_response:
       print(f"decoded as '{x.coding_object.short_name}': {x.param_dict}")

Non-strict mode
---------------

By default, ``odxtools`` raises exceptions when a dataset appears non-conformant
or a requested operation cannot be completed safely. For exploratory work on
imperfect files you can temporarily disable strict checks::

   import odxtools

   odxtools.exceptions.strict_mode = False
   db = odxtools.load_file("my_non-conforming_database.pdx")
   odxtools.exceptions.strict_mode = True

Results in non-strict mode are undefined; re-enable strict mode as soon as
possible.

Command-line usage
------------------

If ``odxtools`` is installed, invoke subcommands with ``odxtools``. From a
source checkout without a system-wide install, use ``python3 -m odxtools``.

List services in a PDX file::

   python3 -m odxtools list examples/somersault.pdx --services

Browse interactively (requires the ``browse-tool`` extra)::

   python3 -m odxtools browse examples/somersault.pdx

Other useful subcommands:

* ``find`` — locate services by name
* ``decode`` — map hex payloads to named parameters
* ``compare`` — compare diagnostic layers or databases
* ``snoop`` — live decoding of a diagnostic session

See all options::

   python3 -m odxtools --help
   python3 -m odxtools list --help

Interactive Python tip
----------------------

Tab completion makes exploring a loaded database much easier. On Windows, many
Python distributions do not enable tab completion in the default REPL; consider
`ptpython <https://github.com/prompt-toolkit/ptpython/>`_::

   python3 -m pip install ptpython
   python3 -m ptpython

Next steps
----------

* Read the :doc:`api_reference` for ``Database`` and the public package API
* Browse ``examples/`` in the repository for runnable samples
* Open an issue on GitHub if you find gaps in the docs or behaviour
* Follow ``CONTRIBUTING.md`` (DCO sign-off required) before submitting a pull request
