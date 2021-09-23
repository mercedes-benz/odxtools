# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import sys
import argparse
import PyInquirer
import json

import odxtools.snoop as snoop

from .load_file import load_file
from .database import Database
from .structures import Request, Response
from .parameters import ParameterWithDOP
from .odxtypes import ODX_TYPE_TO_PYTHON_TYPE

import logging
# logging.basicConfig(level=logging.DEBUG)


def _convert_string_to_odx_type(string_value: str, odx_type: str):
    if ODX_TYPE_TO_PYTHON_TYPE[odx_type] != str:
        if ODX_TYPE_TO_PYTHON_TYPE[odx_type] == int:
            return int(string_value, 0)
        elif ODX_TYPE_TO_PYTHON_TYPE[odx_type] == float:
            try:
                return float(string_value)
            except:
                sub_mantissas = string_value.split(".")
                if len(sub_mantissas) == 1:
                    logging.debug(
                        f"Interpreting string {string_value} as float {float(int(string_value, 0))}")
                    return float(int(string_value, 0))
                else:
                    mantissa_before_point = int(sub_mantissas[0], 16)
                    mantissa_after_point = int("0x" + sub_mantissas[1], 16)
                    mantissa_after_point *= 16**(-len(sub_mantissas[1]))
                    logging.debug(
                        f"Interpreting string {string_value} as float {mantissa_before_point + mantissa_after_point}")
                    return mantissa_before_point + mantissa_after_point

        elif ODX_TYPE_TO_PYTHON_TYPE[odx_type] in [bytes, bytearray]:
            val_as_int = int(string_value, 0)
            val_as_byte = val_as_int.to_bytes(
                (val_as_int.bit_length() + 7) // 8, "big")
            logging.debug(
                f"Value conversion: {string_value} -> {val_as_int} -> {val_as_byte.hex()}")
            return val_as_byte
    else:
        return str(string_value)


def _convert_string_to_bytes(string_value):
    if all(len(x) <= 2 for x in string_value.split(" ")):
        return bytes(int(x, 16) for x in string_value.split(" ") if len(x) > 0)
    else:
        return int(string_value, 16).to_bytes((int(string_value, 16).bit_length() + 7) // 8, 'big')


def print_diagnostic_service(service, print_params=False):

    print(f" {service.short_name} <ID: {service.id}>")
    if print_params:
        print(f"  Message format of a request:")
        service.request.print_message_format(indent=3)

        print(
            f"  Number of positive responses: {len(service.positive_responses)}")
        if len(service.positive_responses) == 1:
            print(f"  Message format of a positive response:")
            service.positive_responses[0].print_message_format(
                indent=3)

        print(
            f"  Number of negative responses: {len(service.negative_responses)}")
        if len(service.negative_responses) == 1:
            print(f"  Message format of a negative response:")
            service.negative_responses[0].print_message_format(
                indent=3)

    if len(service.positive_responses) > 1 or len(service.negative_responses) > 1:
        # Does this ever happen?
        raise NotImplementedError(
            f"The diagnostic service {service.id} offers more than one response!")


def print_summary(odxdb: Database,
                  print_services=False,
                  print_dops=False,
                  print_params=False,
                  print_com_params=False,
                  variants=None,
                  service_filter=lambda x: True):

    diag_layer_names = variants if variants else list(map(lambda dl: dl.short_name, odxdb.diag_layers))

    for dl_sn in diag_layer_names:
        dl = odxdb.diag_layers[dl_sn]
        if not dl:
            print(f"The variant '{dl_sn}' could not be found!")
            continue
        service_sns = sorted(service.short_name for service in dl.services)
        data_object_properties = dl.data_object_properties
        com_params = dl.communication_parameters

        if dl.get_receive_id() is not None:
            recv_id = hex(dl.get_receive_id())
        else:
            recv_id = "None"
        if dl.get_send_id() is not None:
            send_id = hex(dl.get_send_id())
        else:
            send_id = "None"
        print(
            f"{dl.variant_type} '{dl.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
        )
        print(
            f" num services: {len(service_sns)}, num DOPs: {len(data_object_properties)}, num communication parameters: {len(com_params)}."
        )

        if print_services and len(service_sns) > 0:
            services = [dl.services[service_sn] for service_sn in service_sns]
            services = list(filter(service_filter, services))
            if len(services) > 0:
                print(
                    f"The services of the {dl.variant_type} '{dl.short_name}' are: ")
                for service in services:
                    if service_filter(service):
                        print_diagnostic_service(
                            service, print_params=print_params)

        if print_dops and len(data_object_properties) > 0:
            print(f"The DOPs of the {dl.variant_type} '{dl.short_name}' are: ")
            for dop in sorted(data_object_properties, key=lambda x: (type(x).__name__, x.short_name)):
                print("  " + str(dop).replace("\n", "\n  "))

        if print_com_params and len(com_params) > 0:
            print(
                f"The communication parameters of the {dl.variant_type} '{dl.short_name}' are: ")
            for com_param in com_params:
                print(f"  {com_param.id_ref}: {com_param.value}")


def _validate_string_value(input, parameter):
    if parameter.is_optional() and input == "":
        return True
    elif isinstance(parameter, ParameterWithDOP):
        try:
            val = _convert_string_to_odx_type(input,
                                              parameter.physical_data_type
                                              )
        except:
            return False
        return parameter.dop.is_valid_physical_value(val)
    else:
        logging.info(
            "This value is not validated precisely: Parameter {parameter}"
        )
        return input != ""


def prompt_single_parameter_value(parameter):
    if not isinstance(parameter, ParameterWithDOP) or parameter.get_valid_physical_values() is None or parameter.get_valid_physical_values() is []:
        param_prompt = [{
            "type": "input",
            "name": parameter.short_name,
            "message": f"Value for parameter '{parameter.short_name}' (Type: {parameter.physical_data_type})" + (f"[optional]" if parameter.is_optional() else ""),
            # TODO: improve validation
            "validate": lambda x: _validate_string_value(x, parameter),
            # TODO: do type conversion?
            "filter": lambda x: x
            # x if x == "" or p.physical_data_type is None
            # else _convert_string_to_odx_type(x, p.physical_data_type, param=p) # This does not work because the next parameter to be promted is used (for some reason?)
        }]
    else:
        param_prompt = [{
            "type": "list",
            "name": parameter.short_name,
            "message": f"Value for parameter '{parameter.short_name}'",
            "choices": parameter.get_valid_physical_values()
        }]
    answer = PyInquirer.prompt(param_prompt)
    if answer.get(parameter.short_name) == "" and parameter.is_optional():
        return None
    elif parameter.physical_data_type is not None:
        return _convert_string_to_odx_type(answer.get(parameter.short_name), parameter.physical_data_type)
    else:
        logging.warning(
            f"Parameter {parameter.short_name} does not have a physical data type. Param details: {parameter}")
        return answer.get(parameter.short_name)


def encode_message_interactively(sub_service, ask_user_confirmation=False):
    if not sys.__stdin__.isatty() or not sys.__stdout__.isatty():
        raise SystemError(
            "This command can only be used in an interactive shell!")
    param_dict = sub_service.parameter_dict()

    # list(filter(lambda p: p.is_required()
    #                          or p.is_optional(), sub_service.parameters))
    exists_definable_param = False
    for k, param_or_dict in param_dict.items():
        if isinstance(param_or_dict, dict):
            for k, param in param_or_dict.items():
                if param.is_required() or param.is_optional():
                    exists_definable_param = True
        elif param_or_dict.is_required() or param_or_dict.is_optional():
            exists_definable_param = True

    param_values = {}
    if exists_definable_param > 0:
        # Ask whether user wants to encode a message
        if ask_user_confirmation:
            encode_message_prompt = [{
                "type": "list",
                "name": "yes_no_prompt",
                "message": f"Do you want to encode a message? [y/n]",
                "choices": ["yes", "no"]
            }]
            answer = PyInquirer.prompt(encode_message_prompt)
            if answer.get("yes_no_prompt") == "no":
                return

        if isinstance(sub_service, Response):
            answered_request_prompt = [{
                "type": "input",
                "name": "request",
                "message": f"What is the request you want to answer? (Enter the coded request as integer in hexadecimal format (e.g. 12 3B 5)",
                "filter": lambda input: _convert_string_to_bytes(input)
            }]
            answer = PyInquirer.prompt(answered_request_prompt)
            answered_request = answer.get("request")
            print(f"Input interpretation as list: {list(answered_request)}")

        print(
            "Warning: Type conversion only works 'sometimes' .. pass integers, unless a list of valid text values is given.")

        # Request values for parameters
        for key, param_or_structure in param_dict.items():
            if isinstance(param_or_structure, dict):
                # param_or_structure refers to a structure (represented as dict of params)
                print(
                    f"The next {len(param_or_structure)} parameters belong to the structure '{key}'")
                structure_param_values = {}
                for param_sn, param in param_or_structure.items():
                    if param.is_required() or param.is_optional():
                        val = prompt_single_parameter_value(param)
                        if val is not None:
                            structure_param_values[param_sn] = val
                param_values[key] = structure_param_values
            elif (param_or_structure.is_required() or param_or_structure.is_optional()) and param_or_structure.parameter_type != "MATCHING-REQUEST-PARAM":
                # param_or_structure is a parameter
                val = prompt_single_parameter_value(param_or_structure)
                if val is not None:
                    param_values[key] = val
        if isinstance(sub_service, Response):
            payload = sub_service.encode(
                param_values, coded_request=answered_request)
        else:
            payload = sub_service.encode(param_values)
    else:
        # There are no optional parameters that need to be defined by the user -> Just print message
        payload = sub_service.encode()
    print(f"Message payload: 0x{bytes(payload).hex()}")


def encode_message_from_string_values(sub_service, parameter_values: dict = {}):
    parameter_values = parameter_values.copy()
    param_dict = sub_service.parameter_dict()

    # Check if all needed parameters are given
    missing_parameter_names = []
    for parameter_sn, parameter in param_dict.items():
        if isinstance(parameter, dict):
            # parameter_value refers to a structure (represented as dict of params)
            for simple_param_sn, simple_param in parameter.items():
                if simple_param.is_required() and (parameter_values.get(parameter_sn) is None or parameter_values.get(parameter_sn).get(simple_param_sn) is None):
                    missing_parameter_names.append(
                        f"{parameter_sn} :: {simple_param_sn}")
        else:
            if parameter.is_required() and parameter_values.get(parameter_sn) is None:
                missing_parameter_names.append(parameter_sn)
    if len(missing_parameter_names) > 0:
        print("The following parameters are required but missing!")
        print(" - " + "\n - ".join(missing_parameter_names))
        return

    # Request values for parameters
    for parameter_sn, parameter_value in parameter_values.items():
        if isinstance(parameter_value, dict):
            # parameter_value refers to a structure (represented as dict of params)
            parameter_values[parameter_sn] = parameter_values[parameter_sn].copy()
            for simple_param_sn, simple_val in parameter_value.items():
                try:
                    parameter = param_dict[parameter_sn][simple_param_sn]
                except:
                    print(f"I don't know the parameter {simple_param_sn}")
                    continue
                parameter_values[parameter_sn][simple_param_sn] = _convert_string_to_odx_type(
                    simple_val,
                    parameter.physical_data_type
                )
        else:
            try:
                parameter = param_dict[parameter_sn]
            except:
                print(f"I don't know the parameter {parameter_sn}")
                continue
            parameter_values[parameter_sn] = _convert_string_to_odx_type(
                parameter_value,
                parameter.physical_data_type if parameter.parameter_type != "MATCHING-REQUEST-PARAM"
                else "A_BYTEFIELD"
            )
    payload = sub_service.encode(parameter_values)
    print(f"Message payload: 0x{bytes(payload).hex()}")


def browse(odxdb: Database):
    if not sys.__stdin__.isatty() or not sys.__stdout__.isatty():
        raise SystemError(
            "This command can only be used in an interactive shell!")
    dl_names = list(map(lambda dl: dl.short_name, odxdb.diag_layers))
    while True:
        # Select an ECU
        selection = [{
            "type": "list",
            "name": "variant",
            "message": "Select a Variant.",
            "choices": list(dl_names) + ["[exit]"]
        }]
        answer = PyInquirer.prompt(selection)
        if answer.get("variant") == "[exit]":
            return

        variant = odxdb.diag_layers[answer.get("variant")]
        recv_id = hex(variant.get_receive_id()
                      ) if variant.get_receive_id() is not None else "None"
        send_id = hex(variant.get_send_id()
                      ) if variant.get_send_id() is not None else "None"
        print(
            f"{variant.variant_type} '{variant.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
        )

        service_sn = 0
        while True:
            # Select a service of the ECU
            selection = [{
                "type": "list",
                "name": "service",
                "message": f"The variant {variant.short_name} offers the following services. Select one!",
                "choices": [s.short_name for s in variant.services] + ["[back]"],
            }]
            answer = PyInquirer.prompt(selection)
            if answer.get("service") == "[back]":
                break

            service_sn = answer.get("service")

            service = variant.services[service_sn]

            # Select a service of the ECU
            selection = [{
                "type": "list",
                "name": "message_type",
                "message": "This service offers the following messages.",
                "choices":
                    [{
                        "name": f"Request: {service.request.short_name}",
                        "value": service.request,
                        "short": f"Request: {service.request.short_name}"
                    }] +
                    [{
                        "name": f"Positive response: {pr.short_name}",
                        "value": pr,
                        "short": f"Positive response: {pr.short_name}"
                    } for pr in service.positive_responses] +
                    [{
                        "name": f"Negative response: {nr.short_name}",
                        "value": nr,
                        "short": f"Negative response: {nr.short_name}"
                    } for nr in service.negative_responses]
                    + ["[back]"]
            }]
            answer = PyInquirer.prompt(selection)
            if answer.get("message_type") == "[back]":
                continue

            sub_service = answer.get("message_type")
            sub_service.print_message_format()

            encode_message_interactively(
                sub_service, ask_user_confirmation=True)


def start_cli():
    argparser = argparse.ArgumentParser(
        description="\n".join([
            "Utilities to interact with automotive diagnostic descriptions based on the ODX standard.",
            "",
            "Examples:",
            "  For printing all services use:",
            "   odxtools list ./path/to/database.pdx --services",
            "  For browsing the data base and encoding messages use:",
            "   odxtools browse ./path/to/database.pdx"
        ]),
        prog="odxtools",
        formatter_class=argparse.RawTextHelpFormatter)

    # do not enable the CANdela workarounds. Note that we disable then
    # by default because CANdela is by far the most common tool to
    # work with ODX.
    argparser.add_argument("-c", "--conformant", default=False, action='store_const', const=True,
                           required=False, help="The input file fully confirms to the standard, i.e., disable work-arounds for bugs of the CANdela tool")

    subparsers = argparser.add_subparsers(
        help='Select a sub command', dest="subparser_name")

    # The 'list' command just dumps stuff to the console
    parser_list = subparsers.add_parser(
        'list',
        description="\n".join([
            "List the content of automotive diagnostic files (*.pdx)",
            "",
            "Examples:",
            "  For displaying only the names of the diagnostic layers use:",
            "    odxtools list ./path/to/database.pdx",
            "  For displaying all content use:",
            "    odxtools list ./path/to/database.pdx --all",
            "  For more information use:",
            "    odxtools list -h"
        ]),
        help="Print a summary of automotive diagnostic files.",
        formatter_class=argparse.RawTextHelpFormatter)

    parser_list.add_argument(
        "pdx_file", metavar="PDX_FILE", help="path to the .pdx file")

    parser_list.add_argument("-v", "--variants", nargs='+', metavar="VARIANT",
                             required=False, help="Specifies which variants should be included.", default="all")

    # The service option is None if option is not passed at all (-> do not print services), it is an empty list if "--services is passed"
    parser_list.add_argument("-s", "--services", nargs='*', default=None, metavar="SERVICE",
                             required=False, help="Print a list of diagnostic services specified in the pdx. \n"
                             + "If no service names are specified, all services are printed.")
    # Pretty print message format and list parameters
    parser_list.add_argument("-p", "--params", default=False, action='store_const', const=True,
                             required=False, help="Print a list of all parameters relevant for the selected items.\n")
    parser_list.add_argument("-d", "--dops", default=False, action='store_const', const=True,
                             required=False, help="Print a list of all data object properties relevant for the selected items")

    # Shortcut to just dump everything
    parser_list.add_argument("-a", "--all", default=False, action='store_const', const=True,
                             required=False, help="Print a list of all diagnostic services and DOPs specified in the pdx")

    # Browse interactively to avoid spamming the console.
    parser_browse = subparsers.add_parser(
        'browse',
        description="Interactively browse the content of automotive diagnostic files (*.pdx).",
        help="Interactively browse the content of automotive diagnostic files.",
        formatter_class=argparse.RawTextHelpFormatter)

    parser_browse.add_argument(
        "pdx_file", metavar="PDX_FILE", help="path to the .pdx file")

    # follow a diagnostics session over a CAN bus and ISO-TP
    parser_snoop = subparsers.add_parser(
        'snoop',
        description="Live decoding of a diagnostic session.",
        help="Live decoding of a diagnostic session.",
        formatter_class=argparse.RawTextHelpFormatter)

    snoop.add_cli_arguments(parser_snoop)

    # Encode a message (this is basically a short cut through browse to directly encode).
    parser_encode = subparsers.add_parser(
        'encode-message',
        description="Encode a message. Interactively asks for parameter values.",
        help="\n".join([
            "Encode a message. Interactively asks for parameter values.",
            "This is a short cut through the browse command to directly encode a message."
        ]),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser_encode.add_argument("pdx_file", metavar="PDX_FILE",
                               help="path to the .pdx file")

    source_group = parser_encode.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--short-names", metavar=("ECU_VARIANT", "DIAGNOSTIC_SERVICE"),
                              nargs=2, help="short name of the diagnostic layer and service")
    source_group.add_argument("--service-id", metavar="DIAGNOSTIC_SERVICE_ID", nargs=1,
                              help="ID of the request")

    parser_encode.add_argument("--type", choices=["RQ", "PR", "NR"], default="RQ",
                               required=False, help="")

    parser_encode.add_argument("--parameters", metavar="JSON_DICT",
                               help="\n".join([
                                   "parameters as JSON dict, e.g.,",
                                   "'{\"param_name\": \"param_value\", \"structure_name\": {\"simple_param_name\" : \"simple_param_value\"}}'",
                                   "Note that you have to use \" as delimiter for each name and value."]
                               )
                               )

    # Decode message
    parser_decode = subparsers.add_parser(
        'decode-message',
        description="Encode a message. Interactively asks for parameter values.",
        help="\n".join([
            "Decode a message. Interactively asks for parameter values.",
            "This is a short cut through the browse command to directly encode a message."
        ]),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser_decode.add_argument("pdx_file", metavar="PDX_FILE",
                               help="path to the .pdx file")
    parser_decode.add_argument("--variant", metavar=("ECU_VARIANT"),
                               nargs=1, help="short name of the diagnostic layer")
    parser_decode.add_argument("--message", metavar=("UDS-MESSAGE"),
                               nargs=1, help="UDS message to be decoded, e.g. 0x1A2B3C")

    args = argparser.parse_args()  # deals with the help message handling

    if args.subparser_name is None:
        argparser.print_usage()
        exit()

    db_file_name = args.pdx_file

    logging.debug(f"Argument interpretation: {args}")
    odxdb = None
    if db_file_name is not None:
        odxdb = load_file(db_file_name,
                          enable_candela_workarounds=not args.conformant)

    if args.subparser_name == "list":
        variants = args.variants if args.variants else None

        print_summary(odxdb, print_services=args.all or args.params or args.services is not None,
                      service_filter=(lambda s: s.short_name in args.services
                                      if args.services and len(args.services) > 0 else lambda s: True),
                      print_dops=args.all or args.dops, variants=None if variants == "all" else variants,
                      print_params=args.all or args.params,
                      print_com_params=args.all)
    elif args.subparser_name == "browse":
        browse(odxdb)
    elif args.subparser_name == "snoop":
        snoop.run(args, odxdb)
    elif args.subparser_name == "encode-message":
        if args.short_names:
            variant_sn = args.short_names[0]
            service_sn = args.short_names[1]
            diagnostic_service = odxdb.diag_layers[variant_sn].services[service_sn]
        else:
            service_id = args.service_id[0]
            diagnostic_service = odxdb.id_lookup[service_id]
        if args.type == "RQ":
            serv = diagnostic_service.request
        elif args.type == "PR":
            serv = diagnostic_service.positive_responses[0]
        elif args.type == "NR":
            serv = diagnostic_service.negative_responses[0]
        else:
            print(f"Message type: {args.type}")

        if args.parameters is not None:
            params = json.loads(args.parameters)
            encode_message_from_string_values(serv, params)
        else:
            encode_message_interactively(serv, ask_user_confirmation=False)

        # print("Pass parameters with the --parameter option. Use JSON Format. The parameters are:")
        # print("{")
        # print(", \n".join(f"{p_sn} : {param}" for p_sn, param in serv.parameter_dict().items()))
        # print("}")
    elif args.subparser_name == "decode-message":
        variant_sn = args.variant[0]
        uds_message = _convert_string_to_bytes(args.message[0])
        variant = odxdb.diag_layers[variant_sn]
        for m in variant.decode(uds_message):
            print(f"{m}")


if __name__ == "__main__":
    # Command line tool
    start_cli()
else:
    # Module is imported
    pass
