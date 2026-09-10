# SPDX-License-Identifier: MIT
import argparse
import logging
import sys
from typing import Any, cast

from InquirerPy.resolver import prompt as IP_prompt
from InquirerPy.resolver import question_mapping
from rich import print as rich_print

from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diaglayers.diaglayer import DiagLayer
from ..diaglayers.hierarchyelement import HierarchyElement
from ..diagservice import DiagService
from ..dopbase import DopBase
from ..environmentdatadescription import EnvironmentDataDescription
from ..exceptions import OdxError, odxraise, odxrequire
from ..field import Field
from ..multiplexer import Multiplexer
from ..odxtypes import AtomicOdxType, DataType, ParameterValue, ParameterValueDict
from ..parameters.matchingrequestparameter import MatchingRequestParameter
from ..parameters.parameter import Parameter
from ..parameters.valueparameter import ValueParameter
from ..request import Request
from ..response import Response
from . import _browse_utils, _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import build_parameter_table

# name of the tool
_odxtools_tool_name_ = "browse"

question_mapping["list"] = _browse_utils._ListPromptWithCustomKeys


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


def _validate_chosen_value(input_val: ParameterValue, dop: DopBase, is_required: bool) -> bool:
    if not is_required and (input_val == "" or input_val is None):
        return True

    if isinstance(dop, DataObjectProperty):
        if isinstance(input_val, str):
            try:
                phys_type = odxrequire(dop.physical_type)
                converted_val = _convert_string_to_odx_type(input_val, phys_type.base_data_type)
            except (OdxError, ValueError, TypeError):
                return False
            return dop.is_valid_physical_value(converted_val)

        return dop.is_valid_physical_value(input_val)
    else:
        raise NotImplementedError(f"Validation of {dop.__class__.__name__} DOPs")


def prompt_primitive_parameter_value(parameter: ValueParameter,
                                     indent: str = "") -> AtomicOdxType | None:
    if parameter.physical_type is None:
        odxraise("Only ValueParameters which define a physical data type can be queried")
        return None

    dop = parameter.dop
    type_name = parameter.physical_type.base_data_type
    param_prompt = [{
        "type": "input",
        "name": parameter.short_name,
        "message": f"{indent}Value for parameter '{parameter.short_name}' "
                   f"(Type: {type_name})" + (" [optional]" if not parameter.is_required else ""),
        "validate": lambda x: _validate_chosen_value(x, dop, parameter.is_required),
    }]

    # determine the default value to pre-select if a list of choices is shown
    default_value: AtomicOdxType | None = parameter.physical_default_value
    if default_value is None and isinstance(dop, DataObjectProperty):
        internal_to_phys = dop.compu_method.compu_internal_to_phys
        if internal_to_phys is not None and internal_to_phys.compu_default_value is not None:
            default_value = internal_to_phys.compu_default_value.value

    # if the parameter is a texttable, list the possible choices
    if (compu_method := getattr(dop, "compu_method", None)) is not None and \
       (citp := getattr(compu_method, "compu_internal_to_phys", None)) is not None:

        texttable_choices: list[dict[str, Any]] = [
            {
                "name": scale.compu_const.value,
                "value": scale.compu_const.value,
            }
            for scale in citp.compu_scales
            if scale.compu_const is not None and scale.compu_const.value is not None
        ]

        if (cdv := citp.compu_default_value) is not None and cdv.value is not None:
            texttable_choices.append({
                "name": f"[default] ({cdv.value})",
                "value": cdv.value,
            })
            param_prompt[0]["default"] = cdv.value

        if texttable_choices:
            param_prompt[0]["type"] = "list"
            param_prompt[0]["choices"] = texttable_choices

    # query user for answer
    answer = IP_prompt(param_prompt)
    raw_answer = answer.get(parameter.short_name)

    if raw_answer in ("", None):
        if raw_answer == "" and parameter.is_required:
            # For required parameters, an empty input represents the empty
            # value of the parameter's data type (e.g., b'' for byte fields).
            if parameter.physical_type.base_data_type is not None:
                try:
                    return _convert_string_to_odx_type("", parameter.physical_type.base_data_type)
                except (OdxError, ValueError, TypeError):
                    return None
            return None

        # For optional parameters, determine the default value and ask
        # the user whether they meant the default or the empty value.
        if isinstance(dop, DataObjectProperty):
            try:
                empty_phys_val = _convert_string_to_odx_type("",
                                                             parameter.physical_type.base_data_type)
            except (OdxError, ValueError, TypeError):
                empty_phys_val = None

            if empty_phys_val != default_value:
                # ask user if they mean the default or the empty value
                message_prompt = [{
                    "type":
                        "list",
                    "name":
                        "default_empty_prompt",
                    "message":
                        f"Do you want to use the parameter's default value ({default_value!r}) or the empty value?",
                    "choices": ["default", "empty"],
                }]
                answer = IP_prompt(message_prompt)
                if answer.get("default_empty_prompt") == "default":
                    return None
                else:
                    return empty_phys_val

            return empty_phys_val

        return None
    elif not isinstance(raw_answer, str):
        return cast(AtomicOdxType, raw_answer)
    elif parameter.physical_type.base_data_type is not None:
        return _convert_string_to_odx_type(raw_answer, parameter.physical_type.base_data_type)
    else:
        logging.warning(f"Parameter {parameter.short_name} does not have a physical data type.")
        return cast(str, raw_answer)


def prompt_all_parameter_values(params: list[Parameter], indent: str = "") -> ParameterValueDict:
    """Query the user for the values of all settable parameters of a list of parameters
    """

    param_values: ParameterValueDict = {}
    for param in params:
        if isinstance(param, ValueParameter):
            dop = param.dop
            if isinstance(dop, Field):
                odxraise("Encoding field parameters is currently not supported")
            elif isinstance(dop, Multiplexer):
                odxraise("Encoding multiplexer parameters is currently not supported")
            elif isinstance(dop, EnvironmentDataDescription):
                odxraise(
                    "Encoding environment data description parameters is currently not supported")
            elif (inner_params := getattr(dop, "parameters", None)) is not None:
                # param refers to a complex DOP, i.e., the required
                # value is a key-value dict
                inner_params = cast(list[Parameter], inner_params)
                rich_print(f"{indent}Parameters for structure '{dop.short_name}':")

                complex_val = prompt_all_parameter_values(inner_params, indent=indent + "  ")
                param_values[param.short_name] = complex_val

            elif param.is_settable:
                primitive_val = prompt_primitive_parameter_value(param, indent)
                if primitive_val is not None:
                    param_values[param.short_name] = primitive_val

    return param_values


def encode_message_interactively(codec: Request | Response,
                                 ask_user_confirmation: bool = False) -> None:
    if sys.__stdin__ is None or sys.__stdout__ is None or not sys.__stdin__.isatty(
    ) or not sys.stdout.isatty():
        raise SystemError("This command can only be used in an interactive shell!")

    def has_settable_or_matching_request_param(params: list[Parameter]) -> tuple[bool, bool]:
        has_settable_param = False
        has_matching_request_param = False
        for param in params:
            if param.is_settable:
                has_settable_param = True
            if isinstance(param, MatchingRequestParameter):
                has_matching_request_param = True

            # check nested parameters
            dop = getattr(param, "dop", None)
            inner_params = getattr(dop, "parameters", None)
            if inner_params is not None:
                inner_settable, inner_matching = \
                    has_settable_or_matching_request_param(inner_params)
                has_settable_param = has_settable_param or inner_settable
                has_matching_request_param = has_matching_request_param or inner_matching

        return has_settable_param, has_matching_request_param

    has_settable_param, has_matching_request_param = \
        has_settable_or_matching_request_param(codec.parameters)

    param_values: ParameterValueDict = {}
    answered_request = b''
    if has_settable_param:
        # Ask whether user wants to encode a message
        if ask_user_confirmation:
            encode_message_prompt = [{
                "type": "list",
                "name": "yes_no_prompt",
                "message": f"Do you want to encode a message?",
                "choices": ["yes", "no"],
            }]
            answer = IP_prompt(encode_message_prompt)
            if answer.get("yes_no_prompt") == "no":
                return

        # if the user wants to encode a message for a response and the
        # response contains a matching request parameter, we need the
        # corresponding request
        if isinstance(codec, Response):
            answered_request_prompt = [{
                "type": "input",
                "name": "request",
                "message":
                    "What is the request you want to answer? "
                    "(Enter the coded request as integer in hexadecimal format (e.g. 12 3B 05)",
                "filter": lambda input: _convert_string_to_bytes(input),
            }]
            answer = IP_prompt(answered_request_prompt)
            answered_request = cast(bytes, answer.get("request"))
            rich_print(f"Input interpretation as list: {list(answered_request)}")

        param_values = prompt_all_parameter_values(codec.parameters)

        if isinstance(codec, Response):
            payload = codec.encode(coded_request=answered_request, **param_values)
        else:
            payload = codec.encode(**param_values)
    else:
        # There are no settable parameters -> Just print message
        if isinstance(codec, Response):
            payload = codec.encode(coded_request=answered_request)
        else:
            payload = codec.encode()

    rich_print(f"Message payload: 0x{bytes(payload).hex()}")


def browse(odxdb: Database) -> None:
    if sys.__stdin__ is None or sys.__stdout__ is None or not sys.__stdin__.isatty(
    ) or not sys.stdout.isatty():
        raise SystemError("This command can only be used in an interactive shell!")
    dl_names = sorted([dl.short_name for dl in odxdb.diag_layers], key=str.lower)
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
        assert isinstance(variant, DiagLayer)

        if isinstance(variant, HierarchyElement):
            if (rx_id := variant.get_can_receive_id()) is not None:
                recv_id = hex(rx_id)
            else:
                recv_id = "None"

            if (tx_id := variant.get_can_send_id()) is not None:
                send_id = hex(tx_id)
            else:
                send_id = "None"

            rich_print(
                f"{variant.variant_type.value} '{variant.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
            )

        while True:
            services: list[DiagService] = [
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
                "choices":
                    sorted([s.short_name for s in services], key=str.lower) + ["[back]"],
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
                table = build_parameter_table(codec.parameters)
                rich_print(table)

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
