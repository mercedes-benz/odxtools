# SPDX-License-Identifier: MIT
import argparse
import logging
import sys
from typing import List, Optional, Union, cast

import InquirerPy.prompt as IP_prompt

from ..complexdop import ComplexDop
from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diaglayer import DiagLayer
from ..diagservice import DiagService
from ..dopbase import DopBase
from ..exceptions import odxraise, odxrequire
from ..hierarchyelement import HierarchyElement
from ..odxlink import resolve_snref
from ..odxtypes import AtomicOdxType, DataType, ParameterValueDict
from ..parameters.matchingrequestparameter import MatchingRequestParameter
from ..parameters.parameter import Parameter
from ..parameters.parameterwithdop import ParameterWithDOP
from ..parameters.valueparameter import ValueParameter
from ..request import Request
from ..response import Response
from . import _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import extract_parameter_tabulation_data

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

    if (dop := getattr(parameter, "dop", None)) and \
       (compu_method := getattr(dop, "compu_method", None)):
        scales = compu_method.internal_to_phys
        choices = [scale.compu_const for scale in scales if scale is not None]
        if (cdv := compu_method.compu_default_value) is not None:
            choices.append(cdv.compu_const)
        param_prompt[0]["choices"] = choices

    answer = IP_prompt(param_prompt)
    if answer.get(parameter.short_name) == "" and not parameter.is_required:
        return None
    elif parameter.physical_type.base_data_type is not None:
        return _convert_string_to_odx_type(
            cast(str, answer.get(parameter.short_name)), parameter.physical_type.base_data_type)
    else:
        logging.warning(
            f"Parameter {parameter.short_name} does not have a physical data type. Param details: {parameter}"
        )
        return cast(str, answer.get(parameter.short_name))


def encode_message_interactively(codec: Union[Request, Response],
                                 ask_user_confirmation: bool = False) -> None:
    if sys.__stdin__ is None or sys.__stdout__ is None or not sys.__stdin__.isatty(
    ) or not sys.__stdout__.isatty():
        raise SystemError("This command can only be used in an interactive shell!")

    answered_request = b''
    if isinstance(codec, Response):
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
        answer = IP_prompt(answered_request_prompt)
        answered_request = cast(bytes, answer.get("request"))
        print(f"Input interpretation as list: {list(answered_request)}")

    has_settable_param = False
    for param in codec.parameters:
        if not param.is_settable:
            continue

        # TODO: Specifying complex parameters with nesting depth > 1
        # is not possible yet
        if (inner_params := getattr(getattr(param, "dop", None), "parameters", None)) is not None:
            for inner_param in inner_params:
                if inner_param.is_settable:
                    has_settable_param = True
        elif param.is_settable:
            has_settable_param = True

    param_values: ParameterValueDict = {}
    if has_settable_param:
        # Ask whether user wants to encode a message
        if ask_user_confirmation:
            encode_message_prompt = [{
                "type": "list",
                "name": "yes_no_prompt",
                "message": f"Do you want to encode a message? [y/n]",
                "choices": ["yes", "no"],
            }]
            answer = IP_prompt(encode_message_prompt)
            if answer.get("yes_no_prompt") == "no":
                return

        # Query user for the values of all settable parameters
        for param in codec.parameters:
            if (inner_params := getattr(dop := getattr(param, "dop", None), "parameters",
                                        None)) is not None:
                assert isinstance(dop, DopBase)
                inner_params = cast(List[Parameter], inner_params)
                # param refers to a complex DOP, i.e., the required
                # value is a key-value dict
                print(
                    f"The next {len(inner_params)} parameters belong to the structure '{dop.short_name}'"
                )
                structure_param_values: ParameterValueDict = {}
                for inner_param in inner_params:
                    if inner_param.is_settable:
                        val = prompt_single_parameter_value(inner_param)
                        if val is not None:
                            structure_param_values[inner_param.short_name] = val
                param_values[param.short_name] = structure_param_values
            elif param.is_settable:
                val = prompt_single_parameter_value(param)
                if val is not None:
                    param_values[param.short_name] = val

        if isinstance(codec, Response):
            payload = codec.encode(coded_request=answered_request, **param_values)
        else:
            payload = codec.encode(coded_request=b'', **param_values)
    else:
        # There are no settable parameters -> Just print message
        if isinstance(codec, Response):
            payload = codec.encode(coded_request=answered_request)
        else:
            payload = codec.encode()

    print(f"Message payload: 0x{bytes(payload).hex()}")


def encode_message_from_string_values(
    sub_service: Union[Request, Response],
    parameter_values: Optional[ParameterValueDict] = None,
) -> None:
    if parameter_values is None:
        parameter_values = {}
    parameter_values = parameter_values.copy()

    # Check if all needed parameters have been specified
    missing_parameter_names = []
    for param in sub_service.parameters:
        if (inner_params := getattr(dop := getattr(param, "dop", None), "parameters",
                                    None)) is not None:
            inner_param_values = parameter_values.get(param.short_name, {})
            if not isinstance(inner_param_values, dict):
                print(f"Value for composite parameter {param.short_name} must be "
                      f"a dictionary, got {type(inner_param_values).__name__}")
                continue
            for inner_param in inner_params:
                if inner_param.is_required and inner_param.short_name not in inner_param_values:
                    missing_parameter_names.append(f"{param.short_name}.{inner_param.short_name}")
        else:
            if param.is_required and parameter_values.get(param.short_name) is None:
                missing_parameter_names.append(param.short_name)

    if len(missing_parameter_names) > 0:
        print("The following parameters are required but missing:")
        print(" - " + "\n - ".join(sorted(missing_parameter_names)))
        return

    # Request values for parameters
    for parameter_sn, parameter_value in parameter_values.items():
        parameter = resolve_snref(parameter_sn, sub_service.parameters, Parameter)
        if parameter is None:
            print(f"I don't know the parameter {parameter_sn}")
            continue

        if isinstance(parameter_value, dict):
            # parameter_value refers to a structure (represented as dict of params)
            dop = getattr(parameter, "dop", None)
            inner_params = getattr(dop, "parameters", None)
            assert isinstance(dop, ComplexDop)
            assert isinstance(inner_params, list)
            inner_params = cast(List[Parameter], inner_params)

            typed_dict = parameter_value.copy()
            for inner_param_sn, inner_param_value in parameter_value.items():
                inner_param = resolve_snref(inner_param_sn, inner_params, Parameter)
                if inner_param is None:
                    print(f"Unknown sub-parameter {inner_param_sn}")
                    continue
                if not isinstance(inner_param_value, str):
                    print(f"The value specified for parameter {inner_param_sn} is not a string")
                    continue

                typed_dict[inner_param_sn] = _convert_string_to_odx_type(
                    inner_param_value, inner_param.physical_type.base_data_type)
            parameter_values[parameter.short_name] = typed_dict
        else:
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

    payload = sub_service.encode(coded_request=b'\xff' * 100, **parameter_values)

    print(f"Message payload: 0x{bytes(payload).hex()}")


def browse(odxdb: Database) -> None:
    if sys.__stdin__ is None or sys.__stdout__ is None or not sys.__stdin__.isatty(
    ) or not sys.__stdout__.isatty():
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
        answer = IP_prompt(selection)
        if answer.get("variant") == "[exit]":
            return

        variant_name = answer.get("variant")
        assert isinstance(variant_name, str)
        variant = odxdb.diag_layers[variant_name]
        print(f"{type(answer.get('variant'))=}")
        assert isinstance(variant, DiagLayer)

        if isinstance(variant, HierarchyElement):
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
            answer = IP_prompt(selection)
            if answer.get("service") == "[back]":
                break

            service_sn = answer.get("service")
            assert isinstance(service_sn, str)

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
            answer = IP_prompt(selection)
            if answer.get("message_type") == "[back]":
                continue

            codec = answer.get("message_type")
            if codec is not None:
                assert isinstance(codec, (Request, Response))
                table = extract_parameter_tabulation_data(codec.parameters)
                print(table)

                encode_message_interactively(codec, ask_user_confirmation=True)


def add_subparser(subparsers: SubparsersList) -> None:
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
