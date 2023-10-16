# SPDX-License-Identifier: MIT
import argparse
import logging
import sys
from typing import List, Optional, Union

import PyInquirer.prompt as PI_prompt

from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diaglayer import DiagLayer
from ..diagservice import DiagService
from ..exceptions import odxraise, odxrequire
from ..odxtypes import AtomicOdxType, DataType, ParameterValueDict
from ..parameters.matchingrequestparameter import MatchingRequestParameter
from ..parameters.parameter import Parameter
from ..parameters.parameterwithdop import ParameterWithDOP
from ..parameters.valueparameter import ValueParameter
from ..request import Request
from ..response import Response
from . import _parser_utils

# name of the tool
_odxtools_tool_name_ = "browse"


def _convert_string_to_odx_type(string_value: str, odx_type: DataType) -> AtomicOdxType:
    """Similar to odx_type.from_string(string_value) but more relaxed to parse user input"""
    if odx_type == DataType.A_UINT32:
        return int(string_value, 0)
    elif odx_type == DataType.A_BYTEFIELD:
        return _convert_string_to_bytes(string_value)
    else:
        return odx_type.from_string(string_value)


def _convert_string_to_bytes(string_value: str) -> bytes:
    if all(len(x) <= 2 for x in string_value.split(" ")):
        return bytes(int(x, 16) for x in string_value.split(" ") if len(x) > 0)
    else:
        return int(string_value, 16).to_bytes((int(string_value, 16).bit_length() + 7) // 8, "big")


def _validate_string_value(input: str, parameter: Parameter) -> bool:
    if not parameter.is_required and input == "":
        return True
    elif isinstance(parameter, ParameterWithDOP):
        try:
            phys_type = odxrequire(parameter.physical_type)
            val = _convert_string_to_odx_type(input, phys_type.base_data_type)
        except:  # noqa: E722
            return False
        dop = parameter.dop
        if isinstance(dop, DataObjectProperty):
            return dop.is_valid_physical_value(val)
        else:
            raise NotImplementedError("Validation of complex DOPs")
    else:
        logging.info("This value is not validated precisely: Parameter {parameter}")
        return input != ""


def prompt_single_parameter_value(parameter: Parameter) -> Optional[AtomicOdxType]:
    if not isinstance(parameter, ValueParameter):
        odxraise("Only the value of ValueParameters can be queried")
    if parameter.physical_type is None:
        odxraise("Only ValueParameters which define a physical data type can be queried")

    # TODO: add valid choices for the parameter
    #        "choices": parameter.get_valid_physical_values(),
    param_prompt = [{
        "type":
            "input",
        "name":
            parameter.short_name,
        "message":
            f"Value for parameter '{parameter.short_name}' (Type: {parameter.physical_type.base_data_type})"
            + (f"[optional]" if not parameter.is_required else ""),
        # TODO: improve validation
        "validate":
            lambda x: _validate_string_value(x, parameter),
        # TODO: do type conversion?
        "filter":
            lambda x: x
        # x if x == "" or p.physical_type.base_data_type is None
        # else _convert_string_to_odx_type(x, p.physical_type.base_data_type, param=p) # This does not work because the next parameter to be promted is used (for some reason?)
    }]

    if hasattr(parameter, "dop") and hasattr(parameter.dop, "compu_method") \
       and hasattr(parameter.dop.compu_method, "get_scales"):
        scales = parameter.dop.compu_method.get_scales()
        choices = [scale.compu_const for scale in scales if scale is not None]
        param_prompt[0]["choices"] = choices

    answer = PI_prompt.prompt(param_prompt)
    if answer.get(parameter.short_name) == "" and not parameter.is_required:
        return None
    elif parameter.physical_type.base_data_type is not None:
        return _convert_string_to_odx_type(
            answer.get(parameter.short_name), parameter.physical_type.base_data_type)
    else:
        logging.warning(
            f"Parameter {parameter.short_name} does not have a physical data type. Param details: {parameter}"
        )
        return answer.get(parameter.short_name)


def encode_message_interactively(sub_service: Union[Request, Response],
                                 ask_user_confirmation: bool = False) -> None:
    if not sys.__stdin__.isatty() or not sys.__stdout__.isatty():
        raise SystemError("This command can only be used in an interactive shell!")
    param_dict = sub_service.parameter_dict()

    exists_definable_param = False
    for param_or_dict in param_dict.values():
        if isinstance(param_or_dict, dict):
            for param in param_or_dict.values():
                if not isinstance(param_or_dict, dict) and param.is_settable:
                    exists_definable_param = True
        elif param_or_dict.is_settable:
            exists_definable_param = True

    param_values: ParameterValueDict = {}
    if exists_definable_param > 0:
        # Ask whether user wants to encode a message
        if ask_user_confirmation:
            encode_message_prompt = [{
                "type": "list",
                "name": "yes_no_prompt",
                "message": f"Do you want to encode a message? [y/n]",
                "choices": ["yes", "no"],
            }]
            answer = PI_prompt.prompt(encode_message_prompt)
            if answer.get("yes_no_prompt") == "no":
                return

        if isinstance(sub_service, Response):
            answered_request_prompt = [{
                "type":
                    "input",
                "name":
                    "request",
                "message":
                    f"What is the request you want to answer? (Enter the coded request as integer in hexadecimal format (e.g. 12 3B 5)",
                "filter":
                    lambda input: _convert_string_to_bytes(input),
            }]
            answer = PI_prompt.prompt(answered_request_prompt)
            answered_request = answer.get("request")
            print(f"Input interpretation as list: {list(answered_request)}")

        # Request values for parameters
        for key, param_or_structure in param_dict.items():
            if isinstance(param_or_structure, dict):
                # param_or_structure refers to a structure (represented as dict of params)
                print(
                    f"The next {len(param_or_structure)} parameters belong to the structure '{key}'"
                )
                structure_param_values: ParameterValueDict = {}
                for param_sn, param in param_or_structure.items():
                    if not isinstance(param, dict) and param.is_settable:
                        val = prompt_single_parameter_value(param)
                        if val is not None:
                            structure_param_values[param_sn] = val
                param_values[key] = structure_param_values
            elif param_or_structure.is_settable:
                # param_or_structure is a parameter
                val = prompt_single_parameter_value(param_or_structure)
                if val is not None:
                    param_values[key] = val
        if isinstance(sub_service, Response):
            payload = sub_service.encode(coded_request=answered_request, **param_values)
        else:
            payload = sub_service.encode(coded_request=b'', **param_values)
    else:
        # There are no optional parameters that need to be defined by the user -> Just print message
        payload = sub_service.encode()
    print(f"Message payload: 0x{bytes(payload).hex()}")


def encode_message_from_string_values(
    sub_service: Union[Request, Response],
    parameter_values: Optional[ParameterValueDict] = None,
) -> None:
    if parameter_values is None:
        parameter_values = {}
    parameter_values = parameter_values.copy()
    param_dict = sub_service.parameter_dict()

    # Check if all needed parameters are given
    missing_parameter_names = []
    for param_sn, param in param_dict.items():
        if isinstance(param, dict):
            # param_value refers to a structure (represented as dict of params)
            for simple_param_sn, simple_param in param.items():
                structured_value = parameter_values.get(param_sn)
                if not isinstance(simple_param, Parameter):
                    continue
                if simple_param.is_required and (not isinstance(structured_value, dict) or
                                                 structured_value.get(simple_param_sn) is None):
                    missing_parameter_names.append(f"{param_sn} :: {simple_param_sn}")
        else:
            if param.is_required and parameter_values.get(param_sn) is None:
                missing_parameter_names.append(param_sn)

    if len(missing_parameter_names) > 0:
        print("The following parameters are required but missing!")
        print(" - " + "\n - ".join(missing_parameter_names))
        return

    # Request values for parameters
    for parameter_sn, parameter_value in parameter_values.items():
        parameter = param_dict.get(parameter_sn)
        if parameter is None:
            print(f"I don't know the parameter {parameter_sn}")
            continue

        if isinstance(parameter_value, dict):
            # parameter_value refers to a structure (represented as dict of params)
            typed_dict = parameter_value.copy()
            for simple_param_sn, simple_param_val in parameter_value.items():
                simple_parameter = param_dict.get(simple_param_sn)
                if simple_parameter is None:
                    print(f"Unknown sub-parameter {simple_param_sn}")
                    continue
                if not isinstance(simple_param_val, str):
                    print(f"The value specified for parameter {simple_param_sn} is not a string")
                    continue

                typed_dict[simple_param_sn] = _convert_string_to_odx_type(
                    simple_param_val,
                    simple_parameter.physical_type.base_data_type  # type: ignore[union-attr]
                )
                parameter_values[parameter_sn] = typed_dict
        else:
            assert isinstance(parameter, Parameter)

            if not isinstance(parameter_value, str):
                print(f"Value for parameter {parameter_sn} is not a string")
                continue

            if not isinstance(parameter, MatchingRequestParameter):
                parameter_values[parameter_sn] = _convert_string_to_odx_type(
                    parameter_value,
                    parameter.physical_type.base_data_type,  # type: ignore[attr-defined]
                )
            else:
                parameter_values[parameter_sn] = _convert_string_to_odx_type(
                    parameter_value, DataType.A_BYTEFIELD)

    payload = sub_service.encode(**parameter_values)  # type: ignore
    print(f"Message payload: 0x{bytes(payload).hex()}")


def browse(odxdb: Database) -> None:
    if not sys.__stdin__.isatty() or not sys.__stdout__.isatty():
        raise SystemError("This command can only be used in an interactive shell!")
    dl_names = [dl.short_name for dl in odxdb.diag_layers]
    while True:
        # Select an ECU
        selection = [{
            "type": "list",
            "name": "variant",
            "message": "Select a Variant.",
            "choices": list(dl_names) + ["[exit]"],
        }]
        answer = PI_prompt.prompt(selection)
        if answer.get("variant") == "[exit]":
            return

        variant = odxdb.diag_layers[answer.get("variant")]
        assert isinstance(variant, DiagLayer)

        if (rx_id := variant.get_receive_id()) is not None:
            recv_id = hex(rx_id)
        else:
            recv_id = "None"

        if (tx_id := variant.get_send_id()) is not None:
            send_id = hex(tx_id)
        else:
            send_id = "None"

        print(
            f"{variant.variant_type.value} '{variant.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
        )

        service_sn = 0
        while True:
            services: List[DiagService] = [
                s for s in variant.services if isinstance(s, DiagService)
            ]
            # Select a service of the ECU
            selection = [{
                "type":
                    "list",
                "name":
                    "service",
                "message":
                    f"The variant {variant.short_name} offers the following services. Select one!",
                "choices": [s.short_name for s in services] + ["[back]"],
            }]
            answer = PI_prompt.prompt(selection)
            if answer.get("service") == "[back]":
                break

            service_sn = answer.get("service")

            service = variant.services[service_sn]
            assert isinstance(service, DiagService)
            assert service.request is not None
            assert service.positive_responses is not None
            assert service.negative_responses is not None

            # Select a request/ response of the service
            selection = [{
                "type":
                    "list",
                "name":
                    "message_type",
                "message":
                    "This service offers the following messages.",
                "choices": [{
                    "name": f"Request: {service.request.short_name}",
                    "value": service.request,
                    "short": f"Request: {service.request.short_name}",
                }] + [{
                    "name": f"Positive response: {pr.short_name}",
                    "value": pr,
                    "short": f"Positive response: {pr.short_name}",
                } for pr in service.positive_responses] + [{
                    "name": f"Negative response: {nr.short_name}",
                    "value": nr,
                    "short": f"Negative response: {nr.short_name}",
                } for nr in service.negative_responses] + ["[back]"],  # type: ignore
            }]
            answer = PI_prompt.prompt(selection)
            if answer.get("message_type") == "[back]":
                continue

            sub_service = answer.get("message_type")
            sub_service.print_message_format()

            encode_message_interactively(sub_service, ask_user_confirmation=True)


def add_subparser(subparsers: "argparse._SubParsersAction") -> None:
    # Browse interactively to avoid spamming the console.
    parser = subparsers.add_parser(
        "browse",
        description="Interactively browse the content of automotive diagnostic files (*.pdx).",
        help="Interactively browse the content of automotive diagnostic files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    _parser_utils.add_pdx_argument(parser)


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)
    browse(odxdb)
