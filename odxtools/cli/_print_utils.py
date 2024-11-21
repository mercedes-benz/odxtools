# SPDX-License-Identifier: MIT
import re
import textwrap
from typing import List, Optional, Tuple, Union

import markdownify
from rich import print as rich_print
from rich.padding import Padding as RichPadding
from rich.table import Table as RichTable

from ..description import Description
from ..diaglayers.diaglayer import DiagLayer
from ..diagservice import DiagService
from ..parameters.codedconstparameter import CodedConstParameter
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.parameter import Parameter
from ..parameters.physicalconstantparameter import PhysicalConstantParameter
from ..parameters.systemparameter import SystemParameter
from ..parameters.valueparameter import ValueParameter
from ..singleecujob import SingleEcuJob


def format_desc(description: Description, indent: int = 0) -> str:
    # Collapse whitespaces
    desc = re.sub(r"\s+", " ", str(description))
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
                             allow_unknown_bit_lengths: bool = False) -> None:

    rich_print(f" Service '{service.short_name}':")

    if service.description:
        desc = format_desc(service.description, indent=3)
        rich_print(f"  Description: " + desc)

    if print_pre_condition_states and len(service.pre_condition_states) > 0:
        pre_condition_states_short_names = [
            pre_condition_state.short_name for pre_condition_state in service.pre_condition_states
        ]
        rich_print(f"  Pre-Condition States: {', '.join(pre_condition_states_short_names)}")

    if print_state_transitions and len(service.state_transitions) > 0:
        state_transitions = [
            f"{state_transition.source_snref} -> {state_transition.target_snref}"
            for state_transition in service.state_transitions
        ]
        rich_print(f"  State Transitions: {', '.join(state_transitions)}")

    if print_audiences and service.audience:
        enabled_audiences_short_names = [
            enabled_audience.short_name for enabled_audience in service.audience.enabled_audiences
        ]
        rich_print(f"  Enabled Audiences: {', '.join(enabled_audiences_short_names)}")

    if print_params:
        print_service_parameters(service, allow_unknown_bit_lengths=allow_unknown_bit_lengths)


def print_service_parameters(service: DiagService,
                             *,
                             allow_unknown_bit_lengths: bool = False) -> None:
    # prints parameter details of request, positive response and
    # negative response of diagnostic service

    # Request
    if service.request:
        rich_print(f"  Request '{service.request.short_name}':")
        const_prefix = service.request.coded_const_prefix()
        rich_print(
            f"    Identifying Prefix: 0x{const_prefix.hex().upper()} ({bytes(const_prefix)!r})")
        rich_print(f"    Parameters:")
        param_table = extract_parameter_tabulation_data(service.request.parameters)
        rich_print(RichPadding(param_table, pad=(0, 0, 0, 4)))
        rich_print()
    else:
        rich_print(f"  No Request!")

    # Positive Responses
    if not service.positive_responses:
        rich_print(f"  No positive responses")

    for resp in service.positive_responses:
        rich_print(f"  Positive Response '{resp.short_name}':")
        rich_print(f"   Parameters:\n")
        table = extract_parameter_tabulation_data(list(resp.parameters))
        rich_print(RichPadding(table, pad=(0, 0, 0, 4)))
        rich_print()

    # Negative Response
    if not service.negative_responses:
        rich_print(f"  No negative responses")

    for resp in service.negative_responses:
        rich_print(f" Negative Response '{resp.short_name}':")
        rich_print(f"   Parameters:\n")
        table = extract_parameter_tabulation_data(list(resp.parameters))
        rich_print(RichPadding(table, pad=(0, 0, 0, 4)))
        rich_print()

    rich_print("\n")


def extract_service_tabulation_data(services: List[DiagService],
                                    *,
                                    additional_columns: Optional[List[Tuple[str, List[str]]]] = None
                                   ) -> RichTable:
    """Extracts data of diagnostic services into Dictionary which can
    be printed by tabulate module
    """

    # Create Rich table
    table = RichTable(
        title="", show_header=True, header_style="bold cyan", border_style="blue", show_lines=True)

    name_column: List[str] = []
    semantic_column: List[str] = []
    request_column: List[str] = []

    for service in services:
        name_column.append(service.short_name)
        semantic_column.append(service.semantic or "")

        if service.request:
            prefix = service.request.coded_const_prefix()
            request_column.append(f"0x{str(prefix.hex().upper())[:32]}...") if len(
                prefix) > 32 else request_column.append(f"0x{str(prefix.hex().upper())}")
        else:
            request_column.append("")

    table.add_column("Name", style="green")
    table.add_column("Semantic", justify="left", style="white")
    table.add_column("Request", justify="left", style="white")
    if additional_columns is not None:
        for ac_title, _ in additional_columns:
            table.add_column(ac_title, justify="left", style="white")

        rows = zip(name_column, semantic_column, request_column,
                   *[ac[1] for ac in additional_columns])
        for row in rows:
            table.add_row(*map(str, row))

    return table


def extract_parameter_tabulation_data(parameters: List[Parameter]) -> RichTable:
    # extracts data of parameters of diagnostic services into
    # a RichTable object that can be printed

    # Create Rich table
    table = RichTable(
        title="", show_header=True, header_style="bold cyan", border_style="blue", show_lines=True)

    # Add columns with appropriate styling
    table.add_column("Name", style="green")
    table.add_column("Byte Position", justify="right", style="yellow")
    table.add_column("Bit Length", justify="right", style="yellow")
    table.add_column("Semantic", justify="left", style="white")
    table.add_column("Parameter Type", justify="left", style="white")
    table.add_column("Data Type", justify="left", style="white")
    table.add_column("Value", justify="left", style="yellow")
    table.add_column("Value Type", justify="left", style="white")
    table.add_column("Linked DOP", justify="left", style="white")

    name_column: List[str] = []
    byte_column: List[str] = []
    bit_length_column: List[str] = []
    semantic_column: List[str] = []
    param_type_column: List[str] = []
    value_column: List[str] = []
    value_type_column: List[str] = []
    data_type_column: List[str] = []
    dop_column: List[str] = []

    for param in parameters:
        name_column.append(param.short_name)
        byte_column.append("" if param.byte_position is None else str(param.byte_position))
        semantic_column.append(param.semantic or "")
        param_type_column.append(param.parameter_type)
        length = 0
        if param.get_static_bit_length() is not None:
            n = param.get_static_bit_length()
            bit_length_column.append("" if n is None else str(n))
            length = (n or 0) // 4
        else:
            bit_length_column.append("")
        if isinstance(param, CodedConstParameter):
            if isinstance(param.coded_value, int):
                value_column.append(f"0x{param.coded_value:0{length}X}")
            elif isinstance(param.coded_value, bytes) or isinstance(param.coded_value, bytearray):
                value_column.append(f"0x{param.coded_value.hex().upper()}")
            else:
                value_column.append(f"{param.coded_value!r}")
            data_type_column.append(param.diag_coded_type.base_data_type.name)
            value_type_column.append('coded value')
            dop_column.append("")
        elif isinstance(param, NrcConstParameter):
            data_type_column.append(param.diag_coded_type.base_data_type.name)
            value_column.append(str(param.coded_values))
            value_type_column.append('coded values')
            dop_column.append("")
        elif isinstance(param, (PhysicalConstantParameter, SystemParameter, ValueParameter)):
            # this is a hack to make this routine work for parameters
            # which reference DOPs of a type that a is not yet
            # internalized. (all parameter objects of the tested types
            # are supposed to have a DOP.)
            param_dop = getattr(param, "_dop", None)

            if param_dop is not None:
                dop_column.append(param_dop.short_name)

            if param_dop is not None and (phys_type := getattr(param, "physical_type",
                                                               None)) is not None:
                data_type_column.append(phys_type.base_data_type.name)
            else:
                data_type_column.append("")
            if isinstance(param, PhysicalConstantParameter):
                if isinstance(param.physical_constant_value, bytes) or isinstance(
                        param.physical_constant_value, bytearray):
                    value_column.append(f"0x{param.physical_constant_value.hex().upper()}")
                else:
                    value_column.append(f"{param.physical_constant_value!r}")
                value_type_column.append('constant value')
            elif isinstance(param, ValueParameter) and param.physical_default_value is not None:
                if isinstance(param.physical_default_value, bytes) or isinstance(
                        param.physical_default_value, bytearray):
                    value_column.append(f"0x{param.physical_default_value.hex().upper()}")
                else:
                    value_column.append(f"{param.physical_default_value!r}")
                value_type_column.append('default value')
            else:
                value_column.append("")
                value_type_column.append("")
        else:
            value_column.append("")
            data_type_column.append("")
            value_type_column.append("")
            dop_column.append("")

    # Add all rows at once by zipping dictionary values
    rows = zip(name_column, byte_column, bit_length_column, semantic_column, param_type_column,
               data_type_column, value_column, value_type_column, dop_column)
    for row in rows:
        table.add_row(*map(str, row))

    return table


def print_dl_metrics(variants: List[DiagLayer]) -> None:
    """
    Print diagnostic layer metrics using Rich tables.
    Args:
        variants: List of diagnostic layer variants to analyze
    """
    # Create Rich table
    table = RichTable(
        title="", show_header=True, header_style="bold cyan", border_style="blue", show_lines=True)

    # Add columns with appropriate styling
    table.add_column("Name", style="green")
    table.add_column("Variant Type", style="magenta")
    table.add_column("Number of Services", justify="right", style="yellow")
    table.add_column("Number of DOPs", justify="right", style="yellow")
    table.add_column("Number of communication parameters", justify="right", style="yellow")

    # Process each variant
    for variant in variants:
        assert isinstance(variant, DiagLayer)
        all_services: List[Union[DiagService, SingleEcuJob]] = sorted(
            variant.services, key=lambda x: x.short_name)
        ddds = variant.diag_data_dictionary_spec

        # Add row to table
        table.add_row(variant.short_name, variant.variant_type.value, str(len(all_services)),
                      str(len(ddds.data_object_props)),
                      str(len(getattr(variant, "comparams_refs", []))))
    rich_print(table)
