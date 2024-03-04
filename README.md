<!-- SPDX-License-Identifier: MIT -->
[![PyPi - Version](https://img.shields.io/pypi/v/odxtools)](https://pypi.org/project/odxtools)
[![PyPI - License](https://img.shields.io/pypi/l/odxtools)](LICENSE)
[![CI Status](https://github.com/mercedes-benz/odxtools/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mercedes-benz/odxtools/actions?query=branch%3Amain)

# odxtools

`odxtools` is a set of utilities for working with diagnostic
descriptions of automotive electronic control units using the data
model and the associated technologies of the ODX standard.

[ODX](https://de.wikipedia.org/wiki/ODX) stands for "Open Diagnostic
data eXchange" and is primarily an XML based file format to describe
the diagnostic capabilities of the electronic control units (ECUs) of
complex distributed technical systems (usually cars and trucks). ODX
is an [open standard maintained by ASAM
e.V.](https://www.asam.net/standards/detail/mcd-2-d/) and is also
standardized internationally by
[ISO-22901](https://www.iso.org/standard/41207.html).

Usually, ODX is used to complement the
[UDS](https://en.wikipedia.org/wiki/Unified_Diagnostic_Services)
automotive diagnostics standard -- which itself can be considered to
be an extension of
[OBD-II](https://en.wikipedia.org/wiki/On-board_diagnostics#OBD-II) --
to provide a machine-processable description of the vendor-specific
diagnostics functionality of a vehicle's ECUs. That said, the
functionality which is described by ODX files neither needs to be a
super- nor a subset of OBD-II/UDS, e.g., ODX can be used to describe
diagnostic functionality that uses fundamentally different wire
formats and conventions than the ones mandated by OBD-II/UDS. (In
practice, the ODX-described functionality usually adheres to these
standards, though.)

The functionality provided by `odxtools` encompasses parsing and
internalizing ODX diagnostic database files as well as de- and
encoding the data of diagnostic requests and their responses
send to/received from ECUs in an pythonic manner.

## Table of Contents

- [Use Cases](#use-cases)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
  - [Python snippets](#python-snippets)
- [Using the non-strict mode](#using-the-non-strict-mode)
- [Interactive Usage](#interactive-usage)
  - [Python REPL](#python-repl)
- [Command line usage](#command-line-usage)
  - [Generic parameters](#generic-parameters)
  - [The `list` subcommand](#the-list-subcommand)
  - [The `browse` subcommand](#the-browse-subcommand)
  - [The `snoop` subcommand](#the-snoop-subcommand)
  - [The `find` subcommand](#the-find-subcommand)
  - [The `decode` subcommand](#the-decode-subcommand)
  - [The `compare` subcommand](#the-compare-subcommand)
- [Testing](#testing)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [Provider Information](#provider-information)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Use Cases

Here are some of the intended use cases of `odxtools`:

- Prototype development: Interacting with the diagnostic services of
  electronic control units directly from python (requires taping into
  the car's relevant CAN or ethernet bus)
- End-of-production calibration/quality control: Initial set up and
  running a self diagnosis of newly produced cars to ensure that
  everything works as specified
- After-sales: Implementing servicing functionality for workshops, i.e.,
  defining test schedules based on the legally mandated functionality of
  ISO 15031-6 (OBD II) as well as manufacturer-specific routines
- Prototype development (II): Analyzing and debugging diagnostic sessions
  done using third-party software
- Prototype development (III): Implementing bridges to higher-level protocols
  such as HTTP
- Development for mass production: Accelerating the implementation of
  diagnostic servicesfor low-cost ECUs by using `odxtools`-based code
  generators for the diagnostic glue code on system-level languages like
  C++ or rust

Please be aware that some of the use cases listed above are currently
rather aspirational.

## Installation

The easiest way of installing `odxtools` on your system is via `pip`:

```bash
python3 -m pip install odxtools
```

If you want to develop `odxtools` itself, you need to install it from
source using `git`. The first step is to clone the repository:

```bash
cd $BASE_DIR
git clone https://github.com/mercedes-benz/odxtools
```

After this, make sure that all python dependencies are installed:

```bash
cd $BASE_DIR/odxtools
python3 -m pip install -e .
```

Next, you can optionally build a package and install it on the system:

```bash
cd $BASE_DIR/odxtools
python3 -m pip install --upgrade build
python3 -m build
sudo python3 -m pip install dist/odxtools-*.whl
```

Finally, update the `PYTHONPATH` environment variable and the newly
cloned module is ready to be used:

```bash
export PYTHONPATH="$BASE_DIR/odxtools:$PYTHONPATH"
```

Now, you can check whether the installation worked:

```bash
python3 -m odxtools list -a "$YOUR_PDX_FILE"
```

## Usage Examples

### Python snippets

- Load an ODX database from file `somersault.pdx`:

  ```python
  import odxtools

  db = odxtools.load_pdx_file("somersault.pdx")
  ```

- List the names of all available services of the `somersault_lazy` ECU:

  ```python
  # [...]

  ecu = db.ecus.somersault_lazy
  print(f"Available services for {ecu.short_name}: {ecu.services}")
  ```

- Determine the CAN IDs which the `somersault_lazy` ECU uses to send
  and receive diagnostic messages:

  ```python
  # [...]

  print(f"ECU {ecu.short_name} listens for requests on CAN ID 0x{ecu.get_can_receive_id():x}")
  print(f"ECU {ecu.short_name} transmits responses on CAN ID 0x{ecu.get_can_send_id():x}")
  ```

- Encode a `session_start` request to the `somersault_lazy` ECU:

  ```python
  # [...]

  raw_request_data = ecu.services.session_start()

  print(f"Message for session start request of ECU {ecu.short_name}: {raw_request_data}")
  # -> bytearray(b'\x10\x00')
  ```

- Print all mutable parameters of the `session_start` service's first
  positive response:

  ```python
  # [...]

  ecu.services.session_start.positive_responses[0].print_free_parameters_info()
  ```

- Encode the positive response to the `start_session` request:

  ```python
  # [...]

  raw_request_data = ecu.services.session_start()
  raw_response_data = ecu.services.session_start.positive_responses[0].encode(can_do_backward_flips="true", coded_request=raw_request_data)

  print(f"Positive response to session_start() of ECU {ecu.short_name}: {raw_response_data.hex(' ')}")
  # -> Positive response to session_start() of ECU somersault_lazy: 50 01
  ```

- Decode a request:

  ```python
  # [...]

  raw_data = b"\x10\x00"
  decoded_message = ecu.decode(raw_data)
  for x in decoded_message:
    print(f"decoded as '{x.coding_object.short_name}': {x.param_dict}")
  # -> decoded as 'start_session': {'sid': 16, 'id': 0}
  ```

- Decode a response to a request:

  ```python
  # [...]

  raw_request_data = bytes.fromhex("1000")
  raw_response_data = bytes.fromhex("5001")
  decoded_response = ecu.decode_response(raw_response_data, raw_request_data)
  for x in decoded_response:
    print(f"decoded as '{x.coding_object.short_name}': {x.param_dict}")
  # -> decoded as 'session': {'sid': 80, 'can_do_backward_flips': 'true'}
  ```

## Using the non-strict mode

By default, odxtools raises exceptions if it suspects that it cannot
fulfill a requested operation correctly. For example, if the dataset
it is instructed to load is detected to be not conformant with the ODX
specification, or if completing the operation requires missing
features of odxtools. To be able to deal with such cases, odxtools
provides a "non-strict" mode where such issues are ignored, but where
the results are undefined. The following snippet shows how to instruct
odxtools to load a non-conforming file in non-strict mode, and after
this is done, enables the safety checks again:

  ```python
  import odxtools

  [...]

  odxtools.exceptions.strict_mode = False
  botched_db = odxtools.load_file("my_non-conforming_database.pdx")
  odxtools.exceptions.strict_mode = True

  [...]
  ```

## Interactive Usage

### Python REPL

python's interactive read-reval-print-loop (REPL) supports
tab-completion on most plattforms, i.e., in this case, all data can be
conveniently interactivly discovered and this makes `odxtools` a very
convenient tool to explore the capabilities of a given ECU.

A notable exception is the Microsoft Windows platform: Most python
distribtions for Windows do not enable tab-completion by default in
their REPL.  For more convenience in such a scenario, we recommend
using
[ptpython](https://github.com/prompt-toolkit/ptpython/). `ptpython`
can be installed like any other python package, i.e., via `python3 -m
pip install ptpython`. Then, the REPL ought to be started using

```cmd
c:\odxtest>python3 "C:\Python39\Lib\site-packages\ptpython\entry_points\run_ptpython.py"
```

Alternatively, `pyreadline` can be used after installing it via
`python3 -m pip install pyreadline`.  With this, *basic*
tab-completion for python under Windows in [Interactive
Mode](https://docs.python.org/3/tutorial/interpreter.html#interactive-mode)
should work.

## Command line usage

Based the python module, `odxtools` also provides a set of command
line utilities for quick interactive explorations. Amongst others,
these utilities allow the inspection ODX/PDX files, snooping on
diagnostic sessions, etc. If `odxtools` is installed on a system-wide
basis, these commands can be invoked using `odxtools SUBCOMMAND
[PARAMS]`, if the repository has been manually cloned via `git` and
`odxtools` has not been installed on a system-wide basis, the way to
invoke these utilities is via `python3 -m odxtools SUBCOMMAND
[PARAMS]`.

### Generic parameters

Available generic parameters and a list of subcommands can be obtained
using `odxtools --help`:

```bash
$ odxtools --help
usage: odxtools [-h] [--version] {list,browse,snoop,find,decode,compare} ...

Utilities to interact with automotive diagnostic descriptions based on the ODX standard.

Examples:
  For printing all services use:
   odxtools list ./path/to/database.pdx --services
  For browsing the data base and encoding messages use:
   odxtools browse ./path/to/database.pdx

positional arguments:
  {list,browse,snoop,find,decode,compare}
                        Select a sub command
    list                Print a summary of automotive diagnostic files.
    browse              Interactively browse the content of automotive diagnostic files.
    snoop               Live decoding of a diagnostic session.
    find                Find & display services by their name
    decode              Find & print service by hex-data. Can also decode the hex-data to its named parameters.
    compare             Compares two ecu versions or databases with each other. Checks whether diagnostic services and its parameters have changed.

optional arguments:
  -h, --help            show this help message and exit
  --version             Print the odxtools version
```

All subcommands accept the `--help` parameter:

```bash
$ odxtools list --help
usage: odxtools list [-h] [-v VARIANT [VARIANT ...]] [-s [SERVICE [SERVICE ...]]] [-p] [-d] [-a] PDX_FILE
[...]
```

It follows is an inexhaustive list of the subcommands that are
currently available:

### The `list` subcommand

The `list` subcommand is used to parse a `.pdx` database file and
print the relevant parts of its content to the terminal.

```bash
$ odxtools list -h
usage: odxtools list [-h] [-v VARIANT [VARIANT ...]] [-g] [-s [SERVICE [SERVICE ...]]] [-p] [-d] [-a] [-po] PDX_FILE

List the content of automotive diagnostic files (*.pdx)

Examples:
  For displaying only the names of the diagnostic layers use:
    odxtools list ./path/to/database.pdx
  For displaying all content use:
    odxtools list ./path/to/database.pdx --all
  For more information use:
    odxtools list -h

positional arguments:
  PDX_FILE              path to the .pdx file

optional arguments:
  -h, --help            show this help message and exit
  -v VARIANT [VARIANT ...], --variants VARIANT [VARIANT ...]
                        Specifies which variants should be included.
  -g, --global-negative-responses
                        Print a list of the global negative responses for the selected ECUs.
  -s [SERVICE [SERVICE ...]], --services [SERVICE [SERVICE ...]]
                        Print a list of diagnostic services specified in the pdx.
                        If no service names are specified, all services are printed.
  -p, --params          Print a list of all parameters relevant for the selected items.
  -d, --dops            Print a list of all data object properties relevant for the selected items
  -a, --all             Print a list of all diagnostic services and DOPs specified in the pdx
  -po, --plumbing-output
                        Print full objects instead of selected and formatted attributes
```

The options `--variants` and `--services` can be used to specify which services should be printed.  
If the `--params` option is specified, the message layout and information about the service parameters (reuest as well as responses) are printed for all specified variants/services.
If the `--global-negative-responses` option is specified, all global negative responses are printed for all specified variants.
If the `--dops` option is specified, a list of all data object properties (their names) is printed for all specified variants/services.
With the parameter `--all` all data of the file that is recognized by `odxtools` is printed.
The default output does not display all information of the specified objects but a selection. To see all object information choose the parameter `--plumbing-output`.

Example:

```bash
$ odxtools list $BASE_DIR/odxtools/examples/somersault.pdx --variants somersault_lazy --services do_forward_flips --params
Overview of diagnostic layers:
    | Name            | Variant Type | Num. of Services | Num. of DOPs | Num. of comparams
----+-----------------+--------------+------------------+--------------+-------------------
  0 | somersault_lazy | ECU-VARIANT  |                5 |           10 |                10

Diagnostic layer: 'somersault_lazy'
 Variant Type: ECU-VARIANT
 Description: Sloppy variant of the somersault ECU (lazy < assiduous)

The services of 'somersault_lazy' are:
 do_forward_flips <ID: OdxLinkId('somersault.service.do_forward_flips')>
  Service description: Do a forward flip.

  Request Properties:
   Request Name: do_forward_flips
   Byte-Array: ---      Hex-String: 0x---
   Service Parameters: [sid, forward_soberness_check, num_flips]

    | Name                    | Byte Pos. | Bit Length | Param. Type | Data Type | Value | Value Desc. | Linked DOP
----+-------------------------+-----------+------------+-------------+-----------+-------+-------------+-----------------
  0 | sid                     |         0 |          8 | CODED-CONST | A_UINT32  | 0xBA  | coded value |
  1 | forward_soberness_check |         1 |          8 | VALUE       | A_UINT32  |       |             | soberness_check
  2 | num_flips               |         2 |          8 | VALUE       | A_UINT32  |       |             | num_flips

  Message format of a request:
           7     6     5     4     3     2     1     0
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid(8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | forward_soberness_check(8 bits)               |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      2 | num_flips(8 bits)                             |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   
  Positive Response Properties:
   Number of Positive Responses: 1
   Positive Responses: [grudging_forward]
   Service Parameters: [sid, num_flips_done]

    | Name           | Byte Pos. | Bit Length | Parameter Type         | Data Type | Value | Value Desc. | Linked DOP
----+----------------+-----------+------------+------------------------+-----------+-------+-------------+-------------
  0 | sid            |         0 |          8 | CODED-CONST            | A_UINT32  | 0xFA  | coded value |
  1 | num_flips_done |         1 |          8 | MATCHING-REQUEST-PARAM |           |       |             |

  Message format of a positive response:
           7     6     5     4     3     2     1     0
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid(8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | num_flips_done(8 bits)                        |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   
  Negative Response Properties:
   Number of Negative Responses: 1
   Negative Responses: [flips_not_done]
   Service Parameters: [sid, rq_sid, reason, flips_successfully_done]

    | Name                    |Byte Pos. | Bit Length | Parameter Type         | Data Type | Value     | Value Desc. | Linked DOP
----+-------------------------+----------+------------+------------------------+-----------+-----------+-------------+-------------
  0 | sid                     |        0 |          8 | CODED-CONST            | A_UINT32  | 0x7F      | coded value |
  1 | rq_sid                  |        1 |          8 | MATCHING-REQUEST-PARAM |           |           |             |
  2 | reason                  |        2 |          8 | NRC-CONST              | A_UINT32  | [0, 1, 2] | coded value |
  3 | flips_successfully_done |        3 |          8 | VALUE                  | A_UINT32  |           |             | num_flips

  Number of negative responses: 1
  Message format of a negative response:
           7     6     5     4     3     2     1     0
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid(8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | rq_sid(8 bits)                                |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      2 | reason(8 bits)                                |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      3 | flips_successfully_done(8 bits)               |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   
```

### The `browse` subcommand

The `browse` subcommand uses
[InquirerPy](https://github.com/kazhala/InquirerPy) to interactively
navigate through the database of a `.pdx` file. For example, using the
`browse` subcommand you can select the ECU and service without
spamming the terminal:

```bash
$ odxtools browse $BASE_DIR/odxtools/examples/somersault.pdx
? Select a Variant.  somersault_lazy
ECU-VARIANT 'somersault_lazy' (Receive ID: 0x7b, Send ID: 0x1c8)
? The variant somersault_lazy offers the following services. Select one!  do_forward_flips
? This service offers the following messages.  Request: do_forward_flips
             7     6     5     4     3     2     1     0
          +-----+-----+-----+-----+-----+-----+-----+-----+
        0 | sid(8 bits)                                   |
          +-----+-----+-----+-----+-----+-----+-----+-----+
        1 | forward_soberness_check(8 bits)               |
          +-----+-----+-----+-----+-----+-----+-----+-----+
        2 | num_flips(8 bits)                             |
          +-----+-----+-----+-----+-----+-----+-----+-----+
     Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0xba')
     Parameter(short_name='forward_soberness_check', type='VALUE', semantic=None, byte_position=1, bit_length=8, dop_ref='somersault.DOP.soberness_check')
      DataObjectProperty('soberness_check', category='LINEAR', internal_type='A_UINT32', physical_type='A_UINT32')
     Parameter(short_name='num_flips', type='VALUE', semantic=None, byte_position=2, bit_length=8, dop_ref='somersault.DOP.num_flips')
      DataObjectProperty('num_flips', category='LINEAR', internal_type='A_UINT32', physical_type='A_UINT32')
[...]
```

### The `snoop` subcommand

The `snoop` subcommand can be used to decode a trace of a or a
currently running diagnostic session.

```bash
$ odxtools snoop -h
usage: odxtools snoop [-h] [--active] [--channel CHANNEL] [--rx RX] [--tx TX] [--variant VARIANT]
                      [--protocol PROTOCOL]
                      PDX_FILE

Live decoding of a diagnostic session.

positional arguments:
  PDX_FILE              path to the .pdx file

options:
  -h, --help            show this help message and exit
  --active, -a          Active mode, sends flow control messages to receive ISO-TP telegrams successfully
  --channel CHANNEL, -c CHANNEL
                        CAN interface name to be used (required in active mode)
  --rx RX, -r RX        CAN ID in which the ECU listens for diagnostic messages
  --tx TX, -t TX        CAN ID in which the ECU sends replys to diagnostic messages  (required in active mode)
  --variant VARIANT, -v VARIANT
                        Name of the ECU variant which the decode process ought to be based on
  --protocol PROTOCOL, -p PROTOCOL
                        Name of the protocol used for decoding
```
Example:
```bash
# create a socketcan `vcan0` interface
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up

# start the snooping on vcan0
odxtools snoop -c vcan0 --variant "somersault_lazy" $BASE_DIR/odxtools/examples/somersault.pdx

# on a different terminal, run the diagnostic session
$BASE_DIR/odxtools/examples/somersaultlazy.py -c vcan0
```

The snoop command will then output the following:

```bash
$ odxtools snoop -c vcan0 --variant "somersault_lazy" $BASE_DIR/odxtools/examples/somersault.pdx
Decoding messages on channel vcan0
Tester: do_forward_flips(forward_soberness_check=18, num_flips=1)
 -> 7fba7f (bytearray(b'\x7f\xba\x7f'), 3 bytes)
Tester: start_session()
 -> session()
Tester: do_forward_flips(forward_soberness_check=18, num_flips=1)
 -> grudging_forward(num_flips_done=bytearray(b'\x01'))
Tester: do_forward_flips(forward_soberness_check=35, num_flips=1)
 -> flips_not_done(rq_sid=bytearray(b'\xba'), reason=0, flips_successfully_done=0)
Tester: do_forward_flips(forward_soberness_check=18, num_flips=3)
 -> grudging_forward(num_flips_done=bytearray(b'\x03'))
Tester: do_forward_flips(forward_soberness_check=18, num_flips=50)
 -> flips_not_done(rq_sid=bytearray(b'\xba'), reason=1, flips_successfully_done=6)
```

### The `find` subcommand

The `find` subcommand can be used to find a service and its associated information by a partial name via cli.

```bash
$ odxtools find -h
usage: odxtools find [-h] [-v VARIANT] -s [SERVICES ...] [-nd] [-ro] [-po] PDX_FILE

Find & print services by name

Examples:
  For displaying the services associated with the partial name 'Reset' without details:
    odxtools find ./path/to/database.pdx -s "Reset" --no-details
  For more information use:
    odxtools find -h

positional arguments:
  PDX_FILE              Location of the .pdx file

options:
  -h, --help            show this help message and exit
  -v VARIANT, --variants VARIANT
                        Specifies which ecu variants should be included.
  -s [SERVICES ...], --service-names [SERVICES ...]
                        Print a list of diagnostic services partially matching given service names
  -nd, --no-details     Don't show all service details
  -ro, --relaxed-output
                        Relax output formatting rules (allow unknown bitlengths for ascii representation)
  -po, --plumbing-output
                        Print full objects instead of selected and formatted attributes
```

Example: Find diagnostic services with the name `session_start`

```bash
$ odxtools find $BASE_DIR/odxtools/examples/somersault.pdx -s session_start

=====================================
somersault_lazy, somersault_assiduous
=====================================


 session_start <ID: OdxLinkId('somersault.service.session_start')>

  Request Properties:
   Request Name: start_session
   Byte-Array: bytearray(b'\x10\x00')   Hex-String: 0x1000
   Service Parameters: [sid, id]

    | Name | Byte Pos. | Bit Length | Param. Type | Data Type | Value | Value Desc. | Linked DOP
----+------+-----------+------------+-------------+-----------+-------+-------------+------------
  0 | sid  |         0 |          8 | CODED-CONST | A_UINT32  | 0x10  | coded value |
  1 | id   |         1 |          8 | CODED-CONST | A_UINT32  | 0x00  | coded value |

  Message format of a request:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | id (8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+

  Positive Response Properties:
   Number of Positive Responses: 1
   Positive Responses: [session]
   Service Parameters: [sid, can_do_backward_flips]

    | Name                  | Byte Pos. | Bit Length | Param. Type | Data Type        | Value | Value Desc. | Linked DOP
----+-----------------------+-----------+------------+-------------+------------------+-------+-------------+------------
  0 | sid                   |         0 |          8 | CODED-CONST | A_UINT32         | 0x50  | coded value |
  1 | can_do_backward_flips |         1 |          8 | VALUE       | A_UNICODE2STRING |       |             | boolean

  Message format of a positive response:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | can_do_backward_flips (8 bits)                |
        +-----+-----+-----+-----+-----+-----+-----+-----+

  Negative Response Properties:
   Number of Negative Responses: 1
   Negative Responses: [general_negative_response]
   Service Parameters: [sid, rq_sid, response_code]

    | Name          | Byte Pos.| Bit Length | Parameter Type         | Data Type | Value | Value Desc. | Linked DOP
----+---------------+----------+------------+------------------------+-----------+-------+-------------+------------
  0 | sid           |        0 |          8 | CODED-CONST            | A_UINT32  | 0x7F  | coded value |
  1 | rq_sid        |        1 |          8 | MATCHING-REQUEST-PARAM |           |       |             |
  2 | response_code |        2 |          8 | VALUE                  | A_UINT32  |       |             | error_code

  Message format of a negative response:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | rq_sid (8 bits)                               |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      2 | response_code (8 bits)                        |
        +-----+-----+-----+-----+-----+-----+-----+-----+

```

### The `decode` subcommand

The `decode` subcommand can be used to decode hex-data to a service, and its associated
parameters.

```bash
$ odxtools decode -h
usage: odxtools decode [-h] [-v VARIANT] -d DATA [-D] PDX_FILE

Decode request by hex-data

Examples:
  For displaying the service associated with the request 10 01 & decoding it:
    odxtools decode ./path/to/database.pdx -D -d '10 01'
  For displaying the service associated with the request 10 01, without decoding it:
    odxtools decode ./path/to/database.pdx -d '10 01'
  For more information use:
    odxtools decode -h

positional arguments:
  PDX_FILE              Location of the .pdx file

options:
  -h, --help            show this help message and exit
  -v VARIANT, --variants VARIANT
                        Specifies which ecu variants should be included.
  -d DATA, --data DATA  Specify data of hex request
  -D, --decode          Decode the given hex data
```

Example: Decode diagnostic services with the request `10 00`

```bash
$ odxtools decode $BASE_DIR/odxtools/examples/somersault.pdx -d '10 00'
Binary data: 10 00
Decoded by service 'session_start' (decoding ECUs: somersault_lazy, somersault_assiduous)
```

Example: Decode diagnostic services with the request `10 00`, and parameters

```bash
$ odxtools decode $BASE_DIR/odxtools/examples/somersault.pdx -d '10 00' -D
Binary data: 10 00
Decoded by service 'session_start' (decoding ECUs: somersault_lazy, somersault_assiduous)
Decoded data:
  sid=16 (0x10)
  id=0 (0x0)
```

### The `compare` subcommand

The `compare` subcommand can be used to compare databases (pdx-files) and diagnostic layers with each other. All diagnostic services as well as its parameters of specified databases and variants are compared with each other and changes are displayed.

#### database comparison:
- new diagnostic layers
- deleted diagnostic layers
- diagnostic layer comparison

#### diagnostic layer comparison:
- new services
- deleted services
- renamed services
- service parameter comparison

#### service parameter comparison:
find changes in following properties:
- Name
- Byte Position
- Bit Length
- Semantic
- Parameter Type
- Coded Value
- Data Type
- Data Object Property (Name, Data Type, Bit Length, Default Value)

```bash
$ odxtools compare -h
usage: odxtools compare [-h] [-v VARIANT [VARIANT ...]] [-db DATABASE [DATABASE ...]] [-nd] [-od] PDX_FILE

Compares two ecu versions or databases with each other. Checks whether diagnostic services and its parameters have changed.

Examples:
  Comparison of two ecu versions:
    odxtools compare ./path/to/database.pdx -v variant1 variant2
  Comparison of two database versions:
    odxtools compare ./path/to/database.pdx -db ./path/to/old-database.pdx
  For more information use:
    odxtools compare -h

positional arguments:
  PDX_FILE              Location of the .pdx file

options:
  -h, --help            show this help message and exit
  -v VARIANT [VARIANT ...], --variants VARIANT [VARIANT ...]
                        Compare specified ecu variants to each other.
  -db DATABASE [DATABASE ...], --database DATABASE [DATABASE ...]
                        Compare specified database file(s) to database file of first input argument.
  -nd, --no-details     Don't show all service parameter details
  -od, --object-details
                        Print all object details instead of just the name
```

Example: Compare the ecu variants `somersault_lazy` and `somersault_assiduous`

```bash
$ odxtools compare $BASE_DIR/odxtools/examples/somersault.pdx -v somersault_lazy somersault_assiduous

Overview of diagnostic layers:
    | Name                 | Variant Type | Num. of Services | Num. of DOPs | Num. of comparams
----+----------------------+--------------+------------------+--------------+-------------------
  0 | somersault_lazy      | ECU-VARIANT  |                5 |           10 |                10
  1 | somersault_assiduous | ECU-VARIANT  |                8 |           10 |                10


Changes in ecu variant somersault_lazy
 (compared to somersault_assiduous)

 Changed diagnostic services for ecu variant: somersault_lazy

 Deleted services
    | Name                 | Semantic   | Hex-Request
----+----------------------+------------+---------------
  0 | set_operation_params | FUNCTION   |
  1 | do_backward_flips    | FUNCTION   |
  2 | headstand            | UNKNOWN    |
```

Example: Compare two databases

```bash
$ odxtools compare $BASE_DIR/odxtools/examples/somersault_modified.pdx -db $BASE_DIR/odxtools/examples/somersault.pdx -nd

Changes in file somersault_modified.pdx
 (compared to somersault.pdx)

Overview of diagnostic layers (for somersault_modified.pdx)
    | Name                 | Variant Type | Num. of Services | Num. of DOPs | Num. of comparams
----+----------------------+--------------+------------------+--------------+-------------------
  0 | somersault           | BASE-VARIANT |                6 |           10 |                10
  1 | somersault_lazy      | ECU-VARIANT  |                5 |           10 |                10
  2 | somersault_assiduous | ECU-VARIANT  |                8 |           10 |                10
  3 | somersault_young     | ECU-VARIANT  |                6 |           10 |                10


Overview of diagnostic layers (for somersault.pdx)
    | Name                 | Variant Type | Num. of Services | Num. of DOPs | Num. of comparams
----+----------------------+--------------+------------------+--------------+-------------------
  0 | somersault           | BASE-VARIANT |                7 |           10 |                10
  1 | somersault_lazy      | ECU-VARIANT  |                5 |           10 |                10
  2 | somersault_assiduous | ECU-VARIANT  |                8 |           10 |                10

 Changed ecu variants:
         New ecu variants:
                         somersault_young
         Deleted ecu variants:

 Changed diagnostic services for ecu variant: somersault_lazy

 Renamed services
    | Name          | Semantic   | Hex-Request   | Old service name
----+---------------+------------+---------------+--------------------
  0 | session_start | SESSION    | 0x1000        | start_session

 Services with parameter changes
    | Name           | Semantic      | Hex-Request | Changed parameters
----+----------------+---------------+-------------+-----------------------------------------------------------------------------------------------
  0 | session_start  | SESSION       | 0x1000      | positive response parameter 'can_do_backward_flips',
  1 | session_stop   | SESSION       | 0x1001      | request parameter 'id', positive response parameter 'can_do_backward_flips',
  2 | tester_present | TESTERPRESENT | 0x3E00      | request parameter 'id', positive response parameter 'status',
  3 | report_status  | CURRENTDATA   | 0x2200      | positive response parameter 'dizzyness_level', positive response parameter 'happiness_level',

 Detailed changes of diagnostic service session_start

Properties of 2. positive response parameter can_do_backward_flips have changed
    | Property      | Old Value   | New Value
----+---------------+-------------+------------------
  0 | Linked DOP    | uint8       | boolean
  1 | DOP data type | A_UINT32    | A_UNICODE2STRING

 Detailed changes of diagnostic service session_stop

Properties of 2. request parameter id have changed
    | Property   |   Old Value |   New Value
----+------------+-------------+-------------
  0 | Bit Length |          16 |           8

Properties of 2. positive response parameter can_do_backward_flips have changed
    | Property      | Old Value   | New Value
----+---------------+-------------+------------------
  0 | Linked DOP    | uint8       | boolean
  1 | DOP data type | A_UINT32    | A_UNICODE2STRING

 Detailed changes of diagnostic service tester_present

Properties of 2. request parameter id have changed
    | Property   | Old Value   | New Value
----+------------+-------------+-------------
  0 | Value      | 0x01        | 0x00

Properties of 2. positive response parameter status have changed
    | Property   | Old Value   | New Value
----+------------+-------------+-------------
  0 | Bit Length | 16          | 8
  1 | Value      | 0x0043      | 0x00

 Detailed changes of diagnostic service report_status

Properties of 2. positive response parameter dizzyness_level have changed
    | Property       | Old Value       | New Value
----+----------------+-----------------+-----------------
  0 | Parameter name | happiness_level | dizzyness_level
  1 | Linked DOP     | happiness_level | dizzyness_level

Properties of 3. positive response parameter happiness_level have changed
    | Property       | Old Value       | New Value
----+----------------+-----------------+-----------------
  0 | Parameter name | dizzyness_level | happiness_level
  1 | Linked DOP     | dizzyness_level | happiness_level

 Changed diagnostic services for ecu variant: somersault_assiduous

 New services
    | Name     | Semantic   | Hex-Request
----+----------+------------+---------------
  0 | flicflac | FUNCTION   |

 Deleted services
    | Name                 | Semantic   | Hex-Request
----+----------------------+------------+---------------
  0 | set_operation_params | FUNCTION   |

 Renamed services
    | Name          | Semantic   | Hex-Request   | Old service name
----+---------------+------------+---------------+--------------------
  0 | session_start | SESSION    | 0x1000        | start_session

 Services with parameter changes
    | Name              | Semantic      | Hex-Request | Changed parameters
----+-------------------+---------------+-------------+---------------------------------------------------------------------------------------------------------------------------------------------
  0 | session_start     | SESSION       | 0x1000      | positive response parameter 'can_do_backward_flips',
  1 | session_stop      | SESSION       | 0x1001      | request parameter 'id', positive response parameter 'can_do_backward_flips',
  2 | tester_present    | TESTERPRESENT | 0x3E00      | request parameter 'id', positive response parameter 'status',
  3 | do_backward_flips | FUNCTION      |             | request parameter 'backward_soberness_check', positive response parameter 'num_flips_done', positive response parameter 'grumpiness_level',
  4 | report_status     | CURRENTDATA   | 0x2200      | positive response parameter 'dizzyness_level', positive response parameter 'happiness_level',
  5 | headstand         | UNKNOWN       |             | request parameter list,

 Detailed changes of diagnostic service session_start

Properties of 2. positive response parameter can_do_backward_flips have changed
    | Property      | Old Value   | New Value
----+---------------+-------------+------------------
  0 | Linked DOP    | uint8       | boolean
  1 | DOP data type | A_UINT32    | A_UNICODE2STRING

 Detailed changes of diagnostic service session_stop

Properties of 2. request parameter id have changed
    | Property   |   Old Value |   New Value
----+------------+-------------+-------------
  0 | Bit Length |          16 |           8

Properties of 2. positive response parameter can_do_backward_flips have changed
    | Property      | Old Value   | New Value
----+---------------+-------------+------------------
  0 | Linked DOP    | uint8       | boolean
  1 | DOP data type | A_UINT32    | A_UNICODE2STRING

 Detailed changes of diagnostic service tester_present

Properties of 2. request parameter id have changed
    | Property   | Old Value   | New Value
----+------------+-------------+-------------
  0 | Value      | 0x01        | 0x00

Properties of 2. positive response parameter status have changed
    | Property   | Old Value   | New Value
----+------------+-------------+-------------
  0 | Bit Length | 16          | 8
  1 | Value      | 0x0043      | 0x00

 Detailed changes of diagnostic service do_backward_flips

Properties of 2. request parameter backward_soberness_check have changed
    | Property       | Old Value      | New Value
----+----------------+----------------+--------------------------
  0 | Parameter name | backward_check | backward_soberness_check

Properties of 2. positive response parameter num_flips_done have changed
    | Property      |   Old Value | New Value
----+---------------+-------------+-------------
  0 | Byte position |           1 |

Properties of 3. positive response parameter grumpiness_level have changed
    | Property       | Old Value   | New Value
----+----------------+-------------+-------------
  0 | Byte position  | 2           |
  1 | Parameter type | CODED-CONST | VALUE

 Detailed changes of diagnostic service report_status

Properties of 2. positive response parameter dizzyness_level have changed
    | Property       | Old Value       | New Value
----+----------------+-----------------+-----------------
  0 | Parameter name | happiness_level | dizzyness_level
  1 | Linked DOP     | happiness_level | dizzyness_level

Properties of 3. positive response parameter happiness_level have changed
    | Property       | Old Value       | New Value
----+----------------+-----------------+-----------------
  0 | Parameter name | dizzyness_level | happiness_level
  1 | Linked DOP     | dizzyness_level | happiness_level

 Detailed changes of diagnostic service headstand

List of request parameters for service headstand is not identical.
    | List     | Values
----+----------+---------------------
  0 | Old list | [sid, id, duration]
  1 | New list | [sid, duration]
```

## Testing

The included unit tests can be run via

```bash
python -m unittest tests/test_*.py
```

The static type checker can be run via
```bash
python3 -m mypy --ignore-missing-imports odxtools
```

## Contributing

We welcome any contributions.  If you want to contribute to this
project, please read the [contributing guide](https://github.com/mercedes-benz/odxtools/blob/main/CONTRIBUTING.md).

## Code of Conduct

Please read our [Code of Conduct](https://github.com/mercedes-benz/foss/blob/master/CODE_OF_CONDUCT.md)
as it is our base for interaction.

## Provider Information

Please visit <https://mbition.io/en/home/index.html> for information on the provider.

Notice: Before you use the program in productive use, please take all necessary precautions,
e.g. testing and verifying the program with regard to your specific use.
The program was tested solely for our own use cases, which might differ from yours.

## Acknowledgements

This work includes research of the project
[SofDCar](https://sofdcar.de/) (19S21002), which is funded by the
[German Federal Ministry for Economic Affairs and
Climate Action](https://www.bmwk.de/).

## License

This project is licensed under the [MIT LICENSE](LICENSE).
