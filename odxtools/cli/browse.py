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
from ..diagnostictroublecode import DiagnosticTroubleCode
from ..diagservice import DiagService
from ..dopbase import DopBase
from ..dtcdop import DtcDop
from ..environmentdata import EnvironmentData
from ..environmentdatadescription import EnvironmentDataDescription
from ..exceptions import OdxError, odxraise, odxrequire
from ..field import Field
from ..multiplexer import Multiplexer
from ..multiplexercase import MultiplexerCase
from ..multiplexerdefaultcase import MultiplexerDefaultCase
from ..odxlink import resolve_snref
from ..odxtypes import AtomicOdxType, DataType, ParameterValue, ParameterValueDict
from ..parameters.matchingrequestparameter import MatchingRequestParameter
from ..parameters.parameter import Parameter
from ..parameters.tablekeyparameter import TableKeyParameter
from ..parameters.tablestructparameter import TableStructParameter
from ..parameters.valueparameter import ValueParameter
from ..request import Request
from ..response import Response
from ..staticfield import StaticField
from ..structure import Structure
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

    if isinstance(dop, DtcDop):
        if isinstance(input_val, DiagnosticTroubleCode) or any(
                dtc.short_name == input_val for dtc in dop.dtcs):
            return True

        # DTC specified as display_trouble_code
        if any(dtc.display_trouble_code == input_val for dtc in dop.dtcs):
            return True

        # DTC specified as numeric value?
        if isinstance(input_val, (int, float)):
            trouble_code = int(input_val)
        else:
            assert isinstance(input_val, str)
            try:
                trouble_code = int(input_val, 0)
            except ValueError:
                return False
        return any(dtc.trouble_code == trouble_code for dtc in dop.dtcs)

    elif isinstance(dop, DataObjectProperty):
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
    type_name = "DTC" if isinstance(dop, DtcDop) else parameter.physical_type.base_data_type
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

    # if the parameter refers to a DTC-DOP, list the available DTCs
    if isinstance(dop, DtcDop) and len(dop.dtcs) > 0:
        dtc_choices: list[dict[str, Any]] = [{
            "name": f"{dtc.short_name} (0x{dtc.trouble_code:06x}): {dtc.text}",
            "value": dtc,
        } for dtc in dop.dtcs]
        if not parameter.is_required:
            dtc_choices.insert(0, {"name": "[none]", "value": None})

        param_prompt[0]["type"] = "list"
        param_prompt[0]["choices"] = dtc_choices

        # pre-select the default DTC if available
        if isinstance(default_value, int):
            for dtc in dop.dtcs:
                if dtc.trouble_code == default_value:
                    param_prompt[0]["default"] = dtc
                    break

    # if the parameter is a texttable, list the possible choices
    elif (compu_method := getattr(dop, "compu_method", None)) is not None and \
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
    elif isinstance(raw_answer, DiagnosticTroubleCode):
        return raw_answer.trouble_code
    elif not isinstance(raw_answer, str):
        return cast(AtomicOdxType, raw_answer)
    elif parameter.physical_type.base_data_type is not None:
        return _convert_string_to_odx_type(raw_answer, parameter.physical_type.base_data_type)
    else:
        logging.warning(f"Parameter {parameter.short_name} does not have a physical data type.")
        return cast(str, raw_answer)


def prompt_field_parameter_value(parameter: ValueParameter,
                                 indent: str = "") -> list[ParameterValueDict]:
    """Query the user for the value of a parameter that references a field."""
    dop = parameter.dop
    if not isinstance(dop, Field):
        odxraise(f"Expected a Field DOP for parameter '{parameter.short_name}'")
        return []

    structure = dop.structure
    inner_params = structure.parameters

    result: list[ParameterValueDict] = []
    if isinstance(dop, StaticField):
        n_items = dop.fixed_number_of_items
        for i in range(n_items):
            rich_print(f"{indent}Item {i + 1}/{n_items} of field '{parameter.short_name}'")
            item_val = prompt_all_parameter_values(inner_params, indent=indent + "  ")
            result.append(item_val)
        return result

    # dynamically-sized list of items
    min_items = getattr(dop, "min_number_of_items", None) or 0
    max_items = getattr(dop, "max_number_of_items", None)

    while True:
        i = len(result)
        rich_print(f"{indent}Item {i + 1} of field '{parameter.short_name}'")
        item_val = prompt_all_parameter_values(inner_params, indent=indent + "  ")
        result.append(item_val)

        if max_items is not None and len(result) >= max_items:
            break

        if len(result) >= min_items:
            add_another_prompt = [{
                "type": "list",
                "name": "add_another",
                "message": f"{indent}Add another item to field '{parameter.short_name}'?",
                "choices": ["yes", "no"],
                "default": "yes" if len(result) < min_items else "no",
            }]
            answer = IP_prompt(add_another_prompt)
            if answer.get("add_another") == "no":
                break

    return result


def prompt_env_data_desc_parameter_value(parameter: ValueParameter,
                                         sibling_params: list[Parameter],
                                         param_values: ParameterValueDict,
                                         indent: str = "") -> ParameterValueDict:
    """Query the user for the value of a parameter that references an environment data description."""
    dop = parameter.dop
    if not isinstance(dop, EnvironmentDataDescription):
        odxraise(
            f"Expected an EnvironmentDataDescription DOP for parameter '{parameter.short_name}'")
        return {}

    # Determine the environment data objects that are applicable for
    # the DTC value of the referenced parameter.
    applicable_env_datas: list[EnvironmentData] = dop.env_datas
    if dop.param_snpathref is not None:
        raise NotImplementedError(f"Specifying the DOP parameter via SNPATHREF in "
                                  f"environment data description '{parameter.short_name} "
                                  f"is not yet implemented.")

    if dop.param_snref is not None:
        dtc_param = resolve_snref(dop.param_snref, sibling_params, Parameter)
        if dtc_param is None:
            raise OdxError(f"Could not find parameter '{dop.param_snref}' referenced by "
                           f"environment data description '{dop.short_name}'")
        else:
            dtc_value = param_values.get(dop.param_snref)
            numerical_dtc = dop._get_numerical_dtc_from_parameter(dtc_param, dtc_value)
            applicable_env_datas = [
                ed for ed in dop.env_datas if ed.all_value or numerical_dtc in ed.dtc_values
            ]

    # Collect the union of all parameters of the applicable environment data objects.
    all_inner_params: list[Parameter] = []
    seen_param_names: set[str] = set()
    for env_data in applicable_env_datas:
        for inner_param in env_data.parameters:
            if inner_param.short_name not in seen_param_names:
                seen_param_names.add(inner_param.short_name)
                all_inner_params.append(inner_param)

    if all_inner_params:
        rich_print(f"{indent}Parameters for environment data description '{dop.short_name}':")

    return prompt_all_parameter_values(all_inner_params, indent=indent + "  ")


def prompt_multiplexer_parameter_value(parameter: ValueParameter,
                                       indent: str = "") -> tuple[str, ParameterValueDict]:
    """Query the user for the value of a parameter that references a multiplexer."""
    dop = parameter.dop
    if not isinstance(dop, Multiplexer):
        odxraise(f"Expected a Multiplexer DOP for parameter '{parameter.short_name}'")
        return ("", {})

    choices: list[str | dict[str, str]] = []
    for cur_mux_case in dop.cases:
        lower, upper = dop._get_case_limits(cur_mux_case)
        case_dop = cur_mux_case.structure
        assert case_dop is not None
        choices.append({
            "name": f"{cur_mux_case.short_name} ({case_dop.short_name})",
            "value": cur_mux_case.short_name,
        })
    if dop.default_case is not None:
        choices.append({
            "name": f"{dop.default_case.short_name} (default)",
            "value": dop.default_case.short_name,
        })

    if not choices:
        odxraise(f"Multiplexer '{dop.short_name}' does not contain any cases")
        return ("", {})

    prompt = [{
        "type": "list",
        "name": parameter.short_name,
        "message": f"{indent}Select case for multiplexer parameter '{parameter.short_name}'",
        "choices": choices,
    }]
    answer = IP_prompt(prompt)
    case_name = answer.get(parameter.short_name)
    if not isinstance(case_name, str):
        odxraise(f"Expected string case name, got {type(case_name).__name__}")
        return ("", {})

    candidate_cases = [c for c in dop.cases if c.short_name == case_name]
    mux_case: MultiplexerCase | MultiplexerDefaultCase
    if len(candidate_cases) == 1:
        mux_case = candidate_cases[0]
    elif dop.default_case is not None and dop.default_case.short_name == case_name:
        mux_case = dop.default_case
    else:
        odxraise(f"Could not find unique case '{case_name}' in multiplexer '{dop.short_name}'")
        return (case_name, {})

    case_value: ParameterValueDict
    if mux_case.structure is not None:
        rich_print(f"{indent}Parameters for case '{mux_case.short_name}':")
        case_value = prompt_all_parameter_values(
            mux_case.structure.parameters, indent=indent + "  ")
    else:
        case_value = {}

    return (case_name, case_value)


def prompt_table_key_parameter_value(parameter: TableKeyParameter, indent: str = "") -> str:
    """Query the user for the value of a table key parameter."""

    if parameter.table_row is not None:
        # the table row is statically specified
        return parameter.table_row.short_name

    table = parameter.table
    choices = [tr.short_name for tr in table.table_rows]
    if not choices:
        odxraise(f"Table '{table.short_name}' does not contain any rows")
        return ""

    prompt = [{
        "type": "list",
        "name": parameter.short_name,
        "message": f"{indent}Select table row for parameter '{parameter.short_name}'",
        "choices": choices,
    }]
    answer = IP_prompt(prompt)
    result = answer.get(parameter.short_name)
    if not isinstance(result, str):
        odxraise(f"Expected string table row name, got {type(result).__name__}")
        return ""
    return result


def prompt_table_struct_parameter_value(parameter: TableStructParameter,
                                        param_values: ParameterValueDict,
                                        indent: str = ""
                                       ) -> tuple[str, AtomicOdxType | ParameterValueDict]:
    """Query the user for the value of a table struct parameter."""

    table_key = parameter.table_key
    table = table_key.table

    # if the table key has a statically specified row, use it
    if table_key.table_row is not None:
        row_short_name = table_key.table_row.short_name
    else:
        # use the value of the corresponding table key parameter
        key_value = param_values.get(table_key.short_name)
        if not isinstance(key_value, str):
            odxraise(f"Cannot determine table row for parameter '{parameter.short_name}': "
                     f"No value has been specified for the associated table key "
                     f"'{table_key.short_name}'")
            return ("", {})
        row_short_name = key_value

    # find the selected table row
    candidate_rows = [tr for tr in table.table_rows if tr.short_name == row_short_name]
    if len(candidate_rows) != 1:
        odxraise(
            f"Could not find unique table row '{row_short_name}' in table '{table.short_name}'")
        return (row_short_name, {})
    table_row = candidate_rows[0]

    # prompt for the value of the row's structure or DOP
    row_value: AtomicOdxType | ParameterValueDict
    if table_row.structure is not None:
        rich_print(f"{indent}Parameters for table row '{table_row.short_name}':")
        row_value = prompt_all_parameter_values(
            table_row.structure.parameters, indent=indent + "  ")
    elif table_row.dop is not None:
        # the row references a simple DOP -> prompt for a primitive value
        row_dop = table_row.dop
        phys_type = row_dop.physical_type
        if phys_type is None:
            odxraise(f"Table row '{table_row.short_name}' does not have a physical type")
            return (row_short_name, {})

        param_prompt = [{
            "type": "input",
            "name": "row_value",
            "message": f"{indent}Value for table row '{table_row.short_name}' "
                       f"(Type: {phys_type.base_data_type})",
            "validate": lambda x: _validate_chosen_value(x, row_dop, is_required=True),
            "filter": lambda x: x,
        }]
        answer = IP_prompt(param_prompt)
        raw_answer = answer.get("row_value")
        if not isinstance(raw_answer, str):
            odxraise(f"Expected string value, got {type(raw_answer).__name__}")
            return (row_short_name, {})
        row_value = _convert_string_to_odx_type(raw_answer, phys_type.base_data_type)
    else:
        odxraise(f"Table row '{table_row.short_name}' does not reference a structure or a DOP")
        return (row_short_name, {})

    return (row_short_name, row_value)


def prompt_all_parameter_values(params: list[Parameter], indent: str = "") -> ParameterValueDict:
    """Query the user for the values of all settable parameters of a list of parameters
    """

    param_values: ParameterValueDict = {}
    for param in params:
        if isinstance(param, ValueParameter):
            dop = param.dop

            if isinstance(dop, Field):
                param_values[param.short_name] = prompt_field_parameter_value(param, indent)
            elif isinstance(dop, Multiplexer):
                param_values[param.short_name] = prompt_multiplexer_parameter_value(param, indent)
            elif isinstance(dop, EnvironmentDataDescription):
                param_values[param.short_name] = prompt_env_data_desc_parameter_value(
                    param, params, param_values, indent)
            elif isinstance(dop, Structure):
                # param uses a structure as its DOP, i.e., we need to
                # retrieve the values for it recursively
                inner_params = dop.parameters
                rich_print(f"{indent}Parameters belong for structure '{dop.short_name}':")

                val = prompt_all_parameter_values(inner_params, indent=indent + "  ")
                param_values[param.short_name] = val
            elif param.is_settable:
                primitive_val = prompt_primitive_parameter_value(param, indent)
                if primitive_val is not None:
                    param_values[param.short_name] = primitive_val

        elif isinstance(param, TableKeyParameter):
            param_values[param.short_name] = prompt_table_key_parameter_value(param, indent)

        elif isinstance(param, TableStructParameter):
            param_values[param.short_name] = prompt_table_struct_parameter_value(
                param, param_values, indent)

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
            if isinstance(dop, Field):
                inner_params = dop.structure.parameters
            elif isinstance(dop, EnvironmentDataDescription):
                inner_params = []
                seen_param_names: set[str] = set()
                for env_data in dop.env_datas:
                    for inner_param in env_data.parameters:
                        if inner_param.short_name not in seen_param_names:
                            seen_param_names.add(inner_param.short_name)
                            inner_params.append(inner_param)

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
    if has_settable_param or has_matching_request_param:
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

    answered_request = b""
    if has_matching_request_param:
        # if the user wants to encode a message for a response and the
        # response contains a matching request parameter, we need the
        # corresponding request
        answered_request_prompt = [{
            "type": "input",
            "name": "request",
            "message": "What is the request you want to answer? "
                       "(Enter the coded request as integer in hexadecimal format (e.g. 12 3B 05)",
            "filter": lambda input: _convert_string_to_bytes(input),
        }]
        answer = IP_prompt(answered_request_prompt)
        answered_request = cast(bytes, answer.get("request"))
        rich_print(f"Input interpretation as list: {list(answered_request)}")

    param_values = {}
    if has_settable_param:
        param_values = prompt_all_parameter_values(codec.parameters)

    if isinstance(codec, Response):
        payload = codec.encode(coded_request=answered_request, **param_values)
    else:
        payload = codec.encode(**param_values)

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
