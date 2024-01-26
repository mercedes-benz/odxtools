# SPDX-License-Identifier: MIT
import re
import textwrap
from typing import Any, Callable, Dict, List, Optional, Union

import markdownify
from tabulate import tabulate  # TODO: switch to rich tables

from ..diaglayer import DiagLayer
from ..diagservice import DiagService
from ..parameters.codedconstparameter import CodedConstParameter
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.parameter import Parameter
from ..parameters.physicalconstantparameter import PhysicalConstantParameter
from ..parameters.systemparameter import SystemParameter
from ..parameters.valueparameter import ValueParameter
from ..singleecujob import SingleEcuJob


def format_desc(desc: str, indent: int = 0) -> str:
    # Collapse whitespaces
    desc = re.sub(r"\s+", " ", desc)
    # Covert XHTML to Markdown
    desc = markdownify.markdownify(desc)
    # Collapse blank lines
    desc = re.sub(r"(\n\s*)+\n+", "\n", desc).strip()
    # add indentation
    desc = textwrap.indent(desc, " " * indent)

    return desc


def print_diagnostic_service(service: DiagService,
                             print_params: bool = False,
                             print_pre_condition_states: bool = False,
                             print_state_transitions: bool = False,
                             print_audiences: bool = False,
                             allow_unknown_bit_lengths: bool = False,
                             print_fn: Callable = print) -> None:

    print_fn(f" Service '{service.short_name}':")

    if service.description:
        desc = format_desc(service.description, indent=3)
        print_fn(f"  Description: " + desc)

    if print_pre_condition_states and len(service.pre_condition_states) > 0:
        pre_condition_states_short_names = [
            pre_condition_state.short_name for pre_condition_state in service.pre_condition_states
        ]
        print_fn(f"  Pre-Condition States: {', '.join(pre_condition_states_short_names)}")

    if print_state_transitions and len(service.state_transitions) > 0:
        state_transitions = [
            f"{state_transition.source_snref} -> {state_transition.target_snref}"
            for state_transition in service.state_transitions
        ]
        print_fn(f"  State Transitions: {', '.join(state_transitions)}")

    if print_audiences and service.audience:
        enabled_audiences_short_names = [
            enabled_audience.short_name for enabled_audience in service.audience.enabled_audiences
        ]
        print_fn(f"  Enabled Audiences: {', '.join(enabled_audiences_short_names)}")

    if print_params:
        print_service_parameters(
            service, allow_unknown_bit_lengths=allow_unknown_bit_lengths, print_fn=print_fn)


def print_service_parameters(service: DiagService,
                             allow_unknown_bit_lengths: bool = False,
                             print_fn: Callable = print) -> None:
    # prints parameter details of request, positive response and negative response of diagnostic service

    # Request
    if service.request:
        print_fn(f"  Request '{service.request.short_name}':")
        const_prefix = service.request.coded_const_prefix()
        print_fn(
            f"    Identifying Prefix: 0x{const_prefix.hex().upper()} ({bytes(const_prefix)!r})")
        print_fn(f"    Parameters:")
        table = extract_parameter_tabulation_data(list(service.request.parameters))
        table_str = textwrap.indent(tabulate(table, headers='keys', tablefmt='presto'), "    ")
        print_fn()
        print_fn(table_str)
        print_fn()
    else:
        print_fn(f"  No Request!")

    # Positive Responses
    if not service.positive_responses:
        print_fn(f"  No positive responses")

    for resp in service.positive_responses:
        print_fn(f"  Positive Response '{resp.short_name}':")
        print_fn(f"   Parameters:\n")
        table = extract_parameter_tabulation_data(list(resp.parameters))
        table_str = textwrap.indent(tabulate(table, headers='keys', tablefmt='presto'), "    ")
        print_fn(table_str)
        print_fn()

    # Negative Response
    if not service.negative_responses:
        print_fn(f"  No negative responses")

    for resp in service.negative_responses:
        print_fn(f" Negative Response '{resp.short_name}':")
        print_fn(f"   Parameters:\n")
        table = extract_parameter_tabulation_data(list(resp.parameters))
        table_str = textwrap.indent(tabulate(table, headers='keys', tablefmt='presto'), "    ")
        print_fn(table_str)
        print_fn()

    print_fn("\n")


def extract_service_tabulation_data(services: List[DiagService]) -> Dict[str, Any]:
    # extracts data of diagnostic services into Dictionary which can be printed by tabulate module
    # TODO: consider indentation

    name = []
    semantic = []
    request: List[Optional[str]] = []

    for service in services:
        name.append(service.short_name)
        semantic.append(service.semantic)

        if service.request:
            prefix = service.request.coded_const_prefix()
            request.append(f"0x{str(prefix.hex().upper())[:32]}...") if len(
                prefix) > 32 else request.append(f"0x{str(prefix.hex().upper())}")
        else:
            request.append(None)

    return {'Name': name, 'Semantic': semantic, 'Hex-Request': request}


def extract_parameter_tabulation_data(parameters: List[Parameter]) -> Dict[str, Any]:
    # extracts data of parameters of diagnostic services into Dictionary which can be printed by tabulate module
    # TODO: consider indentation

    name = []
    byte = []
    bit_length: List[Optional[int]] = []
    semantic = []
    param_type = []
    value: List[Optional[str]] = []
    value_type: List[Optional[str]] = []
    data_type: List[Optional[str]] = []
    dop: List[Optional[str]] = []

    for param in parameters:
        name.append(param.short_name)
        byte.append(param.byte_position)
        semantic.append(param.semantic)
        param_type.append(param.parameter_type)
        if param.get_static_bit_length() is not None:
            bit_length.append(param.get_static_bit_length())
            length = (param.get_static_bit_length() or 0) // 4
        else:
            bit_length.append(None)
        if isinstance(param, CodedConstParameter):
            if isinstance(param.coded_value, int):
                value.append(f"0x{param.coded_value:0{length}X}")
            elif isinstance(param.coded_value, bytes) or isinstance(param.coded_value, bytearray):
                value.append(f"0x{param.coded_value.hex().upper()}")
            else:
                value.append(f"{param.coded_value!r}")
            data_type.append(param.diag_coded_type.base_data_type.name)
            value_type.append('coded value')
            dop.append(None)
        elif isinstance(param, NrcConstParameter):
            data_type.append(param.diag_coded_type.base_data_type.name)
            value.append(str(param.coded_values))
            value_type.append('coded values')
            dop.append(None)
        elif isinstance(param, (PhysicalConstantParameter, SystemParameter, ValueParameter)):
            # this is a hack to make this routine work for parameters
            # which reference DOPs of a type that a is not yet
            # internalized. (all parameter objects of the tested types
            # are supposed to have a DOP.)
            param_dop = getattr(param, "_dop", None)

            if param_dop is not None:
                dop.append(param_dop.short_name)

            if param_dop is not None and (phys_type := getattr(param, "physical_type",
                                                               None)) is not None:
                data_type.append(phys_type.base_data_type.name)
            else:
                data_type.append(None)
            if isinstance(param, PhysicalConstantParameter):
                if isinstance(param.physical_constant_value, bytes) or isinstance(
                        param.physical_constant_value, bytearray):
                    value.append(f"0x{param.physical_constant_value.hex().upper()}")
                else:
                    value.append(f"{param.physical_constant_value!r}")
                value_type.append('constant value')
            elif isinstance(param, ValueParameter) and param.physical_default_value is not None:
                if isinstance(param.physical_default_value, bytes) or isinstance(
                        param.physical_default_value, bytearray):
                    value.append(f"0x{param.physical_default_value.hex().upper()}")
                else:
                    value.append(f"{param.physical_default_value!r}")
                value_type.append('default value')
            else:
                value.append(None)
                value_type.append(None)
        else:
            value.append(None)
            data_type.append(None)
            value_type.append(None)
            dop.append(None)

    return {
        'Name': name,
        'Byte Position': byte,
        'Bit Length': bit_length,
        'Semantic': semantic,
        'Parameter Type': param_type,
        'Data Type': data_type,
        'Value': value,
        'Value Type': value_type,
        'Linked DOP': dop
    }


def print_dl_metrics(variants: List[DiagLayer], print_fn: Callable = print) -> None:

    name = []
    type = []
    num_services = []
    num_dops = []
    num_comparams = []
    for variant in variants:
        assert isinstance(variant, DiagLayer)
        all_services: List[Union[DiagService, SingleEcuJob]] = sorted(
            variant.services, key=lambda x: x.short_name)
        name.append(variant.short_name)
        type.append(variant.variant_type.value)
        num_services.append(len(all_services))
        num_dops.append(len(variant.diag_data_dictionary_spec.data_object_props))
        num_comparams.append(len(variant.comparams))

    table = {
        'Name': name,
        'Variant Type': type,
        'Number of Services': num_services,
        'Number of DOPs': num_dops,
        'Number of communication parameters': num_comparams
    }
    print_fn(tabulate(table, headers='keys', tablefmt='presto'))
