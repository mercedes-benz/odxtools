# SPDX-License-Identifier: MIT
"""odxtools is a set of utilities to deal with automotive diagnostic
descriptions of electronic control units using ODX-formatted
description files.

ODX stands for "Open Diagnostic Data Exchange" `[ODX]`_ and is an XML
based file format to describe the diagnostic capabilities of the
various electronic control units (ECUs) of complex distributed
technical systems (mainly cars and trucks). ODX is an open standard,
maintained by ASAM e.V. `[ASAM]`_ and standardized internationally by
ISO 22901 `[ISO22901]`_.

The services provided by odxtools encompass parsing and internalizing
ODX diagnostic database files as well as decoding and endcoding raw
data of diagnostic requests and responses that are send to/received
from ECUs in an pythonic manner.

Examples:
=========

- Load a database from file ``my_diag_db.pdx``:

.. code-block:: python

    import odxtools

    db = odxtools.load_file("my_diag_db.pdx")

- List the names of all available services of the first ECU:

.. code-block:: python

    # [...]

    dl = db.diag_layer_containers[0].diag_layers[0]
    print(f"Available services for {dl.short_name}: {[s.short_name for s in dl.services]}")

- Determine the CAN IDs which the first described ECU uses to send and receive diagnostic messages:

.. code-block:: python

    # [...]

    print(f"ECU listens on ID 0x{dl.get_receive_id():x}")
    print(f"ECU transmits on ID 0x{dl.get_send_id():x}")

- Decode a diagnostic message for an ECU:

.. code-block:: python

    # [...]

    raw_data = b"\xB0\xA7"
    decoded_message = dl.decode(raw_data)
    print(f"decoded message: {decoded_message}")

References
==========

- _`[ASAM]` ASAM e.V: https://www.asam.net/
- _`[ODX]` The ODX Specification: https://www.asam.net/standards/detail/mcd-2-d/
- _`[ISO22901]` The ISO 22901 Standard: https://www.iso.org/standard/41207.html

"""
from .loadfile import load_directory as load_directory  # noqa: F401
from .loadfile import load_file as load_file  # noqa: F401
from .loadfile import load_files  # noqa: F401
from .loadfile import load_odx_d_file as load_odx_d_file  # noqa: F401
from .loadfile import load_pdx_file as load_pdx_file  # noqa: F401
from .loadfile import load_xml_file as load_xml_file  # noqa: F401
from .version import __version__ as __version__  # noqa: F401
from .writepdxfile import write_pdx_file as write_pdx_file  # noqa: F401

__author__ = "Katrin Bauer"


def _main() -> None:
    # Command line tool
    from .cli import main as _main

    _main.start_cli()
