#!/usr/bin/env python
# SPDX-License-Identifier: MIT

import argparse
import os
from dataclasses import dataclass, field
from typing import Optional

from rich import print as rich_print
from rich.padding import Padding as RichPadding
from rich.table import Table as RichTable

from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diaglayers.diaglayer import DiagLayer
from ..diagservice import DiagService
from ..dtcdop import DtcDop
from ..loadfile import load_file
from ..odxtypes import AtomicOdxType
from ..parameters.codedconstparameter import CodedConstParameter
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.parameter import Parameter
from ..parameters.parameterwithdop import ParameterWithDOP
from ..parameters.physicalconstantparameter import PhysicalConstantParameter
from ..parameters.valueparameter import ValueParameter
from . import _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import build_service_table, print_dl_metrics, print_service_parameters

# name of the tool
_odxtools_tool_name_ = "compare"


@dataclass
class ParameterAttributeChanges:
    attribute: str
    old_value: Optional[AtomicOdxType] = field(default=None)
    new_value: Optional[AtomicOdxType] = field(default=None)


@dataclass
class ParameterChanges:
    description: str  # description of change
    changed_attributes: list[ParameterAttributeChanges] = field(
        default_factory=list)  # detailed information on changed attribute of parameter


@dataclass
class ServiceChanges:
    service: DiagService  # The service whose parameters have changed
    changed_parameters_of_service: list[ParameterChanges] = field(default_factory=list)


@dataclass
class RenamedService:
    old_service_name: str
    new_service_name: str
    new_service_object: DiagService


@dataclass
class DiagLayerChanges:
    diag_layer: str
    diag_layer_type: str
    new_services: list[DiagService] = field(default_factory=list)
    deleted_services: list[DiagService] = field(default_factory=list)
    renamed_services: list[RenamedService] = field(default_factory=list)
    services_with_parameter_changes: list[ServiceChanges] = field(default_factory=list)


@dataclass
class SpecsChangesVariants:
    new_diagnostic_layers: list[DiagLayer] = field(default_factory=list)
    deleted_diagnostic_layers: list[DiagLayer] = field(default_factory=list)
    changed_diagnostic_layers: list[DiagLayerChanges] = field(default_factory=list)


class Display:

    detailed: bool

    def __init__(self) -> None:
        pass

    def print_dl_overview(self, filename: str, dls: list[DiagLayer]) -> None:
        rich_print()
        rich_print(f"Overview of diagnostic layers (in [orange1]{filename}[/orange1])")
        print_dl_metrics(dls)

    def print_dl_changes(self, service_spec: DiagLayerChanges) -> None:
        if service_spec.new_services or service_spec.deleted_services or service_spec.renamed_services or service_spec.services_with_parameter_changes:
            assert isinstance(service_spec.diag_layer, str)
            rich_print()
            rich_print(
                f"[blue]Changed diagnostic services[/blue] of diagnostic layer [green3]'{service_spec.diag_layer}'[/green3] [medium_spring_green]({service_spec.diag_layer_type})[/medium_spring_green]:"
            )
        if service_spec.new_services:
            assert isinstance(service_spec.new_services, list)
            rich_print()
            rich_print(" [blue]New services[/blue]")
            rich_print(build_service_table(service_spec.new_services))
        if service_spec.deleted_services:
            assert isinstance(service_spec.deleted_services, list)
            rich_print()
            rich_print(" [blue]Deleted services[/blue]")
            rich_print(build_service_table(service_spec.deleted_services))
        if service_spec.renamed_services:
            assert isinstance(service_spec.renamed_services, list)
            rich_print()
            rich_print(" [blue]Renamed services[/blue]")
            services = [item.new_service_object for item in service_spec.renamed_services]
            old_names = [item.old_service_name for item in service_spec.renamed_services]
            rich_print(
                build_service_table(
                    services=services, additional_columns=[("Old service name", old_names)]))
        if service_spec.services_with_parameter_changes:
            assert isinstance(service_spec.services_with_parameter_changes, list)
            rich_print()
            rich_print(" [blue]Services with parameter changes[/blue]")
            services = [item.service for item in service_spec.services_with_parameter_changes]
            changed_param_column = [
                f"\n".join(
                    [item.description
                     for item in changed_params.changed_parameters_of_service])
                for changed_params in service_spec.services_with_parameter_changes
            ]

            table = build_service_table(
                services=services,
                additional_columns=[("Changed Parameters", changed_param_column)])
            rich_print(RichPadding(table, pad=(0, 0, 0, 1)))

            for item in service_spec.services_with_parameter_changes:
                assert isinstance(item, ServiceChanges)
                assert isinstance(item.service, DiagService)
                rich_print()
                rich_print(
                    f"  [blue]Detailed changes[/blue] of diagnostic service [magenta]'{item.service.short_name}'[/magenta]"
                )
                for param_changes in item.changed_parameters_of_service:
                    rich_print(f"   {param_changes.description}:")
                    table = RichTable(
                        show_header=True,
                        header_style="bold cyan",
                        border_style="blue",
                        show_lines=True)
                    table.add_column("Attribute", style="light_cyan1")
                    table.add_column("Old Value", justify="left", style="light_goldenrod3")
                    table.add_column("New Value", justify="left", style="light_goldenrod3")

                    for value in param_changes.changed_attributes:
                        table.add_row(value.attribute,
                                      (str(value.old_value) if value.old_value else ""),
                                      (str(value.new_value) if value.new_value else ""))
                    rich_print(RichPadding(table, pad=(0, 0, 0, 3)))

                if self.detailed:
                    print_service_parameters(item.service, allow_unknown_bit_lengths=True)

    def print_database_changes(self, changes_variants: SpecsChangesVariants) -> None:

        if changes_variants.new_diagnostic_layers:
            rich_print()
            rich_print("[blue]New diagnostic layers[/blue]:")
            for variant in changes_variants.new_diagnostic_layers:
                assert isinstance(variant, DiagLayer)
                rich_print(
                    f" [green3]{variant.short_name}[/green3] [medium_spring_green]({variant.variant_type.value})[/medium_spring_green]"
                )

        if changes_variants.deleted_diagnostic_layers:
            rich_print()
            rich_print("[blue]Deleted diagnostic layers[/blue]:")
            for variant in changes_variants.deleted_diagnostic_layers:
                assert isinstance(variant, DiagLayer)
                rich_print(
                    f" [green3]{variant.short_name}[/green3] [medium_spring_green]({variant.variant_type.value})[/medium_spring_green]"
                )

        if changes_variants.changed_diagnostic_layers:
            rich_print()
            rich_print("[blue]Changed diagnostic layers[/blue]: ")
            [
                rich_print(
                    f" [green3]{value.diag_layer}[/green3] [medium_spring_green]({value.diag_layer_type})[/medium_spring_green]"
                ) for value in changes_variants.changed_diagnostic_layers
            ]

            # print changes of diagnostic services
            for value in changes_variants.changed_diagnostic_layers:
                assert isinstance(value, DiagLayerChanges)
                self.print_dl_changes(value)


class Comparison(Display):
    databases: list[Database] = []  # storage of database objects
    diagnostic_layers: list[DiagLayer] = []  # storage of DiagLayer objects
    diagnostic_layer_names: set[str] = set()  # storage of diagnostic layer names

    db_indicator_1: int
    db_indicator_2: int

    def __init__(self) -> None:
        pass

    def compare_parameters(self, param1: Parameter,
                           param2: Parameter) -> list[ParameterAttributeChanges]:
        '''
        checks whether properties of param1 and param2 differ
        
        checked properties: Name, Byte Position, Bit Length, Semantic, Parameter Type, Value (Coded, Constant, Default etc.), Data Type, Data Object Property (Name, Physical Data Type, Unit)
        '''

        changed_attributes: list[ParameterAttributeChanges] = []

        if param1.short_name != param2.short_name:
            changed_attributes.append(
                ParameterAttributeChanges(
                    attribute="Parameter name",
                    old_value=param2.short_name,
                    new_value=param1.short_name))
        if param1.byte_position != param2.byte_position:
            changed_attributes.append(
                ParameterAttributeChanges(
                    attribute="Byte position",
                    old_value=param2.byte_position,
                    new_value=param1.byte_position))
        if param1.get_static_bit_length() != param2.get_static_bit_length():
            changed_attributes.append(
                ParameterAttributeChanges(
                    attribute="Bit Length",
                    old_value=param2.get_static_bit_length(),
                    new_value=param1.get_static_bit_length()))
        if param1.semantic != param2.semantic:
            changed_attributes.append(
                ParameterAttributeChanges(
                    attribute="Semantic", old_value=param2.semantic, new_value=param1.semantic))
        if param1.parameter_type != param2.parameter_type:
            changed_attributes.append(
                ParameterAttributeChanges(
                    attribute="Parameter type",
                    old_value=param2.parameter_type,
                    new_value=param1.parameter_type))

        if isinstance(param1, CodedConstParameter) and isinstance(param2, CodedConstParameter):
            if param1.diag_coded_type.base_data_type != param2.diag_coded_type.base_data_type:
                changed_attributes.append(
                    ParameterAttributeChanges(
                        attribute="Data type",
                        old_value=param2.diag_coded_type.base_data_type.name,
                        new_value=param1.diag_coded_type.base_data_type.name))
            if param1.coded_value != param2.coded_value:
                if isinstance(param1.coded_value, int) and isinstance(param2.coded_value, int):
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Value",
                            old_value=f"0x{param2.coded_value:0{(param2.get_static_bit_length() or 0) // 4}X}",
                            new_value=f"0x{param1.coded_value:0{(param1.get_static_bit_length() or 0) // 4}X}"
                        ))
                else:
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Value",
                            old_value=f"{param2.coded_value!r}",
                            new_value=f"{param1.coded_value!r}"))

        elif isinstance(param1, NrcConstParameter) and isinstance(param2, NrcConstParameter):
            if param1.diag_coded_type.base_data_type != param2.diag_coded_type.base_data_type:
                changed_attributes.append(
                    ParameterAttributeChanges(
                        attribute="Data type",
                        old_value=param2.diag_coded_type.base_data_type.name,
                        new_value=param1.diag_coded_type.base_data_type.name))

            if param1.coded_values != param2.coded_values:
                changed_attributes.append(
                    ParameterAttributeChanges(
                        attribute="Values",
                        old_value=param2.coded_values,
                        new_value=param1.coded_values))

        elif isinstance(param1, ParameterWithDOP) and isinstance(param2, ParameterWithDOP):

            if (dop_1 := param1.dop) != (dop_2 := param2.dop):
                # TODO: compare INTERNAL-CONSTR, COMPU-INTERNAL-TO-PHYS of DOP

                # DOP Name
                if dop_1.short_name != dop_2.short_name:
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Linked DOP object: Name",
                            old_value=dop_2.short_name,
                            new_value=dop_1.short_name))

                # DOP Unit
                if isinstance(dop_1, DataObjectProperty) and isinstance(dop_2, DataObjectProperty):
                    # (properties of unit object: short_name, long_name, description, odx_id, display_name, oid, factor_si_to_unit, offset_si_to_unit, physical_dimension_ref)
                    if dop_1.unit != dop_2.unit and dop_1.unit.short_name != dop_2.unit.short_name:
                        changed_attributes.append(
                            ParameterAttributeChanges(
                                attribute="Linked DOP object: Unit name",
                                old_value=dop_2.unit.short_name,
                                new_value=dop_1.unit.short_name))
                    elif dop_1.unit != dop_2.unit and dop_1.unit.display_name != dop_2.unit.display_name:
                        changed_attributes.append(
                            ParameterAttributeChanges(
                                attribute="Linked DOP object: Unit display name",
                                old_value=dop_2.unit.display_name,
                                new_value=dop_1.unit.display_name))
                    elif dop_1.unit != dop_2.unit:
                        changed_attributes.append(
                            ParameterAttributeChanges(attribute="Linked DOP object: Unit object"))

                if ((isinstance(dop_1, DataObjectProperty) or isinstance(dop_1, DtcDop)) and
                    (isinstance(dop_2, DataObjectProperty) or isinstance(dop_2, DtcDop))):
                    if (dop_1.physical_type and dop_2.physical_type and
                            dop_1.physical_type.base_data_type
                            != dop_2.physical_type.base_data_type):
                        changed_attributes.append(
                            ParameterAttributeChanges(
                                attribute="Linked DOP object: Physical data type",
                                old_value=dop_2.physical_type.base_data_type.name,
                                new_value=dop_1.physical_type.base_data_type.name))

            if (isinstance(param1, PhysicalConstantParameter) and
                    isinstance(param2, PhysicalConstantParameter) and
                    param1.physical_constant_value != param2.physical_constant_value):
                if isinstance(param1.physical_constant_value, int) and isinstance(
                        param2.physical_constant_value, int):
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Constant value",
                            old_value=f"0x{param2.physical_constant_value:0{(param2.get_static_bit_length() or 0) // 4}X}",
                            new_value=f"0x{param1.physical_constant_value:0{(param1.get_static_bit_length() or 0) // 4}X}"
                        ))
                else:
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Constant value",
                            old_value=f"{param2.physical_constant_value!r}",
                            new_value=f"{param1.physical_constant_value!r}"))

            elif (isinstance(param1, ValueParameter) and isinstance(param2, ValueParameter) and
                  param1.physical_default_value is not None and
                  param2.physical_default_value is not None and
                  param1.physical_default_value != param2.physical_default_value):
                if isinstance(param1.physical_default_value, int) and isinstance(
                        param2.physical_default_value, int):
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Constant value",
                            old_value=f"0x{param2.physical_default_value:0{(param2.get_static_bit_length() or 0) // 4}X}",
                            new_value=f"0x{param1.physical_default_value:0{(param1.get_static_bit_length() or 0) // 4}X}"
                        ))
                else:
                    changed_attributes.append(
                        ParameterAttributeChanges(
                            attribute="Default value",
                            old_value=f"{param2.physical_default_value!r}",
                            new_value=f"{param1.physical_default_value!r}"))

        return changed_attributes

    def compare_services(self, service1: DiagService,
                         service2: DiagService) -> Optional[ServiceChanges]:
        '''compares request, positive response and negative response parameters of two diagnostic services'''

        changed_params: list[ParameterChanges] = []

        # Request
        if service1.request is not None and service2.request is not None and len(
                service1.request.parameters) == len(service2.request.parameters):
            for res1_idx, param1 in enumerate(service1.request.parameters):
                for res2_idx, param2 in enumerate(service2.request.parameters):
                    if res1_idx == res2_idx:
                        # find changed request parameter properties
                        if (param_changes := self.compare_parameters(param1, param2)):
                            description = (
                                f"Properties of {res2_idx+1}. request parameter [light_slate_grey]'{param2.short_name}'[/light_slate_grey] have changed"
                            )
                            changed_params.append(
                                ParameterChanges(
                                    description=description, changed_attributes=param_changes))
        else:
            description = f"List of request parameters for service [magenta]'{service2.short_name}'[/magenta] is not identical"

            changed_params.append(
                ParameterChanges(
                    description=description,
                    changed_attributes=[
                        ParameterAttributeChanges(
                            attribute="Request parameter list",
                            old_value=[x.short_name for x in service2.request.parameters]
                            if service2.request else "",
                            new_value=[x.short_name for x in service1.request.parameters]
                            if service1.request else "")
                    ]))

        # Positive Responses
        if len(service1.positive_responses) == len(service2.positive_responses):
            for res1_idx, response1 in enumerate(service1.positive_responses):
                for res2_idx, response2 in enumerate(service2.positive_responses):
                    if res1_idx == res2_idx:
                        if len(response1.parameters) == len(response2.parameters):
                            for param1_idx, param1 in enumerate(response1.parameters):
                                for param2_idx, param2 in enumerate(response2.parameters):
                                    if param1_idx == param2_idx:
                                        # find changed positive response parameter properties
                                        if (param_changes :=
                                                self.compare_parameters(param1, param2)):
                                            description = f"Properties of {param2_idx+1}. positive response parameter [light_slate_grey]'{param2.short_name}'[/light_slate_grey] have changed"
                                            changed_params.append(
                                                ParameterChanges(
                                                    description=description,
                                                    changed_attributes=param_changes))
                        else:
                            description = f"List of positive response parameters for service [magenta]'{service2.short_name}'[/magenta] is not identical"
                            changed_params.append(
                                ParameterChanges(
                                    description=description,
                                    changed_attributes=[
                                        ParameterAttributeChanges(
                                            attribute="Positive response parameter list",
                                            old_value=[x.short_name for x in response2.parameters],
                                            new_value=[x.short_name for x in response1.parameters])
                                    ]))

        else:
            description = f"List of positive responses for service [magenta]'{service2.short_name}'[/magenta] is not identical"
            changed_params.append(
                ParameterChanges(
                    description=description,
                    changed_attributes=[
                        ParameterAttributeChanges(
                            attribute="Positive responses list",
                            old_value=[x.short_name for x in service2.positive_responses],
                            new_value=[x.short_name for x in service1.positive_responses])
                    ]))

        # Negative Responses
        if len(service1.negative_responses) == len(service2.negative_responses):
            for res1_idx, response1 in enumerate(service1.negative_responses):
                for res2_idx, response2 in enumerate(service2.negative_responses):
                    if res1_idx == res2_idx:
                        if len(response1.parameters) == len(response2.parameters):
                            for param1_idx, param1 in enumerate(response1.parameters):
                                for param2_idx, param2 in enumerate(response2.parameters):
                                    if param1_idx == param2_idx:
                                        # find changed negative response parameter properties
                                        if (param_changes :=
                                                self.compare_parameters(param1, param2)):
                                            description = f"Properties of {param2_idx+1}. negative response parameter [light_slate_grey]'{param2.short_name}'[/light_slate_grey] have changed"
                                            changed_params.append(
                                                ParameterChanges(
                                                    description=description,
                                                    changed_attributes=param_changes))
                        else:
                            description = f"List of negative response parameters for service [magenta]'{service2.short_name}'[/magenta] is not identical"
                            changed_params.append(
                                ParameterChanges(
                                    description=description,
                                    changed_attributes=[
                                        ParameterAttributeChanges(
                                            attribute="Negative response parameter list",
                                            old_value=[x.short_name for x in response2.parameters],
                                            new_value=[x.short_name for x in response1.parameters])
                                    ]))
        else:
            description = f"List of negative responses for service [magenta]'{service2.short_name}'[/magenta] is not identical"
            changed_params.append(
                ParameterChanges(
                    description=description,
                    changed_attributes=[
                        ParameterAttributeChanges(
                            attribute="Negative responses list",
                            old_value=[x.short_name for x in service2.negative_responses],
                            new_value=[x.short_name for x in service1.negative_responses])
                    ]))

        if changed_params:
            return ServiceChanges(service=service1, changed_parameters_of_service=changed_params)

    def compare_diagnostic_layers(self, dl1: DiagLayer,
                                  dl2: DiagLayer) -> Optional[DiagLayerChanges]:
        '''compares diagnostic services of two diagnostic layers with each other'''
        # TODO: add comparison of SingleECUJobs

        new_services: list[DiagService] = []
        deleted_services: list[DiagService] = []
        renamed_services: list[RenamedService] = []
        services_with_param_changes: list[ServiceChanges] = []

        service_spec = DiagLayerChanges(
            diag_layer=dl1.short_name,
            diag_layer_type=dl1.variant_type.value,
            new_services=new_services,
            deleted_services=deleted_services,
            renamed_services=renamed_services,
            services_with_parameter_changes=services_with_param_changes)
        dl1_service_names = [service.short_name for service in dl1.services]
        dl2_service_names = [service.short_name for service in dl2.services]

        dl1_request_prefixes: list[bytes | bytearray | None] = [
            None if s.request is None else s.request.coded_const_prefix() for s in dl1.services
        ]
        dl2_request_prefixes: list[bytes | bytearray | None] = [
            None if s.request is None else s.request.coded_const_prefix() for s in dl2.services
        ]

        # compare diagnostic services
        for service1 in dl1.services:

            # check for added diagnostic services
            rq_prefix: bytes | bytearray
            if service1.request is not None:
                rq_prefix = service1.request.coded_const_prefix()

            if service1 not in dl2.services:

                # check whether names of diagnostic services have changed
                # (this will not work in cases where the constant prefix of a request was modified)
                if (rq_prefix in dl2_request_prefixes and
                        service1.short_name not in dl2_service_names):

                    # get related diagnostic service for request
                    service2 = dl2.services[dl2_request_prefixes.index(rq_prefix)]

                    # save information about changes in ServiceDiff object
                    service_spec.renamed_services.append(
                        RenamedService(
                            old_service_name=service2.short_name,
                            new_service_name=service1.short_name,
                            new_service_object=service1))

                    # compare request, pos. response and neg. response parameters of diagnostic services &
                    # add information about changed diagnostic service parameters to ServiceDiff object
                    if (detailed_information := self.compare_services(service1, service2)):
                        service_spec.services_with_parameter_changes.append(detailed_information)

                elif rq_prefix not in dl2_request_prefixes or service1.short_name not in dl2_service_names:
                    service_spec.new_services.append(service1)

            for service2_idx, service2 in enumerate(dl2.services):

                # check for deleted diagnostic services
                if service2.short_name not in dl1_service_names and dl2_request_prefixes[
                        service2_idx] not in dl1_request_prefixes:

                    if service2 not in (deleted_list := service_spec.deleted_services):
                        deleted_list.append(service2)

                if service1.short_name == service2.short_name:
                    # compare request, pos. response and neg. response parameters of both diagnostic services &
                    # add information about changed diagnostic service parameters to ServiceDiff object
                    if (detailed_information := self.compare_services(service1, service2)):
                        service_spec.services_with_parameter_changes.append(detailed_information)

        if service_spec.new_services or service_spec.deleted_services or service_spec.renamed_services or service_spec.services_with_parameter_changes:
            return service_spec

    def compare_databases(self, database_new: Database,
                          database_old: Database) -> Optional[SpecsChangesVariants]:
        '''compares two PDX-files with each other'''

        new_variants: list[DiagLayer] = []  # Assuming it stores diagnostic layer names
        deleted_variants: list[DiagLayer] = []

        changes_variants = SpecsChangesVariants(
            new_diagnostic_layers=new_variants,
            deleted_diagnostic_layers=deleted_variants,
            changed_diagnostic_layers=[])

        # compare databases
        for _, dl1 in enumerate(database_new.diag_layers):
            # check for new diagnostic layers
            if dl1.short_name not in [dl.short_name for dl in database_old.diag_layers]:
                changes_variants.new_diagnostic_layers.append(dl1)

            for _, dl2 in enumerate(database_old.diag_layers):
                # check for deleted diagnostic layers
                if (dl2.short_name not in [dl.short_name for dl in database_new.diag_layers] and
                        dl2 not in changes_variants.deleted_diagnostic_layers):

                    changes_variants.deleted_diagnostic_layers.append(dl2)

                if dl1.short_name == dl2.short_name and dl1.short_name in self.diagnostic_layer_names:
                    # compare diagnostic services of both diagnostic layers &
                    # save diagnostic service changes in SpecsChangesVariants object
                    if (service_spec := self.compare_diagnostic_layers(dl1, dl2)):
                        changes_variants.changed_diagnostic_layers.append(service_spec)

        if changes_variants.new_diagnostic_layers or changes_variants.deleted_diagnostic_layers or changes_variants.changed_diagnostic_layers:
            return changes_variants


def add_subparser(subparsers: SubparsersList) -> None:
    parser = subparsers.add_parser(
        "compare",
        description="\n".join([
            "Compares two versions of diagnostic layers or databases with each other. Checks whether diagnostic services and its parameters have changed.",
            "",
            "Examples:",
            "  Comparison of two diagnostic layers:",
            "    odxtools compare ./path/to/database.pdx -v variant1 variant2",
            "  Comparison of two database versions:",
            "    odxtools compare ./path/to/database.pdx -db ./path/to/old-database.pdx",
            "  For more information use:",
            "    odxtools compare -h",
        ]),
        help="Compares two versions of diagnostic layers and/or databases with each other. Checks whether diagnostic services and its parameters have changed.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "-v",
        "--variants",
        nargs="+",
        metavar="VARIANT",
        required=False,
        default=None,
        help="Compare specified (ecu) variants to each other.",
    )

    parser.add_argument(
        "-db",
        "--database",
        nargs="+",
        default=None,
        metavar="DATABASE",
        required=False,
        help="Compare specified database file(s) to database file of first input argument.",
    )

    parser.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        default=False,
        required=False,
        help="Show all variant and service details",
    )

    # TODO
    # Idea: provide folder with multiple pdx files as argument
    # -> load all pdx files in folder, sort them alphabetically, compare databases pairwaise
    # -> calculate metrics (number of added services, number of changed services, number of removed services, total number of services per ecu variant, ...)
    # -> display metrics graphically


def run(args: argparse.Namespace) -> None:

    task = Comparison()
    task.detailed = args.verbose

    db_names = [args.pdx_file if isinstance(args.pdx_file, str) else str(args.pdx_file[0])]

    if args.database:
        # compare specified databases
        # if args.variants is specified, filter considered diagnostic layers

        for name in args.database:
            db_names.append(name) if isinstance(name, str) else str(name[0])

        task.databases = [load_file(name) for name in db_names]
        diag_layer_names = {dl.short_name for db in task.databases for dl in db.diag_layers}

        if args.variants:
            task.diagnostic_layer_names = diag_layer_names.intersection(set(args.variants))

            for name in args.variants:
                if name not in task.diagnostic_layer_names:
                    rich_print(f"The variant [green3]'{name}'[/green3] could not be found!")
                    return

        else:
            task.diagnostic_layer_names = diag_layer_names

        task.db_indicator_1 = 0

        for db_idx, _ in enumerate(task.databases):
            if db_idx + 1 >= len(task.databases):
                break
            task.db_indicator_2 = db_idx + 1

            rich_print()
            rich_print(f"Changes in file [orange1]'{os.path.basename(db_names[0])}'[/orange1]")
            rich_print(
                f" (compared to [orange1]'{os.path.basename(db_names[db_idx + 1])}'[/orange1])")

            if task.detailed:
                if args.variants:
                    diag_layers_1 = [
                        dl for dl in task.databases[0].diag_layers
                        if dl.short_name in task.diagnostic_layer_names
                    ]
                    diag_layers_2 = [
                        dl for dl in task.databases[db_idx + 1].diag_layers
                        if dl.short_name in task.diagnostic_layer_names
                    ]
                else:
                    diag_layers_1 = task.databases[0].diag_layers
                    diag_layers_2 = task.databases[db_idx + 1].diag_layers

                task.print_dl_overview(filename=os.path.basename(db_names[0]), dls=diag_layers_1)
                task.print_dl_overview(
                    filename=os.path.basename(db_names[db_idx + 1]), dls=diag_layers_2)

            task.print_database_changes(
                task.compare_databases(task.databases[0], task.databases[db_idx + 1]))

    elif args.variants:
        # no databases specified -> comparison of diagnostic layers

        odxdb = _parser_utils.load_file(args)
        task.databases = [odxdb]

        task.diagnostic_layers = [
            v for db in task.databases for variant in args.variants
            if (v := db.diag_layers.get(variant))
        ]
        task.diagnostic_layer_names = {dl.short_name for dl in task.diagnostic_layers}

        for name in args.variants:
            if name not in task.diagnostic_layer_names:
                rich_print(f"The variant [green3]'{name}'[/green3] could not be found!")
                return

        if task.detailed:
            task.print_dl_overview(
                filename=os.path.basename(
                    args.pdx_file if isinstance(args.pdx_file, str) else str(args.pdx_file[0])),
                dls=task.diagnostic_layers)

        for db_idx, dl in enumerate(task.diagnostic_layers):
            if db_idx + 1 >= len(task.diagnostic_layers):
                break

            rich_print()
            rich_print(
                f"Changes in diagnostic layer [green3]'{dl.short_name}'[/green3] [medium_spring_green]({dl.variant_type.value})[/medium_spring_green]"
            )
            rich_print(
                f" (compared to '[green3]{task.diagnostic_layers[db_idx+1].short_name}'[/green3] [medium_spring_green]({task.diagnostic_layers[db_idx+1].variant_type.value})[/medium_spring_green])"
            )
            task.print_dl_changes(
                task.compare_diagnostic_layers(dl, task.diagnostic_layers[db_idx + 1]))

    else:
        # no databases & no variants specified
        rich_print("Please specify either a database or variant for a comparison")
