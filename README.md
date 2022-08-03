<!-- SPDX-License-Identifier: MIT -->
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
- [Interactive Usage](#interactive-usage)
  - [Python REPL](#python-repl)
- [Command line usage](#command-line-usage)
  - [Generic parameters](#generic-parameters)
  - [The `list` subcommand](#the-list-subcommand)
  - [The `browse` subcommand](#the-browse-subcommand)
  - [The `snoop` subcommand](#the-snoop-subcommand)
  - [The `find` subcommand](#the-find-subcommand)
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
pip3 install odxtools
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
pip3 install -r requirements.txt
```

Next, build the project and install it on the system:

```bash
cd $BASE_DIR/odxtools
python3 ./setup.py build
sudo python3 ./setup.py install # <- optional
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

  db = odxtools.load_pdx_file("somersault.pdx", enable_candela_workarounds=False)
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

  print(f"ECU {ecu.short_name} listens for requests on CAN ID 0x{ecu.get_receive_id():x}")
  print(f"ECU {ecu.short_name} transmits responses on CAN ID 0x{ecu.get_send_id():x}")
  ```

- Encode a `session_start` request to the `somersault_lazy` ECU:

  ```python
  # [...]

  raw_request_data = ecu.services.session_start()

  print(f"Message for session start request of ECU {ecu.short_name}: {raw_request_data}")
  # -> bytearray(b'\x10\x00')
  ```

- Encode the positive response to the `start_session` request:

  ```python
  # [...]

  raw_request_data = ecu.services.session_start()
  raw_response_data = ecu.services.session_start.positive_responses[0].encode(coded_request=raw_request_data)

  print(f"Positive response to session_start() of ECU {ecu.short_name}: {raw_response_data}")
  # -> bytearray(b'P')
  ```

- Decode a request:

  ```python
  # [...]

  raw_data = b"\x10\x00"
  decoded_message = ecu.decode(raw_data)
  print(f"decoded message: {decoded_message}")
  # -> decoded message: [start_session()]
  ```

- Decode a response to a request:

  ```python
  # [...]

  raw_request_data = b"\x10\x00"
  raw_response_data = b'P'
  decoded_response = ecu.decode_response(raw_response_data, raw_request_data)
  print(f"decoded response: {decoded_response}")
  # -> decoded response: [session()]
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
can be installed like any other python package, i.e., via `pip3
install ptpython`. Then, the REPL ought to be started using

```cmd
c:\odxtest>python3 "C:\Python39\Lib\site-packages\ptpython\entry_points\run_ptpython.py"
```

Alternatively, `pyreadline` can be used after installing it via `pip3
install wheel pyreadline`.  With this, *basic* tab-completion for
python under Windows in [Interactive
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
usage: odxtools [-h] [-c] {list,browse,snoop,find,encode-message,decode-message} ...

Utilities to interact with automotive diagnostic descriptions based on the ODX standard.

Examples:
  For printing all services use:
   odxtools list ./path/to/database.pdx --services
  For browsing the data base and encoding messages use:
   odxtools browse ./path/to/database.pdx

positional arguments:
  {list,browse,snoop,find,encode-message,decode-message}
                        Select a sub command
    list                Print a summary of automotive diagnostic files.
    browse              Interactively browse the content of automotive diagnostic files.
    snoop               Live decoding of a diagnostic session.
    find                Find & display services by hex-data, or name, can also decodes requests.
    encode-message      Encode a message. Interactively asks for parameter values.
                        This is a short cut through the browse command to directly encode a message.
    decode-message      Decode a message. Interactively asks for parameter values.
                        This is a short cut through the browse command to directly encode a message.

optional arguments:
  -h, --help            show this help message and exit
  -c, --conformant      The input file fully confirms to the standard, i.e., disable work-arounds for bugs of the CANdela tool
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
usage: odxtools list [-h] [-v VARIANT [VARIANT ...]] [-s [SERVICE [SERVICE ...]]] [-p] [-d] [-a] PDX_FILE

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
  -s [SERVICE [SERVICE ...]], --services [SERVICE [SERVICE ...]]
                        Print a list of diagnostic services specified in the pdx.
                        If no service names are specified, all services are printed.
  -p, --params          Print a list of all parameters relevant for the selected items.
  -d, --dops            Print a list of all data object properties relevant for the selected items
  -a, --all             Print a list of all diagnostic services and DOPs specified in the pdx
```

The options `--variants` and `--services` can be used to specify which
services should be printed.  If the `--params` option is specified,
the message layout is printed for all specified variants/services and
the `--all` parameter prints all data of the file that is recognized
by `odxtools`. Example:

```bash
$ odxtools --conformant list $BASE_DIR/odxtools/examples/somersault.pdx --variants somersault_lazy --services do_forward_flips --params
ECU-VARIANT 'somersault_lazy' (Receive ID: 0x7b, Send ID: 0x1c8)
 num services: 5, num DOPs: 6, num communication parameters: 11.
The services of the ECU-VARIANT 'somersault_lazy' are:
 do_forward_flips <ID: somersault.service.do_forward_flips>
  Message format of a request:
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
  Number of positive responses: 1
  Message format of a positive response:
           7     6     5     4     3     2     1     0
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid(8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | num_flips_done(8 bits)                        |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0xfa')
   Parameter(short_name='num_flips_done', type='MATCHING-REQUEST-PARAM', semantic=None, byte_position=1)
    Request byte position = 2, byte length = 1
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
   Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0x7f')
   Parameter(short_name='rq_sid', type='MATCHING-REQUEST-PARAM', semantic=None, byte_position=1)
    Request byte position = 0, byte length = 1
   Parameter(short_name='reason', type='VALUE', semantic=None, byte_position=2, bit_length=8, dop_ref='somersault.DOP.error_code')
    DataObjectProperty('error_code', category='LINEAR', internal_type='A_UINT32', physical_type='A_UINT32')
   Parameter(short_name='flips_successfully_done', type='VALUE', semantic=None, byte_position=3, bit_length=8, dop_ref='somersault.DOP.num_flips')
    DataObjectProperty('num_flips', category='LINEAR', internal_type='A_UINT32', physical_type='A_UINT32')
```

### The `browse` subcommand

The `browse` subcommand uses
[PyInquirer](https://github.com/CITGuru/PyInquirer/) to interactively
navigate through the database of a `.pdx` file. For example, using the
`browse` subcommand you can select the ECU and service without
spamming the terminal:

```bash
$ odxtools --conformant browse $BASE_DIR/odxtools/examples/somersault.pdx
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
currently running diagnostic session:

```bash
# create a socketcan `vcan0` interface
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up

# start the snooping on vcan0
odxtools --conformant snoop -c vcan0 --variant "somersault_lazy" $BASE_DIR/odxtools/examples/somersault.pdx

# on a different terminal, run the diagnostic session
$BASE_DIR/odxtools/examples/somersaultlazy.py -c vcan0
```

The snoop command will then output the following:

```bash
$ odxtools --conformant snoop -c vcan0 --variant "somersault_lazy" $BASE_DIR/odxtools/examples/somersault.pdx
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

The `find` subcommand can be used to find a service and its associated 
information by either a hex request, or partial name via cli. 

In addition, it can also decode a hex request and display its parameters 
mapped to a service. 

```bash
$ odxtools find $BASE_DIR/odxtools/examples/somersault.pdx -D 10 00


=====================================
somersault_lazy, somersault_assiduous
=====================================


 session_start <ID: somersault.service.session_start>
  Message format of a request:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | id (8 bits)                                   |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0x10')
   Parameter(short_name='id', type='CODED-CONST', semantic=None, byte_position=1, bit_length=8, coded_value='0x0')
  Number of positive responses: 1
  Message format of a positive response:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | can_do_backward_flips (8 bits)                |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0x50')
   Parameter(short_name='can_do_backward_flips', type='VALUE', semantic=None, byte_position=1, bit_length=8, dop_ref='somersault.DOP.boolean')
    DataObjectProperty('boolean', category='TEXTTABLE', internal_type='A_UINT32', physical_type='A_UNICODE2STRING')
  Number of negative responses: 1
  Message format of a negative response:
           7     6     5     4     3     2     1     0  
        +-----+-----+-----+-----+-----+-----+-----+-----+
      0 | sid (8 bits)                                  |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      1 | rq_sid (8 bits)                               |
        +-----+-----+-----+-----+-----+-----+-----+-----+
      2 | response_code (8 bits)                        |
        +-----+-----+-----+-----+-----+-----+-----+-----+
   Parameter(short_name='sid', type='CODED-CONST', semantic=None, byte_position=0, bit_length=8, coded_value='0x7f')
   Parameter(short_name='rq_sid', type='MATCHING-REQUEST-PARAM', semantic=None, byte_position=1)
    Request byte position = 0, byte length = 1
   Parameter(short_name='response_code', type='VALUE', semantic=None, byte_position=2, bit_length=8, dop_ref='somersault.DOP.error_code')
    DataObjectProperty('error_code', category='IDENTICAL', internal_type='A_UINT32', physical_type='A_UINT32')

Decoded Request('start_session'):
	sid: 16
	id: 0
```

`odxtools find $BASE_DIR/odxtools/examples/somersault.pdx -d 10 00` would display the same information, 
without the decoded request, and `-s <name>` can be used to find a service by partial name.

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

Please read our [Code of Conduct](https://github.com/mercedes-benz/daimler-foss/blob/master/CODE_OF_CONDUCT.md)
as it is our base for interaction.

## License

This project is licensed under the [MIT LICENSE](https://github.com/mercedes-benz/odxtools/blob/main/LICENSE).

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
