#!/usr/bin/env python
# SPDX-License-Identifier: MIT

import argparse
import os
from typing import Any, Dict, List, Optional, Set, Union, cast

from rich import print as rich_print
from rich.padding import Padding as RichPadding
from rich.table import Table as RichTable

from ..database import Database
from ..diaglayers.diaglayer import DiagLayer
from ..diagservice import DiagService
from ..loadfile import load_file
from ..odxtypes import AtomicOdxType
from ..parameters.codedconstparameter import CodedConstParameter
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.parameter import Parameter
from ..parameters.physicalconstantparameter import PhysicalConstantParameter
from ..parameters.valueparameter import ValueParameter
from . import _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import (extract_service_tabulation_data, print_dl_metrics,
                           print_service_parameters)

# name of the tool
_odxtools_tool_name_ = "compare"

VariantName = str
VariantType = str
NewServices = List[DiagService]
DeletedServices = List[DiagService]
RenamedServices = List[List[Union[str, DiagService]]]
ServicesWithParamChanges = List[List[Union[str, DiagService]]]

SpecsServiceDict = Dict[str, Union[VariantName, VariantType, NewServices, DeletedServices,
                                   RenamedServices, ServicesWithParamChanges]]

NewVariants = List[DiagLayer]
DeletedVariants = List[DiagLayer]

SpecsChangesVariants = Dict[str, Union[NewVariants, DeletedVariants, SpecsServiceDict]]


class Display:
    # class with variables and functions to display the result of the comparison

    # TODO
    # - Idea: results as json export
    #  - write results of comparison in json structure
    #  - use odxlinks to refer to dignostic services / objects if
    #    changes have already been detected (e.g. in another ecu
    #    variant / diagnostic layer)
    # - print all information about parameter properties (request,
    #   pos. response & neg. response parameters) for changed diagnostic
    #   services
    param_detailed: bool
    obj_detailed: bool

    def __init__(self) -> None:
        pass

    def print_dl_changes(self, service_dict: SpecsServiceDict) -> None:

        if service_dict["new_services"] or service_dict["deleted_services"] or service_dict[
                "changed_name_of_service"][0] or service_dict["changed_parameters_of_service"][0]:
            assert isinstance(service_dict["diag_layer"], str)
            rich_print()
            rich_print(
                f"Changed diagnostic services for diagnostic layer '{service_dict['diag_layer']}' ({service_dict['diag_layer_type']}):"
            )
        if service_dict["new_services"]:
            assert isinstance(service_dict["new_services"], List)
            rich_print()
            rich_print(" [blue]New services[/blue]")
            rich_print(extract_service_tabulation_data(
                service_dict["new_services"]))  # type: ignore[arg-type]
        if service_dict["deleted_services"]:
            assert isinstance(service_dict["deleted_services"], List)
            rich_print()
            rich_print(" [blue]Deleted services[/blue]")
            rich_print(extract_service_tabulation_data(
                service_dict["deleted_services"]))  # type: ignore[arg-type]
        if service_dict["changed_name_of_service"][0]:
            rich_print()
            rich_print(" [blue]Renamed services[/blue]")
            rich_print(extract_service_tabulation_data(
                service_dict["changed_name_of_service"][0]))  # type: ignore[arg-type]
        if service_dict["changed_parameters_of_service"][0]:
            rich_print()
            rich_print(" [blue]Services with parameter changes[/blue]")
            # create table with information about services with parameter changes
            changed_param_column = [
                str(x) for x in service_dict["changed_parameters_of_service"][
                    1]  # type: ignore[union-attr]
            ]
            table = extract_service_tabulation_data(
                service_dict["changed_parameters_of_service"][0],  # type: ignore[arg-type]
                additional_columns=[("Changed Parameters", changed_param_column)])
            rich_print(table)

            for service_idx, service in enumerate(
                    service_dict["changed_parameters_of_service"][0]):  # type: ignore[arg-type]
                assert isinstance(service, DiagService)
                rich_print()
                rich_print(
                    f"  Detailed changes of diagnostic service [u cyan]{service.short_name}[/u cyan]"
                )
                #   detailed_info in [infotext1, dict1, infotext2, dict2, ...]
                info_list = cast(
                    list,  # type: ignore[type-arg]
                    service_dict["changed_parameters_of_service"])[2][service_idx]
                for detailed_info in info_list:
                    if isinstance(detailed_info, str):
                        rich_print()
                        rich_print(detailed_info)
                    elif isinstance(detailed_info, dict):
                        table = RichTable(
                            show_header=True,
                            header_style="bold cyan",
                            border_style="blue",
                            show_lines=True)
                        for header in detailed_info:
                            table.add_column(header)
                        rows = zip(*detailed_info.values())
                        for row in rows:
                            table.add_row(*map(str, row))

                        rich_print(RichPadding(table, pad=(0, 0, 0, 4)))
                        rich_print()
                if self.param_detailed:
                    # print all parameter details of diagnostic service
                    print_service_parameters(service, allow_unknown_bit_lengths=True)

    def print_database_changes(self, changes_variants: SpecsChangesVariants) -> None:
        # prints result of database comparison (input variable: dictionary: changes_variants)

        # diagnostic layers
        if changes_variants["new_diagnostic_layers"] or changes_variants[
                "deleted_diagnostic_layers"]:
            rich_print()
            rich_print("[bright_blue]Changed diagnostic layers[/bright_blue]: ")
            rich_print(" New diagnostic layers: ")
            for variant in changes_variants["new_diagnostic_layers"]:
                assert isinstance(variant, DiagLayer)
                rich_print(
                    f"  [magenta]{variant.short_name}[/magenta] ({variant.variant_type.value})")
            rich_print(" Deleted diagnostic layers: ")
            for variant in changes_variants["deleted_diagnostic_layers"]:
                assert isinstance(variant, DiagLayer)
                rich_print(
                    f"  [magenta]{variant.short_name}[/magenta] ({variant.variant_type.value})")

        # diagnostic services
        for _, value in changes_variants.items():
            if isinstance(value, dict):
                self.print_dl_changes(value)


class Comparison(Display):
    databases: List[Database] = []  # storage of database objects
    diagnostic_layers: List[DiagLayer] = []  # storage of DiagLayer objects
    diagnostic_layer_names: Set[str] = set()  # storage of diagnostic layer names

    db_indicator_1: int
    db_indicator_2: int

    def __init__(self) -> None:
        pass

    def compare_parameters(self, param1: Parameter, param2: Parameter) -> Dict[str, Any]:
        # checks whether properties of param1 and param2 differ
        # checked properties: Name, Byte Position, Bit Length, Semantic, Parameter Type, Value (Coded, Constant, Default etc.), Data Type, Data Object Property (Name, Physical Data Type, Unit)

        property = []
        old = []
        new = []

        def append_list(property_name: str, new_property_value: Optional[AtomicOdxType],
                        old_property_value: Optional[AtomicOdxType]) -> None:
            property.append(property_name)
            old.append(old_property_value)
            new.append(new_property_value)

        if param1.short_name != param2.short_name:
            append_list("Parameter name", param1.short_name, param2.short_name)
        if param1.byte_position != param2.byte_position:
            append_list("Byte position", param1.byte_position, param2.byte_position)
        if param1.get_static_bit_length() != param2.get_static_bit_length():
            append_list("Bit Length", param1.get_static_bit_length(),
                        param2.get_static_bit_length())
        if param1.semantic != param2.semantic:
            append_list("Semantic", param1.semantic, param2.semantic)
        if param1.parameter_type != param2.parameter_type:
            append_list("Parameter type", param1.parameter_type, param2.parameter_type)

        if isinstance(param1, CodedConstParameter) and isinstance(param2, CodedConstParameter):
            if param1.diag_coded_type.base_data_type != param2.diag_coded_type.base_data_type:
                append_list("Data type", param1.diag_coded_type.base_data_type.name,
                            param2.diag_coded_type.base_data_type.name)
            if param1.coded_value != param2.coded_value:
                if isinstance(param1.coded_value, int) and isinstance(param2.coded_value, int):
                    append_list(
                        "Value",
                        f"0x{param1.coded_value:0{(param1.get_static_bit_length() or 0) // 4}X}",
                        f"0x{param2.coded_value:0{(param2.get_static_bit_length() or 0) // 4}X}")
                else:
                    append_list("Value", f"{param1.coded_value!r}", f"{param2.coded_value!r}")

        elif isinstance(param1, NrcConstParameter) and isinstance(param2, NrcConstParameter):
            if param1.diag_coded_type.base_data_type != param2.diag_coded_type.base_data_type:
                append_list("Data type", param1.diag_coded_type.base_data_type.name,
                            param2.diag_coded_type.base_data_type.name)
            if param1.coded_values != param2.coded_values:
                append_list("Values", str(param1.coded_values), str(param2.coded_values))

        elif (dop_1 := getattr(param1, "dop", None)) is not None and (dop_2 := getattr(
                param2, "dop", None)) is not None:

            if dop_1 != dop_2:
                # TODO: compare INTERNAL-CONSTR, COMPU-INTERNAL-TO-PHYS of DOP
                append_list("Linked DOP object", "", "")

                # DOP Name
                if dop_1.short_name != dop_2.short_name:
                    append_list(" DOP name", dop_1.short_name, dop_2.short_name)

                # DOP Unit
                if getattr(dop_1, "unit", None) and getattr(dop_2, "unit", None):
                    # (properties of unit object: short_name, long_name, description, odx_id, display_name, oid, factor_si_to_unit, offset_si_to_unit, physical_dimension_ref)
                    if dop_1.unit != dop_2.unit and dop_1.unit.short_name != dop_2.unit.short_name:
                        append_list("  DOP unit name", dop_1.unit.short_name, dop_2.unit.short_name)
                    elif dop_1.unit != dop_2.unit and dop_1.unit.display_name != dop_2.unit.display_name:
                        append_list("  DOP unit display name", dop_1.unit.display_name,
                                    dop_2.unit.display_name)
                    elif dop_1.unit != dop_2.unit:
                        append_list(" DOP unit object", "", "")

                if hasattr(dop_1, "physical_type") and hasattr(dop_2, "physical_type"):
                    if (dop_1.physical_type and dop_2.physical_type and
                            dop_1.physical_type.base_data_type
                            != dop_2.physical_type.base_data_type):
                        append_list(" DOP physical data type",
                                    dop_1.physical_type.base_data_type.name,
                                    dop_2.physical_type.base_data_type.name)

            if (isinstance(param1, PhysicalConstantParameter) and
                    isinstance(param2, PhysicalConstantParameter) and
                    param1.physical_constant_value != param2.physical_constant_value):
                if isinstance(param1.physical_constant_value, int) and isinstance(
                        param2.physical_constant_value, int):
                    append_list(
                        "Constant value",
                        f"0x{param1.physical_constant_value:0{(param1.get_static_bit_length() or 0) // 4}X}",
                        f"0x{param2.physical_constant_value:0{(param2.get_static_bit_length() or 0) // 4}X}"
                    )
                else:
                    append_list("Constant value", f"{param1.physical_constant_value!r}",
                                f"{param2.physical_constant_value!r}")

            elif (isinstance(param1, ValueParameter) and isinstance(param2, ValueParameter) and
                  param1.physical_default_value is not None and
                  param2.physical_default_value is not None and
                  param1.physical_default_value != param2.physical_default_value):
                if isinstance(param1.physical_default_value, int) and isinstance(
                        param2.physical_default_value, int):
                    append_list(
                        "Default value",
                        f"0x{param1.physical_default_value:0{(param1.get_static_bit_length() or 0) // 4}X}",
                        f"0x{param2.physical_default_value:0{(param2.get_static_bit_length() or 0) // 4}X}"
                    )
                else:
                    append_list("Default value", f"{param1.physical_default_value!r}",
                                f"{param2.physical_default_value!r}")

        return {"Property": property, "Old Value": old, "New Value": new}

    def compare_services(self, service1: DiagService,
                         service2: DiagService) -> List[SpecsServiceDict]:
        # compares request, positive response and negative response parameters of two diagnostic services

        information: List[Union[str, Dict[str, Any]]] = [
        ]  # information = [infotext1, table1, infotext2, table2, ...]
        changed_params = ""

        # Request
        if service1.request is not None and service2.request is not None and len(
                service1.request.parameters) == len(service2.request.parameters):
            for res1_idx, param1 in enumerate(service1.request.parameters):
                for res2_idx, param2 in enumerate(service2.request.parameters):
                    if res1_idx == res2_idx:
                        # find changed request parameter properties
                        table = self.compare_parameters(param1, param2)
                        infotext = (f"   Properties of request parameter '{param2.short_name}' "
                                    f"that have changed:\n")
                        # array index starts with 0 -> param[0] is 1. service parameter

                        if table["Property"]:
                            information.append(infotext)
                            information.append(table)
                            changed_params += f"request parameter '{param2.short_name}',\n"
        else:
            changed_params += "request parameter list, "
            # infotext
            information.append(f"List of request parameters for service '{service2.short_name}' "
                               f"is not identical.\n")

            # table

            param_list1 = [] if service1.request is None else service1.request.parameters
            param_list2 = [] if service2.request is None else service2.request.parameters

            information.append({
                "List": ["Old list", "New list"],
                "Values": [f"\\{param_list1}", f"\\{param_list2}"]
            })

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
                                        table = self.compare_parameters(param1, param2)
                                        infotext = (
                                            f"   Properties of positive response parameter '{param2.short_name}' that "
                                            f"have changed:\n")
                                        # array index starts with 0 -> param[0] is first service parameter

                                        if table["Property"]:
                                            information.append(infotext)
                                            information.append(table)
                                            changed_params += f"positive response parameter '{param2.short_name}',\n"
                        else:
                            changed_params += "positive response parameter list, "
                            # infotext
                            information.append(
                                f"List of positive response parameters for service '{service2.short_name}' is not identical."
                            )
                            # table
                            information.append({
                                "List": ["Old list", "New list"],
                                "Values": [str(response1.parameters),
                                           str(response2.parameters)]
                            })
        else:
            changed_params += "positive responses list, "
            # infotext
            information.append(
                f"List of positive responses for service '{service2.short_name}' is not identical.")
            # table
            information.append({
                "List": ["Old list", "New list"],
                "Values": [str(service1.positive_responses),
                           str(service2.positive_responses)]
            })

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
                                        table = self.compare_parameters(param1, param2)
                                        infotext = f"   Properties of response parameter '{param2.short_name}' that have changed:\n"
                                        # array index starts with 0 -> param[0] is 1. service parameter

                                        if table["Property"]:
                                            information.append(infotext)
                                            information.append(table)
                                            changed_params += f"negative response parameter '{param2.short_name}',\n"
                        else:
                            changed_params += "positive response parameter list, "
                            # infotext
                            information.append(
                                f"List of positive response parameters for service '{service2.short_name}' is not identical.\n"
                            )
                            # table
                            information.append({
                                "List": ["Old list", "New list"],
                                "Values": [str(response1.parameters),
                                           str(response2.parameters)]
                            })
        else:
            changed_params += "negative responses list, "
            # infotext
            information.append(
                f"List of positive responses for service '{service2.short_name}' is not identical.\n"
            )
            # table
            information.append({
                "List": ["Old list", "New list"],
                "Values": [str(service1.negative_responses),
                           str(service2.negative_responses)]
            })

        return [information, changed_params]  # type: ignore[list-item]

    def compare_diagnostic_layers(self, dl1: DiagLayer,
                                  dl2: DiagLayer) -> dict:  # type: ignore[type-arg]
        # compares diagnostic services of two diagnostic layers with each other
        # save changes in dictionary (service_dict)
        # TODO: add comparison of SingleECUJobs

        new_services: NewServices = []
        deleted_services: DeletedServices = []
        renamed_service: RenamedServices = [[],
                                            []]  # TODO: implement list of (str, DiagService)-tuples
        services_with_param_changes: ServicesWithParamChanges = [
            [], [], []
        ]  # TODO: implement list of tuples (str, str, DiagService)-tuples

        service_dict: SpecsServiceDict = {
            "diag_layer": dl1.short_name,
            "diag_layer_type": dl1.variant_type.value,
            # list with added diagnostic services [service1, service2, service3, ...] Type: DiagService
            "new_services": new_services,
            # list with deleted diagnostic services [service1, service2, service3, ...] Type: DiagService
            "deleted_services": deleted_services,
            # list with diagnostic services where the service name changed [[services], [old service names]]
            "changed_name_of_service": renamed_service,
            # list with diagnostic services where the service parameter changed [[services], [changed_parameters], [information_texts]]
            "changed_parameters_of_service": services_with_param_changes
        }
        # service_dict["changed_name_of_service"][{0 = services, 1 = old service names}][i]
        # service_dict["changed_parameters_of_service"][{0 = services, 1 = changed_parameters, 2 = information_texts}][i]

        dl1_service_names = [service.short_name for service in dl1.services]

        # extract the constant prefixes for the requests of all
        # services (used for duck-typed rename detection)
        dl1_request_prefixes: List[Optional[bytes]] = [
            None if s.request is None else s.request.coded_const_prefix() for s in dl1.services
        ]
        dl2_request_prefixes: List[Optional[bytes]] = [
            None if s.request is None else s.request.coded_const_prefix() for s in dl2.services
        ]

        # compare diagnostic services
        for service1 in dl1.services:

            # check for added diagnostic services
            rq_prefix: Optional[bytes] = None
            if service1.request is not None:
                rq_prefix = service1.request.coded_const_prefix()

            if service1 not in dl2.services:
                if rq_prefix is None or rq_prefix not in dl2_request_prefixes:
                    # TODO: this will not work in cases where the constant
                    # prefix of a request was modified...
                    service_dict["new_services"].append(  # type: ignore[union-attr]
                        service1)  # type: ignore[arg-type]

            # check whether names of diagnostic services have changed
            elif service1 not in dl2.services:
                if rq_prefix is None or rq_prefix in dl2_request_prefixes:
                    # get related diagnostic service for request
                    service2_idx = dl2_request_prefixes.index(rq_prefix)
                    service2 = dl2.services[service2_idx]

                    # save information about changes in dictionary

                    # add new service (type: DiagService)
                    service_dict["changed_name_of_service"][0].append(  # type: ignore[union-attr]
                        service1)
                    # add old service name (type: String)
                    service_dict["changed_name_of_service"][1].append(  # type: ignore[union-attr]
                        service2.short_name)

                    # compare request, pos. response and neg. response parameters of diagnostic services
                    detailed_information = self.compare_services(service1, service2)
                    # detailed_information = [[infotext1, table1, infotext2, table2, ...], changed_params]

                    # add information about changed diagnostic service parameters to dicitionary
                    if detailed_information[1]:  # check whether string "changed_params" is empty
                        # new service (type: DiagService)
                        service_dict["changed_parameters_of_service"][
                            0].append(  # type: ignore[union-attr]
                                service1)
                        # add parameters which have been changed (type: String)
                        service_dict["changed_parameters_of_service"][
                            1].append(  # type: ignore[union-attr]
                                detailed_information[1])  # type: ignore[arg-type]
                        # add detailed information about changed service parameters (type: list) [infotext1, table1, infotext2, table2, ...]
                        service_dict["changed_parameters_of_service"][
                            2].append(  # type: ignore[union-attr]
                                detailed_information[0])  # type: ignore[arg-type]

            for service2_idx, service2 in enumerate(dl2.services):

                # check for deleted diagnostic services
                if service2.short_name not in dl1_service_names and dl2_request_prefixes[
                        service2_idx] not in dl1_request_prefixes:

                    deleted_list = service_dict["deleted_services"]
                    assert isinstance(deleted_list, list)
                    if service2 not in deleted_list:
                        service_dict["deleted_services"].append(  # type: ignore[union-attr]
                            service2)  # type: ignore[arg-type]

                if service1.short_name == service2.short_name:
                    # compare request, pos. response and neg. response parameters of both diagnostic services
                    detailed_information = self.compare_services(service1, service2)
                    # detailed_information = [[infotext1, table1, infotext2, table2, ...], changed_params]

                    # add information about changed diagnostic service parameters to dicitionary
                    if detailed_information[1]:  # check whether string "changed_params" is empty
                        # new service (type: DiagService)
                        service_dict["changed_parameters_of_service"][
                            0].append(  # type: ignore[union-attr]
                                service1)
                        # add parameters which have been changed (type: String)
                        service_dict["changed_parameters_of_service"][  # type: ignore[union-attr]
                            1].append(detailed_information[1])  # type: ignore[arg-type]
                        # add detailed information about changed service parameters (type: list) [infotext1, table1, infotext2, table2, ...]
                        service_dict["changed_parameters_of_service"][  # type: ignore[union-attr]
                            2].append(detailed_information[0])  # type: ignore[arg-type]
        return service_dict

    def compare_databases(self, database_new: Database,
                          database_old: Database) -> dict:  # type: ignore[type-arg]
        # compares two PDX-files with each other

        new_variants: NewVariants = []
        deleted_variants: DeletedVariants = []

        changes_variants: SpecsChangesVariants = {
            "new_diagnostic_layers": new_variants,
            "deleted_diagnostic_layers": deleted_variants
        }

        # compare databases
        for _, dl1 in enumerate(database_new.diag_layers):
            # check for new diagnostic layers
            if dl1.short_name not in [dl.short_name for dl in database_old.diag_layers]:
                changes_variants["new_diagnostic_layers"].append(dl1)  # type: ignore[union-attr]

            for _, dl2 in enumerate(database_old.diag_layers):
                # check for deleted diagnostic layers
                if (dl2.short_name not in [dl.short_name for dl in database_new.diag_layers] and
                        dl2 not in changes_variants["deleted_diagnostic_layers"]):

                    changes_variants[
                        "deleted_diagnostic_layers"].append(  # type: ignore[union-attr]
                            dl2)

                if dl1.short_name == dl2.short_name and dl1.short_name in self.diagnostic_layer_names:
                    # compare diagnostic services of both diagnostic layers
                    # save diagnostic service changes in dictionary (empty if no changes)
                    service_dict: SpecsServiceDict = self.compare_diagnostic_layers(dl1, dl2)
                    if service_dict:
                        # adds information about diagnostic service changes to return variable (changes_variants)
                        changes_variants.update({dl1.short_name: service_dict})

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
        "-nd",
        "--no-details",
        action="store_false",
        default=True,
        required=False,
        help="Don't show all service parameter details",
    )

    # TODO
    # Idea: provide folder with multiple pdx files as argument
    # -> load all pdx files in folder, sort them alphabetically, compare databases pairwaise
    # -> calculate metrics (number of added services, number of changed services, number of removed services, total number of services per ecu variant, ...)
    # -> display metrics graphically


def run(args: argparse.Namespace) -> None:

    task = Comparison()
    task.param_detailed = args.no_details

    db_names = [args.pdx_file if isinstance(args.pdx_file, str) else str(args.pdx_file[0])]

    if args.database and args.variants:
        # compare specified databases, consider only specified variants

        for name in args.database:
            db_names.append(name) if isinstance(name, str) else str(name[0])

        task.databases = [load_file(name) for name in db_names]
        diag_layer_names = {dl.short_name for db in task.databases for dl in db.diag_layers}

        task.diagnostic_layer_names = diag_layer_names.intersection(set(args.variants))

        for name in args.variants:
            if name not in task.diagnostic_layer_names:
                rich_print(f"The variant '{name}' could not be found!")
                return

        task.db_indicator_1 = 0

        for db_idx, _ in enumerate(task.databases):
            if db_idx + 1 >= len(task.databases):
                break
            task.db_indicator_2 = db_idx + 1

            rich_print()
            rich_print(f"Changes in file '{os.path.basename(db_names[0])}'")
            rich_print(f" (compared to '{os.path.basename(db_names[db_idx + 1])}')")

            rich_print()
            rich_print(f"Overview of diagnostic layers (for {os.path.basename(db_names[0])})")
            print_dl_metrics([
                variant for variant in task.databases[0].diag_layers
                if variant.short_name in task.diagnostic_layer_names
            ])

            rich_print()
            rich_print(
                f"Overview of diagnostic layers (for {os.path.basename(db_names[db_idx+1])})")
            print_dl_metrics([
                variant for variant in task.databases[db_idx + 1].diag_layers
                if variant.short_name in task.diagnostic_layer_names
            ])

            task.print_database_changes(
                task.compare_databases(task.databases[0], task.databases[db_idx + 1]))

    elif args.database:
        # compare specified databases, consider all variants

        for name in args.database:
            db_names.append(name)
        task.databases = [load_file(name) for name in db_names]

        # collect all diagnostic layers from all specified databases
        task.diagnostic_layer_names = {
            dl.short_name
            for db in task.databases
            for dl in db.diag_layers
        }
        task.db_indicator_1 = 0

        for db_idx, _ in enumerate(task.databases):
            if db_idx + 1 >= len(task.databases):
                break
            task.db_indicator_2 = db_idx + 1

            rich_print()
            rich_print(f"Changes in file '{os.path.basename(db_names[0])}")
            rich_print(f" (compared to '{os.path.basename(db_names[db_idx + 1])}')")

            rich_print()
            rich_print(f"Overview of diagnostic layers (for {os.path.basename(db_names[0])})")
            print_dl_metrics(list(task.databases[0].diag_layers))

            rich_print()
            rich_print(
                f"Overview of diagnostic layers (for {os.path.basename(db_names[db_idx+1])})")
            print_dl_metrics(list(task.databases[db_idx + 1].diag_layers))

            task.print_database_changes(
                task.compare_databases(task.databases[0], task.databases[db_idx + 1]))

    elif args.variants:
        # no databases specified -> comparison of diagnostic layers

        odxdb = _parser_utils.load_file(args)
        task.databases = [odxdb]

        diag_layer_names = {dl.short_name for db in task.databases for dl in db.diag_layers}

        task.diagnostic_layer_names = diag_layer_names.intersection(set(args.variants))
        task.diagnostic_layers = [
            dl for db in task.databases for dl in db.diag_layers
            if dl.short_name in task.diagnostic_layer_names
        ]

        for name in args.variants:
            if name not in task.diagnostic_layer_names:
                rich_print(f"The variant '{name}' could not be found!")
                return

        rich_print()
        rich_print(f"Overview of diagnostic layers: ")
        print_dl_metrics(task.diagnostic_layers)

        for db_idx, dl in enumerate(task.diagnostic_layers):
            if db_idx + 1 >= len(task.diagnostic_layers):
                break

            rich_print()
            rich_print(f"Changes in diagnostic layer '{dl.short_name}' ({dl.variant_type.value})")
            rich_print(
                f" (compared to '{task.diagnostic_layers[db_idx + 1].short_name}' ({task.diagnostic_layers[db_idx + 1].variant_type.value}))"
            )
            task.print_dl_changes(
                task.compare_diagnostic_layers(dl, task.diagnostic_layers[db_idx + 1]))

    else:
        # no databases & no variants specified
        rich_print("Please specify either a database or variant for a comparison")
