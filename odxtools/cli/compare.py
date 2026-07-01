#!/usr/bin/env python
# SPDX-License-Identifier: MIT

import argparse
import csv
import functools
import json
import os
import re
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.padding import Padding as RichPadding
from rich.table import Table as RichTable
from typing_extensions import override

try:
    import yaml  # pyright: ignore[reportMissingModuleSource]
except ImportError:  # pragma: no cover
    yaml = None

from ..compumethods.limit import Limit
from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diaglayers.diaglayer import DiagLayer
from ..diagservice import DiagService
from ..dopbase import DopBase
from ..dtcdop import DtcDop
from ..encoding import Encoding
from ..internalconstr import InternalConstr
from ..loadfile import load_file
from ..nameditemlist import NamedItemList
from ..odxtypes import AtomicOdxType, DataType
from ..parameters.codedconstparameter import CodedConstParameter
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.parameter import Parameter
from ..parameters.parameterwithdop import ParameterWithDOP
from ..parameters.physicalconstantparameter import PhysicalConstantParameter
from ..parameters.valueparameter import ValueParameter
from ..request import Request
from ..response import Response
from ..unit import Unit
from . import _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import (
    build_service_table,
    print_dl_metrics,
    print_service_parameters,
)

ParameterAttributeChangesDict = dict[str, str]
ParameterChangesDict = dict[str, str | list[ParameterAttributeChangesDict]]
ServiceChangesDict = dict[str, dict[str, str] | list[ParameterChangesDict]]
DiagLayerChangesDict = dict[str, str | int | list[str | dict[str, str] | ServiceChangesDict]]
SpecsChangesVariantsDict = dict[str, list[dict[str, str] | DiagLayerChangesDict] | dict[str, int]]


def _strip_rich_formatting(text: str) -> str:
    """Remove rich formatting tags like [blue], [/blue], , etc."""
    return re.sub(r'\[.*?\]', '', text)


def profile(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that times method execution when profiling is enabled."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        profile_enabled = getattr(self, 'profile_enabled', False)
        if not profile_enabled:
            return func(self, *args, **kwargs)
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        elapsed = time.perf_counter() - start_time
        rich_print(f"[dim]{func.__name__} completed in {elapsed:.4f}s[/dim]")
        return result

    return wrapper


console = Console()
rich_print = console.print

# name of the tool
_odxtools_tool_name_ = "compare"


@dataclass
class ParameterAttributeChanges:
    """Represents a single attribute change detected during comparison."""
    attribute: str
    old_value: AtomicOdxType | Sequence[AtomicOdxType] | Encoding | DataType | None = field(
        default=None)
    new_value: AtomicOdxType | Sequence[AtomicOdxType] | Encoding | DataType | None = field(
        default=None)

    def to_dict(self) -> ParameterAttributeChangesDict:
        return {
            "attribute": self.attribute,
            "old_value": str(self.old_value) if self.old_value is not None else "",
            "new_value": str(self.new_value) if self.new_value is not None else "",
        }


@dataclass
class ParameterChanges:
    description: str  # description of change
    changed_attributes: list[ParameterAttributeChanges] = field(
        default_factory=list  # detailed information on changed attribute of parameter
    )

    def to_dict(self) -> ParameterChangesDict:
        return {
            "description": self.description,
            "changed_attributes": [attr.to_dict() for attr in self.changed_attributes],
        }


@dataclass
class ServiceChanges:
    service: DiagService  # The service whose parameters have changed
    changed_parameters_of_service: list[ParameterChanges] = field(default_factory=list)

    def to_dict(self) -> ServiceChangesDict:
        return {
            "service": {
                "short_name": self.service.short_name,
            },
            "changed_parameters": [p.to_dict() for p in self.changed_parameters_of_service],
        }


@dataclass
class RenamedService:
    old_service_name: str
    new_service_object: DiagService
    new_service_name: str = field(init=False)

    def __post_init__(self) -> None:
        """Set new_service_name from the service object's short_name."""
        self.new_service_name = self.new_service_object.short_name

    def to_dict(self) -> dict[str, str]:
        return {
            "old_service_name": self.old_service_name,
            "new_service_name": self.new_service_name,
        }


@dataclass
class DiagLayerChanges:
    """Represents changes detected between two diagnostic layers."""
    diag_layer: str
    diag_layer_type: str
    new_services: list[DiagService] = field(default_factory=list)
    deleted_services: list[DiagService] = field(default_factory=list)
    renamed_services: list[RenamedService] = field(default_factory=list)
    services_with_parameter_changes: list[ServiceChanges] = field(default_factory=list)

    def to_dict(self) -> DiagLayerChangesDict:
        return {
            "diag_layer": self.diag_layer,
            "diag_layer_type": self.diag_layer_type,
            "new_services": [
                service.short_name
                for service in sorted(self.new_services, key=lambda x: x.short_name)
            ],
            "deleted_services": [
                service.short_name
                for service in sorted(self.deleted_services, key=lambda x: x.short_name)
            ],
            "renamed_services": [
                rename.to_dict()
                for rename in sorted(self.renamed_services, key=lambda item: item.new_service_name)
            ],
            "services_with_parameter_changes": [
                service_change.to_dict() for service_change in sorted(
                    self.services_with_parameter_changes, key=lambda item: item.service.short_name)
            ],
            "change_score": self.change_score,
        }

    @property
    def change_score(self) -> int:
        return (len(self.new_services) + len(self.deleted_services) + len(self.renamed_services) +
                sum(
                    len(change.changed_parameters_of_service)
                    for change in self.services_with_parameter_changes))


@dataclass
class SpecsChangesVariants:
    new_diagnostic_layers: list[DiagLayer] = field(default_factory=list)
    deleted_diagnostic_layers: list[DiagLayer] = field(default_factory=list)
    changed_diagnostic_layers: list[DiagLayerChanges] = field(default_factory=list)

    def to_dict(self) -> SpecsChangesVariantsDict:
        return {
            "new_diagnostic_layers": [{
                "short_name": variant.short_name,
                "variant_type": variant.variant_type.value,
            } for variant in sorted(
                self.new_diagnostic_layers, key=lambda x: (x.variant_type.value, x.short_name))],
            "deleted_diagnostic_layers": [{
                "short_name": variant.short_name,
                "variant_type": variant.variant_type.value,
            } for variant in sorted(
                self.deleted_diagnostic_layers, key=lambda x: (x.variant_type.value, x.short_name))
                                         ],
            "changed_diagnostic_layers": [
                variant.to_dict() for variant in sorted(
                    self.changed_diagnostic_layers, key=lambda x: (x.diag_layer_type, x.diag_layer))
            ],
            "summary": self.summary,
        }

    @property
    def summary(self) -> dict[str, int]:
        return {
            "new_layers":
                len(self.new_diagnostic_layers),
            "deleted_layers":
                len(self.deleted_diagnostic_layers),
            "changed_layers":
                len(self.changed_diagnostic_layers),
            "new_services":
                sum(len(v.new_services) for v in self.changed_diagnostic_layers),
            "deleted_services":
                sum(len(v.deleted_services) for v in self.changed_diagnostic_layers),
            "renamed_services":
                sum(len(v.renamed_services) for v in self.changed_diagnostic_layers),
            "changed_services":
                sum(len(v.services_with_parameter_changes) for v in self.changed_diagnostic_layers),
            "total_change_score":
                sum(v.change_score for v in self.changed_diagnostic_layers),
        }


class ReportFormatter:
    """
    Formats and prints comparison results to the console using rich formatting.

    This class is responsible for presenting diagnostic comparison results
    in a human-readable, color-coded format suitable for interactive use.
    It uses the Rich library to provide enhanced terminal output with:

    - Colored highlighting for different types of changes
    - Hierarchical structure for diagnostic layers and services
    - Tables for structured data presentation

    Note:
        This class is the primary user interface for the compare tool
        in interactive mode. The output is optimized for human readability
        and fast scanning of changes.
    """

    def __init__(self, detailed: bool = False) -> None:
        """
        Initialize the ReportFormatter.

        Args:
            detailed: Whether to show detailed service parameter information.
                      When True, full parameter structures and DOP trees
                      are printed. When False, only summary information
                      is displayed.
        """
        self.detailed = detailed

    def print_dl_overview(self, filename: str, dls: list[DiagLayer]) -> None:
        """
        Print an overview of diagnostic layers in a file.

        Args:
            filename: Name of the file being displayed.
            dls: List of diagnostic layers to display.
        """
        rich_print()
        rich_print(f"Overview of diagnostic layers (in [orange1]{filename}[/orange1])")
        print_dl_metrics(dls)

    def print_dl_changes(self, service_spec: DiagLayerChanges) -> None:
        """
        Print changes detected between two diagnostic layers.

        Args:
            service_spec: All detected changes between two diagnostic layers.
        """
        if not (service_spec.new_services or service_spec.deleted_services or
                service_spec.renamed_services or service_spec.services_with_parameter_changes):
            return

        rich_print()
        rich_print(
            f"[blue]Changed diagnostic services[/blue] of diagnostic layer [green3]'{service_spec.diag_layer}'[/green3] [medium_spring_green]({service_spec.diag_layer_type})[/medium_spring_green]:"
        )

        if service_spec.new_services:
            rich_print()
            rich_print(" [blue]New services[/blue]")
            rich_print(
                build_service_table(sorted(service_spec.new_services, key=lambda s: s.short_name)))

        if service_spec.deleted_services:
            rich_print()
            rich_print(" [blue]Deleted services[/blue]")
            rich_print(
                build_service_table(
                    sorted(service_spec.deleted_services, key=lambda s: s.short_name)))

        if service_spec.renamed_services:
            rich_print()
            rich_print(" [blue]Renamed services[/blue]")
            services = [
                item.new_service_object for item in sorted(
                    service_spec.renamed_services, key=lambda item: item.new_service_name)
            ]
            old_names = [
                item.old_service_name for item in sorted(
                    service_spec.renamed_services, key=lambda item: item.new_service_name)
            ]
            rich_print(
                build_service_table(
                    services=services, additional_columns=[("Old service name", old_names)]))

        if service_spec.services_with_parameter_changes:
            rich_print()
            rich_print(" [blue]Services with parameter changes[/blue]")
            sorted_changes = sorted(
                service_spec.services_with_parameter_changes,
                key=lambda item: item.service.short_name)
            services = [item.service for item in sorted_changes]
            changed_param_column = [
                "\n".join([change.description
                           for change in item.changed_parameters_of_service])
                for item in sorted_changes
            ]

            table = build_service_table(
                services=services,
                additional_columns=[("Changed Parameters", changed_param_column)],
            )
            rich_print(RichPadding(table, pad=(0, 0, 0, 1)))

            for item in sorted_changes:
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
                        show_lines=True,
                    )
                    table.add_column("Attribute", style="light_cyan1")
                    table.add_column("Old Value", justify="left", style="light_goldenrod3")
                    table.add_column("New Value", justify="left", style="light_goldenrod3")

                    for value in param_changes.changed_attributes:
                        table.add_row(
                            value.attribute,
                            str(value.old_value) if value.old_value else "",
                            str(value.new_value) if value.new_value else "",
                        )
                    rich_print(RichPadding(table, pad=(0, 0, 0, 3)))

                if self.detailed:
                    print_service_parameters(item.service, allow_unknown_bit_lengths=True)

    def print_database_changes(self, changes_variants: SpecsChangesVariants) -> None:
        """
        Print changes detected between two databases.

        Args:
            changes_variants: All detected changes between two databases.
        """
        if changes_variants.new_diagnostic_layers:
            rich_print()
            rich_print("[blue]New diagnostic layers[/blue]:")
            for variant in sorted(
                    changes_variants.new_diagnostic_layers,
                    key=lambda x: (x.variant_type.value, x.short_name)):
                rich_print(
                    f" [green3]{variant.short_name}[/green3] [medium_spring_green]({variant.variant_type.value})[/medium_spring_green]"
                )

        if changes_variants.deleted_diagnostic_layers:
            rich_print()
            rich_print("[blue]Deleted diagnostic layers[/blue]:")
            for variant in sorted(
                    changes_variants.deleted_diagnostic_layers,
                    key=lambda x: (x.variant_type.value, x.short_name)):
                rich_print(
                    f" [green3]{variant.short_name}[/green3] [medium_spring_green]({variant.variant_type.value})[/medium_spring_green]"
                )

        if changes_variants.changed_diagnostic_layers:
            rich_print()
            rich_print("[blue]Changed diagnostic layers[/blue]: ")
            for value in sorted(
                    changes_variants.changed_diagnostic_layers,
                    key=lambda x: (x.diag_layer_type, x.diag_layer)):
                rich_print(
                    f" [green3]{value.diag_layer}[/green3] [medium_spring_green]({value.diag_layer_type})[/medium_spring_green]"
                )
            # Print changes of diagnostic services
            for value in sorted(
                    changes_variants.changed_diagnostic_layers,
                    key=lambda x: (x.diag_layer_type, x.diag_layer)):
                self.print_dl_changes(value)


class DiffEngine:
    """
    Core comparison engine for ODX diagnostic specifications.

    This class implements diagnostic comparison logic
    required for tracking changes across ODX files and ECU variants.

    Detection Capabilities:
    - New/Deleted/Changed diagnostic layers
    - New/Deleted/Renamed Services
    - request / response parameter comparison:
        - Name
        - Byte Position
        - Bit Length
        - Semantic
        - Parameter Type
        - Value
        - Data Type
        - Linked DOPs (Data Object Properties)
            - ID
            - Short Name
            - COMPU-METHOD
            - DIAG-CODED-TYPE
            - PHYSICAL-TYPE
            - INTERNAL-CONSTR
            - PHYS-CONSTR
            - Unit
            - DTCs
            - PHYS-CONST value
            - PHYSICAL-DEFAULT-VALUE

    Performance Features:
    - @profile decorator for method-level timing
    - Regex-based attribute filtering for noise reduction
    - Efficient object comparison with early exit

    Note:
        This class is designed for precision and reliability
        in detecting diagnostic specification changes. It prioritizes
        correctness over performance, with the @profile decorator providing
        insight into performance characteristics when needed.

    """

    def __init__(self,
                 ignore_patterns: Sequence[str] | None = None,
                 profile_enabled: bool = False) -> None:
        """
        Initialize the DiffEngine.

        Args:
            ignore_patterns: Regex patterns to ignore when comparing attributes.
                            Example: [r"Bit Length", r"Byte Position"] will
                            ignore all attributes containing these strings.
            profile_enabled: Whether to enable performance profiling.
        """
        self.ignore_regexes: list[re.Pattern[str]] = []
        self.profile_enabled = profile_enabled
        for pattern in (ignore_patterns or []):
            if not pattern:
                continue
            try:
                self.ignore_regexes.append(re.compile(pattern, re.IGNORECASE))
            except re.error as exc:
                raise ValueError(f"Invalid ignore regex '{pattern}': {exc}") from exc

    @profile
    def compare_databases(
        self,
        database_new: Database,
        database_old: Database,
        layer_filter: set[str] | None = None,
    ) -> SpecsChangesVariants | None:
        """
        Compare two ODX databases (PDX files).

        This method performs a detailed comparison between two diagnostic databases,
        detecting new, deleted, and changed diagnostic layers across versions.

        Args:
            database_new: The newer database to compare against the baseline.
            database_old: The older baseline database.
            layer_filter: Optional set of diagnostic layer names to include.

        Returns:
            SpecsChangesVariants containing all detected changes, or None if
            no changes are found.
        """
        old_layers = {dl.short_name: dl for dl in database_old.diag_layers}
        new_layers = {dl.short_name: dl for dl in database_new.diag_layers}

        if layer_filter is None:
            layer_filter = set(old_layers) | set(new_layers)

        new_layer_names = sorted(
            name for name in new_layers if name not in old_layers and name in layer_filter)
        deleted_layer_names = sorted(
            name for name in old_layers if name not in new_layers and name in layer_filter)
        common_layer_names = sorted(
            name for name in new_layers if name in old_layers and name in layer_filter)

        new_variants = [new_layers[name] for name in new_layer_names]
        deleted_variants = [old_layers[name] for name in deleted_layer_names]
        changed_variants: list[DiagLayerChanges] = []

        for name in common_layer_names:
            dl_new = new_layers[name]
            dl_old = old_layers[name]
            if (layer_changes := self.compare_diagnostic_layers(dl_new, dl_old)):
                changed_variants.append(layer_changes)

        if new_variants or deleted_variants or changed_variants:
            return SpecsChangesVariants(
                new_diagnostic_layers=new_variants,
                deleted_diagnostic_layers=deleted_variants,
                changed_diagnostic_layers=changed_variants,
            )
        return None

    @profile
    def compare_diagnostic_layers(self, dl_new: DiagLayer,
                                  dl_old: DiagLayer) -> DiagLayerChanges | None:
        """
        Compare diagnostic services of two diagnostic layers.

        Detects new services, deleted services, renamed services (via prefix + signature),
        and services with parameter changes.

        Args:
            dl_new: The newer diagnostic layer.
            dl_old: The older diagnostic layer.

        Returns:
            DiagLayerChanges containing all detected changes, or None if no changes.
        """
        # TODO: add comparison of SingleECUJobs
        new_services: list[DiagService] = []
        deleted_services: list[DiagService] = []
        renamed_services: list[RenamedService] = []
        services_with_param_changes: list[ServiceChanges] = []

        dl_new_by_name, dl_new_by_prefix = self._build_service_maps(dl_new.services)
        dl_old_by_name, dl_old_by_prefix = self._build_service_maps(dl_old.services)

        for service_new in sorted(dl_new.services, key=lambda s: s.short_name):
            service_old = dl_old_by_name.get(service_new.short_name)
            if service_old is not None:
                if (service_changes := self.compare_services(service_new, service_old)):
                    services_with_param_changes.append(service_changes)
                continue

            prefix = self._service_prefix(service_new)
            # check whether names of diagnostic services have changed
            # (this will not work in cases where the constant prefix of a request was modified)
            service_old = self._unique_prefix_match(dl_old_by_prefix, prefix)
            if service_old is not None and service_old.short_name not in dl_new_by_name:
                if self._service_signature(service_new) == self._service_signature(service_old):
                    renamed_services.append(
                        RenamedService(
                            old_service_name=service_old.short_name,
                            new_service_object=service_new,
                        ))
                    if (service_changes := self.compare_services(service_new, service_old)):
                        services_with_param_changes.append(service_changes)
                    continue

            new_services.append(service_new)

        for service_old in sorted(dl_old.services, key=lambda s: s.short_name):
            if service_old.short_name in dl_new_by_name:
                continue
            prefix = self._service_prefix(service_old)
            if self._unique_prefix_match(dl_new_by_prefix, prefix) is not None:
                continue
            deleted_services.append(service_old)

        if new_services or deleted_services or renamed_services or services_with_param_changes:
            return DiagLayerChanges(
                diag_layer=dl_new.short_name,
                diag_layer_type=dl_new.variant_type.value,
                new_services=sorted(new_services, key=lambda s: s.short_name),
                deleted_services=sorted(deleted_services, key=lambda s: s.short_name),
                renamed_services=sorted(renamed_services, key=lambda item: item.new_service_name),
                services_with_parameter_changes=sorted(
                    services_with_param_changes, key=lambda item: item.service.short_name),
            )
        return None

    @profile
    def compare_services(self, service_new: DiagService,
                         service_old: DiagService) -> ServiceChanges | None:
        """
        Compare request, positive response and negative response parameters of two diagnostic services.

        Args:
            service_new: The newer service.
            service_old: The older service.

        Returns:
            ServiceChanges containing all detected changes, or None if no changes.
        """
        changed_params: list[ParameterChanges] = []

        changed_params.extend(
            self._compare_request_block(service_new.request, service_old.request,
                                        service_old.short_name))

        changed_params.extend(
            self._compare_response_block(
                service_new.positive_responses,
                service_old.positive_responses,
                "positive",
                service_old.short_name,
            ))

        changed_params.extend(
            self._compare_response_block(
                service_new.negative_responses,
                service_old.negative_responses,
                "negative",
                service_old.short_name,
            ))

        if changed_params:
            return ServiceChanges(service=service_new, changed_parameters_of_service=changed_params)
        return None

    @profile
    def compare_parameters(self, param_new: Parameter,
                           param_old: Parameter) -> list[ParameterAttributeChanges]:
        """
        Checks whether properties of param_new and param_old differ
        Compared properties:
        - Short Name
        - Byte Position
        - Bit Length
        - Semantic
        - Parameter Type
        - Value (CODED-CONST, NRC-CONST, PHYS-CONST, PHYSICAL-DEFAULT-VALUE)
        - Data Type
        - Data Object Property
        """
        changed_attributes: list[ParameterAttributeChanges] = []

        self._append_attribute_change(
            changed_attributes,
            "Parameter Name",
            param_old.short_name,
            param_new.short_name,
        )
        self._append_attribute_change(
            changed_attributes,
            "Byte Position",
            param_old.byte_position,
            param_new.byte_position,
        )
        self._append_attribute_change(
            changed_attributes,
            "Bit Length",
            param_old.get_static_bit_length(),
            param_new.get_static_bit_length(),
        )
        self._append_attribute_change(
            changed_attributes,
            "Semantic",
            param_old.semantic,
            param_new.semantic,
        )
        self._append_attribute_change(
            changed_attributes,
            "Parameter Type",
            param_old.parameter_type,
            param_new.parameter_type,
        )

        if isinstance(param_new, CodedConstParameter) and isinstance(param_old,
                                                                     CodedConstParameter):
            self._compare_coded_const(param_new, param_old, changed_attributes)
        elif isinstance(param_new, NrcConstParameter) and isinstance(param_old, NrcConstParameter):
            self._compare_nrc_const(param_new, param_old, changed_attributes)
        elif isinstance(param_new, ParameterWithDOP) and isinstance(param_old, ParameterWithDOP):
            self._compare_parameter_with_dop(param_new, param_old, changed_attributes)

        return changed_attributes

    def _compare_coded_const(
        self,
        new_param: CodedConstParameter,
        old_param: CodedConstParameter,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare parameters of type CODED-CONST.

        Compares:
        - Data Type
        - Coded Value (formatted as hex for integer values)

        Args:
            new_param: The newer CodedConstParameter.
            old_param: The older CodedConstParameter.
            changed_attributes: List to append detected changes to.
        """
        self._append_attribute_change(
            changed_attributes,
            "Data Type",
            old_param.diag_coded_type.base_data_type.name,
            new_param.diag_coded_type.base_data_type.name,
        )
        if new_param.coded_value != old_param.coded_value:
            if isinstance(new_param.coded_value, int) and isinstance(old_param.coded_value, int):
                self._append_attribute_change(
                    changed_attributes,
                    "Value (CODED-CONST)",
                    self._format_hex(old_param.coded_value, old_param.get_static_bit_length()),
                    self._format_hex(new_param.coded_value, new_param.get_static_bit_length()),
                )
            else:
                self._append_attribute_change(
                    changed_attributes,
                    "Value (CODED-CONST)",
                    repr(old_param.coded_value),
                    repr(new_param.coded_value),
                )

    def _compare_nrc_const(
        self,
        new_param: NrcConstParameter,
        old_param: NrcConstParameter,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare parameters of type NRC-CONST.

        Compares:
        - Data Type
        - Coded Values (list of NRC values)

        Args:
            new_param: The newer NrcConstParameter.
            old_param: The older NrcConstParameter.
            changed_attributes: List to append detected changes to.
        """
        self._append_attribute_change(
            changed_attributes,
            "Data Type",
            old_param.diag_coded_type.base_data_type.name,
            new_param.diag_coded_type.base_data_type.name,
        )
        self._append_attribute_change(
            changed_attributes,
            "Values (NRC-CONST)",
            old_param.coded_values,
            new_param.coded_values,
        )

    def _compare_parameter_with_dop(
        self,
        new_param: ParameterWithDOP,
        old_param: ParameterWithDOP,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare parameters that reference DOPs with detailed DOP traversal.

        Compares:
        - DOP object (via compare_dops)
        - PHYS-CONST value (if PhysicalConstantParameter)
        - PHYSICAL-DEFAULT-VALUE (if ValueParameter)

        Args:
            new_param: The newer ParameterWithDOP.
            old_param: The older ParameterWithDOP.
            changed_attributes: List to append detected changes to.
        """
        changed_attributes.extend(self.compare_dops(new_param.dop, old_param.dop))
        if isinstance(new_param, PhysicalConstantParameter) and isinstance(
                old_param, PhysicalConstantParameter):
            if new_param.physical_constant_value != old_param.physical_constant_value:
                if isinstance(new_param.physical_constant_value, int) and isinstance(
                        old_param.physical_constant_value, int):
                    self._append_attribute_change(
                        changed_attributes,
                        "Value (PHYS-CONST)",
                        self._format_hex(old_param.physical_constant_value,
                                         old_param.get_static_bit_length()),
                        self._format_hex(new_param.physical_constant_value,
                                         new_param.get_static_bit_length()),
                    )
                else:
                    self._append_attribute_change(
                        changed_attributes,
                        "Value (PHYS-CONST)",
                        repr(old_param.physical_constant_value),
                        repr(new_param.physical_constant_value),
                    )
        if isinstance(new_param, ValueParameter) and isinstance(old_param, ValueParameter):
            if new_param.physical_default_value != old_param.physical_default_value:
                if isinstance(new_param.physical_default_value, int) and isinstance(
                        old_param.physical_default_value, int):
                    self._append_attribute_change(
                        changed_attributes,
                        "Value (PHYSICAL-DEFAULT-VALUE)",
                        self._format_hex(old_param.physical_default_value,
                                         old_param.get_static_bit_length()),
                        self._format_hex(new_param.physical_default_value,
                                         new_param.get_static_bit_length()),
                    )
                else:
                    self._append_attribute_change(
                        changed_attributes,
                        "Value (PHYSICAL-DEFAULT-VALUE)",
                        repr(old_param.physical_default_value),
                        repr(new_param.physical_default_value),
                    )

    @profile
    def compare_dops(self, dop_new: DopBase, dop_old: DopBase) -> list[ParameterAttributeChanges]:
        """
        Compare two Data Object Properties (DOPs).

        Compares:
        - ID
        - Short Name
        - COMPU-METHOD (for DataObjectProperty and DtcDop)
        - DIAG-CODED-TYPE (for DataObjectProperty and DtcDop)
        - PHYSICAL-TYPE (for DataObjectProperty and DtcDop)
        - INTERNAL-CONSTR (for DataObjectProperty)
        - PHYS-CONSTR (for DataObjectProperty)
        - Unit (for DataObjectProperty)
        - DTCs (for DtcDop)

        Args:
            dop_new: The newer DOP.
            dop_old: The older DOP.

        Returns:
            List of ParameterAttributeChanges, empty if no changes.
        """
        if dop_new == dop_old:
            return []

        changed_attributes: list[ParameterAttributeChanges] = []
        self._append_attribute_change(
            changed_attributes,
            "Linked Data Object Property (DOP) Object",
            "<Old DOP>",
            "<New DOP>",
        )
        # DOP ID
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP: ID",
            dop_old.odx_id.local_id,
            dop_new.odx_id.local_id,
        )
        # DOP Name
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP: Short Name",
            dop_old.short_name,
            dop_new.short_name,
        )
        # compare COMPU-METHOD, DIAG-CODED-TYPE and PHYSICAL-TYPE of DOP
        if (isinstance(dop_new, DataObjectProperty) and isinstance(dop_old, DataObjectProperty)) or \
           (isinstance(dop_new, DtcDop) and isinstance(dop_old, DtcDop)):
            self._compare_compu_method(dop_new, dop_old, changed_attributes)
            self._compare_diag_coded_type(dop_new, dop_old, changed_attributes)
            self._compare_physical_type(dop_new, dop_old, changed_attributes)
        # compare INTERNAL-CONSTR, PHYS-CONSTR and Unit of DOP
        if isinstance(dop_new, DataObjectProperty) and isinstance(dop_old, DataObjectProperty):
            self._compare_internal_constraints(dop_new, dop_old, changed_attributes)
            self._compare_unit(dop_new.unit, dop_old.unit, changed_attributes)
        # compare DTCs of DOP
        if isinstance(dop_new, DtcDop) and isinstance(dop_old, DtcDop):
            self._compare_dtcs(dop_new, dop_old, changed_attributes)

        return changed_attributes

    def _compare_compu_method(
        self,
        dop_new: DataObjectProperty | DtcDop,
        dop_old: DataObjectProperty | DtcDop,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare COMPU-METHOD (computation method) of two Data Object Properties.

        The computation method defines how raw (coded) values are converted to
        physical values and vice versa. This comparison detects changes in the
        specified conversion mechanisms applied to diagnostic parameters.

        Args:
            dop_new: The newer DOP containing the computation method to compare.
            dop_old: The older DOP containing the reference computation method.
            changed_attributes: Accumulator list for detected attribute changes.

        Note:
            Currently compares only method existence. Future enhancement:
            Compare internal structure of CompuMethod (category, scales, default value, ...).
        """
        # TODO compare sub-attributes of CompuMethod
        if dop_new.compu_method != dop_old.compu_method:
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: Computation Method",
                "<OLD COMPU-METHOD>",
                "<NEW COMPU-METHOD>",
            )

    def _compare_diag_coded_type(
        self,
        dop_new: DataObjectProperty | DtcDop,
        dop_old: DataObjectProperty | DtcDop,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare DIAG-CODED-TYPE (diagnostic coded type) attributes of two DOPs.

        The DIAG-CODED-TYPE defines how diagnostic data is physically encoded
        in the communication frame, including bit ordering, byte ordering,
        and the fundamental data type representation.

        This comparison detects changes in:
        - Base Type Encoding: How the data is physically represented
        - Base Data Type: The fundamental data type (e.g., A_UINT32, A_INT16)
        - Type: Specific type of DIAG-CODED-TYPE

        Args:
            dop_new: The newer DOP with the diagnostic coded type to compare.
            dop_old: The older DOP with the reference diagnostic coded type.
            changed_attributes: Accumulator list for detected attribute changes.

        """
        if dop_new.diag_coded_type != dop_old.diag_coded_type:
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: DIAG-CODED-TYPE: Base Type Encoding",
                dop_old.diag_coded_type.base_type_encoding,
                dop_new.diag_coded_type.base_type_encoding,
            )
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: DIAG-CODED-TYPE: Base Data Type",
                dop_old.diag_coded_type.base_data_type.name,
                dop_new.diag_coded_type.base_data_type.name,
            )
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: DIAG-CODED-TYPE: Type",
                dop_old.diag_coded_type.dct_type,
                dop_new.diag_coded_type.dct_type,
            )

    def _compare_physical_type(
        self,
        dop_new: DataObjectProperty | DtcDop,
        dop_old: DataObjectProperty | DtcDop,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare PHYSICAL-TYPE (physical type) attributes of two DOPs.

        The PHYSICAL-TYPE defines how physical values are presented to the user,
        including precision and display formatting.

        This comparison detects changes in:
        - Precision: Number of decimal places displayed
        - Base Data Type: The fundamental data type for physical representation
        - Display Radix: Number base for display (decimal, hex, octal, binary)

        Args:
            dop_new: The newer DOP with the physical type to compare.
            dop_old: The older DOP with the reference physical type.
            changed_attributes: Accumulator list for detected attribute changes.
        """
        if dop_new.physical_type != dop_old.physical_type:
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: PHYSICAL-TYPE: Precision",
                dop_old.physical_type.precision,
                dop_new.physical_type.precision,
            )
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: PHYSICAL-TYPE: Base data type",
                dop_old.physical_type.base_data_type.name,
                dop_new.physical_type.base_data_type.name,
            )
            display_radix_old = dop_old.physical_type.display_radix.name if dop_old.physical_type.display_radix else ""
            display_radix_new = dop_new.physical_type.display_radix.name if dop_new.physical_type.display_radix else ""
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: PHYSICAL-TYPE: Display Radix",
                display_radix_old,
                display_radix_new,
            )

    def _compare_internal_constraints(
        self,
        dop_new: DataObjectProperty,
        dop_old: DataObjectProperty,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare INTERNAL-CONSTR (internal constraints) and PHYS-CONSTR
        (physical constraints) of two DataObjectProperty objects.

        Internal constraints define the valid range of internal
        values. Physical constraints define the valid range of numeric
        physical values.

        This comparison delegates to the constraint object comparator to
        detect changes in lower/upper limits and scale constraints.

        Args:
            dop_new: The newer DOP with constraints to compare.
            dop_old: The older DOP with reference constraints.
            changed_attributes: Accumulator list for detected attribute changes.
        """
        self._compare_constr_object(
            dop_new.internal_constr,
            dop_old.internal_constr,
            "INTERNAL-CONSTR",
            changed_attributes,
        )
        self._compare_constr_object(
            dop_new.physical_constr,
            dop_old.physical_constr,
            "PHYS-CONSTR",
            changed_attributes,
        )

    def _compare_constr_object(
        self,
        new_constr: InternalConstr | None,
        old_constr: InternalConstr | None,
        constr_type: str,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compares two objects of type 'InternalConstr'
        Compares attributes: lower_limit, upper_limit, scale_constrs
        """
        if new_constr == old_constr:
            return

        self._append_attribute_change(
            changed_attributes,
            f"Linked DOP: {constr_type}",
            f"<Old {constr_type}>" if old_constr else "",
            f"<New {constr_type}>" if new_constr else "",
        )
        if new_constr is None or old_constr is None:
            return

        self._compare_limit(
            new_constr.lower_limit,
            old_constr.lower_limit,
            f"Linked DOP object: {constr_type}: Lower Limit",
            changed_attributes,
        )
        self._compare_limit(
            new_constr.upper_limit,
            old_constr.upper_limit,
            f"Linked DOP object: {constr_type}: Upper Limit",
            changed_attributes,
        )
        if new_constr.scale_constrs != old_constr.scale_constrs:
            self._append_attribute_change(
                changed_attributes,
                f"Linked DOP object: {constr_type}: Scale Constraints",
                "<Old list of SCALE-CONSTR objects>",
                "<New list of SCALE-CONSTR objects>",
            )

    def _compare_limit(
        self,
        new_limit: Limit | None,
        old_limit: Limit | None,
        attribute_name: str,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """Compares two objects of type 'Limit'"""
        if new_limit == old_limit:
            return

        self._append_attribute_change(
            changed_attributes,
            attribute_name,
            "<Old LIMIT Object>" if old_limit else "",
            "<New LIMIT Object>" if new_limit else "",
        )
        if new_limit is None or old_limit is None:
            return

        if new_limit.value != old_limit.value:
            self._append_attribute_change(
                changed_attributes,
                f"{attribute_name}: Value",
                old_limit.value,
                new_limit.value,
            )
        if new_limit.value_type != old_limit.value_type:
            self._append_attribute_change(
                changed_attributes,
                f"{attribute_name}: Value Type",
                old_limit.value_type,
                new_limit.value_type,
            )

    def _compare_unit(
        self,
        new_unit: Unit | None,
        old_unit: Unit | None,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Checks whether properties of new_unit and old_unit differ.

        Compared properties:
        - short_name
        - display_name
        - factor_si_to_unit
        - offset_si_to_unit
        - physical_dimension
        """
        if old_unit == new_unit:
            return

        self._append_attribute_change(
            changed_attributes,
            "Linked DOP: UNIT",
            "<Old UNIT Object>" if old_unit else "",
            "<New UNIT Object>" if new_unit else "",
        )
        if new_unit is None or old_unit is None:
            return

        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: ID",
            f"<{old_unit.odx_id.local_id}>",
            f"<{new_unit.odx_id.local_id}>",
        )
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: Name",
            old_unit.short_name,
            new_unit.short_name,
        )
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: Display name",
            old_unit.display_name,
            new_unit.display_name,
        )
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: FACTOR-SI-TO-UNIT",
            old_unit.factor_si_to_unit or "",
            new_unit.factor_si_to_unit or "",
        )
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: OFFSET-SI-TO-UNIT",
            old_unit.offset_si_to_unit or "",
            new_unit.offset_si_to_unit or "",
        )
        self._append_attribute_change(
            changed_attributes,
            "Linked DOP object: Unit: Physical dimension",
            "<Old PHYSICAL-DIMENSION>" if old_unit.physical_dimension else "",
            "<New PHYSICAL-DIMENSION>" if new_unit.physical_dimension else "",
        )

    def _compare_dtcs(
        self,
        dop_new: DtcDop,
        dop_old: DtcDop,
        changed_attributes: list[ParameterAttributeChanges],
    ) -> None:
        """
        Compare DTC lists of two DtcDop objects.

        Args:
            dop_new: The newer DtcDop.
            dop_old: The older DtcDop.
            changed_attributes: List to append detected changes to.
        """
        if dop_new.dtcs != dop_old.dtcs:
            self._append_attribute_change(
                changed_attributes,
                "Linked DOP object: List of DTCs",
                "<Old list of DTC objects>",
                "<New list of DTC objects>",
            )

    def _append_attribute_change(
        self,
        changed_attributes: list[ParameterAttributeChanges],
        attribute: str,
        old_value: AtomicOdxType | Sequence[AtomicOdxType] | Encoding | DataType | None,
        new_value: AtomicOdxType | Sequence[AtomicOdxType] | Encoding | DataType | None,
    ) -> None:
        """
        Append an attribute change to the accumulation list if values differ
        and the attribute is not matched by any ignore pattern.

        This is the canonical entry point for all attribute change tracking
        in the comparison engine. It ensures consistent handling of changes
        across all comparison operations.

        Args:
            changed_attributes: Accumulator list for detected attribute changes.
            attribute: The fully qualified name of the attribute being compared.
            old_value: The attribute value from the baseline object.
            new_value: The attribute value from the comparison target object.

        Note:
            This method handles complex value types (sequences, encodings)
            and ensures proper type safety in the comparison pipeline.
        """
        if old_value == new_value:
            return
        if self._matches_ignore(attribute):
            return
        changed_attributes.append(
            ParameterAttributeChanges(
                attribute=attribute, old_value=old_value, new_value=new_value))

    def _matches_ignore(self, attribute: str) -> bool:
        """
        Determine whether an attribute should be ignored in comparison results.

        This method applies the user-supplied regex patterns to filter out
        noisy or irrelevant attribute changes from the comparison report.

        Args:
            attribute: The fully qualified attribute name to check.

        Returns:
            True if the attribute matches any ignore pattern and should be
            excluded from the comparison results. False otherwise.
        """
        if not self.ignore_regexes:
            return False
        return any(regex.search(attribute) for regex in self.ignore_regexes)

    def _compare_request_block(
        self,
        request_new: Request | None,
        request_old: Request | None,
        service_name: str,
    ) -> list[ParameterChanges]:
        """
        Compare request parameters of two services.

        Args:
            request_new: The newer request.
            request_old: The older request.
            service_name: Name of the diagnostic service the request is associated with.

        Returns:
            List of ParameterChanges, empty if no changes.
        """
        changed_params: list[ParameterChanges] = []
        if request_new is None or request_old is None:
            if request_new is not None or request_old is not None:
                changed_params.append(
                    ParameterChanges(
                        description=f"Request for service [magenta]'{service_name}'[/magenta] is not identical, exactly one of the requests is None.",
                        changed_attributes=[
                            ParameterAttributeChanges(
                                attribute="Request parameter list",
                                old_value=[x.short_name for x in request_old.parameters]
                                if request_old else [],
                                new_value=[x.short_name for x in request_new.parameters]
                                if request_new else [],
                            )
                        ],
                    ))
            return changed_params

        params_new = request_new.parameters
        params_old = request_old.parameters
        new_map = {param.short_name: param for param in params_new}
        old_map = {param.short_name: param for param in params_old}
        all_names = sorted(set(new_map) | set(old_map))

        if new_map.keys() != old_map.keys():
            changed_params.append(
                ParameterChanges(
                    description=f"List of request parameters for service [magenta]'{service_name}'[/magenta] is not identical",
                    changed_attributes=[
                        ParameterAttributeChanges(
                            attribute="Request parameter list",
                            old_value=[x.short_name for x in params_old],
                            new_value=[x.short_name for x in params_new],
                        )
                    ],
                ))

        for name in all_names:
            if name not in new_map or name not in old_map:
                continue
            param_new = new_map[name]
            param_old = old_map[name]
            if (param_changes := self.compare_parameters(param_new, param_old)):
                changed_params.append(
                    ParameterChanges(
                        description=(
                            f"Properties of request parameter [light_slate_grey]'{name}'[/light_slate_grey] have changed"
                        ),
                        changed_attributes=param_changes,
                    ))
        return changed_params

    def _compare_response_block(
        self,
        responses_new: NamedItemList[Response],
        responses_old: NamedItemList[Response],
        response_type: str,
        service_name: str,
    ) -> list[ParameterChanges]:
        """
        Compare response parameters of two services.

        Args:
            responses_new: The newer responses.
            responses_old: The older responses.
            response_type: 'positive' or 'negative'.
            service_name: Name of the diagnostic service the response is associated with.

        Returns:
            List of ParameterChanges, empty if no changes.
        """
        changed_params: list[ParameterChanges] = []
        new_map = {response.short_name: response for response in responses_new}
        old_map = {response.short_name: response for response in responses_old}
        all_response_names = sorted(set(new_map) | set(old_map))

        if new_map.keys() != old_map.keys():
            changed_params.append(
                ParameterChanges(
                    description=f"List of {response_type} responses for service [magenta]'{service_name}'[/magenta] is not identical",
                    changed_attributes=[
                        ParameterAttributeChanges(
                            attribute=f"{response_type.capitalize()} responses list",
                            old_value=[x.short_name for x in responses_old],
                            new_value=[x.short_name for x in responses_new],
                        )
                    ],
                ))

        for response_name in all_response_names:
            if response_name not in new_map or response_name not in old_map:
                continue
            response_new = new_map[response_name]
            response_old = old_map[response_name]
            params_new = response_new.parameters
            params_old = response_old.parameters
            param_new_map = {param.short_name: param for param in params_new}
            param_old_map = {param.short_name: param for param in params_old}
            all_param_names = sorted(set(param_new_map) | set(param_old_map))

            if param_new_map.keys() != param_old_map.keys():
                changed_params.append(
                    ParameterChanges(
                        description=f"List of {response_type} response parameters for service [magenta]'{service_name}'[/magenta] is not identical",
                        changed_attributes=[
                            ParameterAttributeChanges(
                                attribute=f"{response_type.capitalize()} response parameter list",
                                old_value=[x.short_name for x in params_old],
                                new_value=[x.short_name for x in params_new],
                            )
                        ],
                    ))

            for param_name in all_param_names:
                if param_name not in param_new_map or param_name not in param_old_map:
                    continue
                param_new = param_new_map[param_name]
                param_old = param_old_map[param_name]
                if (param_changes := self.compare_parameters(param_new, param_old)):
                    changed_params.append(
                        ParameterChanges(
                            description=(
                                f"Properties of {response_type} response parameter [light_slate_grey]'{param_name}'[/light_slate_grey] have changed"
                            ),
                            changed_attributes=param_changes,
                        ))
        return changed_params

    def _service_prefix(self, service: DiagService) -> bytes | None:
        """
        Get the coded constant prefix of a service for rename detection.

        The prefix is the constant byte sequence that identifies the service
        request in the diagnostic communication frame. This is used for
        intelligent rename detection when service names change but the
        underlying protocol identifier remains the same.

        Args:
            service: The diagnostic service to extract the prefix from.

        Returns:
            The coded constant prefix as bytes, or None if:
            - The service has no request object
            - The request has no coded constant prefix

        Note:
            This method is critical for the rename detection algorithm.
            Without this, service renames would be incorrectly flagged
            as new services + deleted services.
        """
        if service.request is None:
            return None
        prefix = service.request.coded_const_prefix()
        if not prefix:
            return None
        return bytes(prefix)

    def _service_signature(self, service: DiagService
                          ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        """
        Get the signature of a service for intelligent rename detection.

        The signature consists of three components that together identify a
        service's interface without relying on its name:

        Signature Components:
        1. Request Parameter Names: The ordered list of parameter names
            in the request structure.
        2. Positive Response Names: The ordered list of positive response
            names that the service can return.
        3. Negative Response Names: The ordered list of negative response
            names that the service can return.

        Args:
            service: The diagnostic service to generate a signature for.

        Returns:
            A tuple of three tuples:
            (request_parameters, positive_response_names, negative_response_names)
        """
        request_parameters = tuple(
            param.short_name for param in service.request.parameters) if service.request else ()
        positive_response_names = tuple(
            response.short_name for response in service.positive_responses)
        negative_response_names = tuple(
            response.short_name for response in service.negative_responses)
        return request_parameters, positive_response_names, negative_response_names

    def _build_service_maps(
        self, services: list[DiagService]
    ) -> tuple[dict[str, DiagService], dict[bytes | None, list[DiagService]]]:
        """
        Build name and prefix maps for services.

        Args:
            services: List of diagnostic services.

        Returns:
            Tuple of (name_map, prefix_map) where:
            - name_map: short_name -> DiagService
            - prefix_map: coded_const_prefix -> list of DiagService
        """
        by_name: dict[str, DiagService] = {}
        by_prefix: dict[bytes | None, list[DiagService]] = {}
        for service in services:
            by_name[service.short_name] = service
            prefix = self._service_prefix(service)
            by_prefix.setdefault(prefix, []).append(service)
        return by_name, by_prefix

    def _unique_prefix_match(self, prefix_map: dict[bytes | None, list[DiagService]],
                             prefix: bytes | None) -> DiagService | None:
        """
        Find a unique service matching a prefix.

        Args:
            prefix_map: Map of prefix -> list of services.
            prefix: The prefix to match.

        Returns:
            The matching service if unique, otherwise None.
        """
        if prefix not in prefix_map:
            return None
        services = prefix_map[prefix]
        if len(services) != 1:
            return None
        return services[0]

    def _format_hex(self, value: int | None, bit_length: int | None) -> str:
        """
        Format an integer value as a hexadecimal string with appropriate width.

        This method ensures consistent hexadecimal representation of raw
        diagnostic values across all comparison outputs. The width is
        determined by the bit_length parameter to maintain alignment
        and readability in comparison reports.

        Args:
            value: The integer value to format. Returns empty string if None.
            bit_length: The bit length of the original data type, used to
                    determine the hex string width (nibble alignment).

        Returns:
            A formatted hex string (e.g., "0xFF", "0x00FF", "0x0000FFFF")
            or an empty string if value is None.

        Example:
            >>> _format_hex(255, 8)
            "0xFF"
            >>> _format_hex(65535, 16)
            "0xFFFF"

        Note:
            The width calculation ensures that the hex representation
            is properly aligned for the original bit length.
        """
        if value is None:
            return ""
        width = max(1, -(-(bit_length or 0) // 4))
        return f"0x{value:0{width}X}"


class Exporter(ABC):
    """
    Abstract base class for exporting comparison results.

    This class defines the contract for all export format implementations.
    Each concrete exporter must implement the export method to serialize
    SpecsChangesVariants data to a specific format.

    Implementations:
    - JsonExporter: Structured JSON format for programmatic consumption
    - TextExporter: Human-readable text format for console output
    - YamlExporter: Human-readable YAML format with rich structure
    - CsvExporter: Flat CSV format for spreadsheet analysis
    """

    @abstractmethod
    def export(self, data: SpecsChangesVariants, target: Path | None) -> Path:
        """
        Export comparison data to a file.

        Args:
            data: The comparison results to export.
            target: The target file path. If None, a default path is used.

        Returns:
            The actual Path where the data was written.

        Raises:
            NotImplementedError: This is an abstract method that must be
            implemented by concrete subclasses.
        """
        raise NotImplementedError


class JsonExporter(Exporter):

    @override
    def export(self, data: SpecsChangesVariants, target: Path | None) -> Path:
        destination = Path(target) if target else Path.cwd() / "compare-report.json"
        with destination.open("w", encoding="utf-8") as handle:
            json.dump(data.to_dict(), handle, indent=2)
        return destination


class TextExporter(Exporter):

    @override
    def export(self, data: SpecsChangesVariants, target: Path | None) -> Path:
        destination = Path(target) if target else None
        output = self._render_report(data)
        if destination:
            with destination.open("w", encoding="utf-8") as handle:
                handle.write(output)
            return destination

        rich_print(output)
        return Path("stdout")

    def _render_report(self, data: SpecsChangesVariants) -> str:
        lines = self._render_summary(data)
        lines.append("")  # blank line before details
        lines.extend(self._render_details(data))
        return "\n".join(lines)

    def _render_summary(self, data: SpecsChangesVariants) -> list[str]:
        lines: list[str] = ["Comparison report summary:"]
        lines.append(f"New diagnostic layers: {len(data.new_diagnostic_layers)}")
        lines.append(f"Deleted diagnostic layers: {len(data.deleted_diagnostic_layers)}")
        lines.append(f"Changed diagnostic layers: {len(data.changed_diagnostic_layers)}")
        lines.append(f"Total change score: {data.summary['total_change_score']}")

        if data.new_diagnostic_layers:
            lines.append("\nNew diagnostic layers:")
            for layer in sorted(
                    data.new_diagnostic_layers, key=lambda x: (x.variant_type.value, x.short_name)):
                lines.append(f"  - {layer.short_name} ({layer.variant_type.value})")

        if data.deleted_diagnostic_layers:
            lines.append("\nDeleted diagnostic layers:")
            for layer in sorted(
                    data.deleted_diagnostic_layers, key=lambda x:
                (x.variant_type.value, x.short_name)):
                lines.append(f"  - {layer.short_name} ({layer.variant_type.value})")

        if data.changed_diagnostic_layers:
            lines.append("\nChanged diagnostic layers:")
            for layer_changes in data.changed_diagnostic_layers:
                lines.append(f"  - {layer_changes.diag_layer} ({layer_changes.diag_layer_type})")
        return lines

    def _render_details(self, data: SpecsChangesVariants) -> list[str]:
        lines: list[str] = []
        if not data.changed_diagnostic_layers:
            return lines

        lines.append("Detailed changes:")
        for layer_changes in data.changed_diagnostic_layers:
            lines.append(
                f"\nDiagnostic layer: {layer_changes.diag_layer} ({layer_changes.diag_layer_type})")

            if layer_changes.new_services:
                lines.append("\n  New services:")
                for service in sorted(layer_changes.new_services, key=lambda s: s.short_name):
                    lines.append(f"    - {service.short_name}")

            if layer_changes.deleted_services:
                lines.append("\n  Deleted services:")
                for service in sorted(layer_changes.deleted_services, key=lambda s: s.short_name):
                    lines.append(f"    - {service.short_name}")

            if layer_changes.renamed_services:
                lines.append("\n  Renamed services:")
                for renamed in sorted(
                        layer_changes.renamed_services, key=lambda item: item.new_service_name):
                    lines.append(f"    - {renamed.old_service_name} -> {renamed.new_service_name}")

            if layer_changes.services_with_parameter_changes:
                lines.append("\n  Services with parameter changes:")
                for service_change in sorted(
                        layer_changes.services_with_parameter_changes,
                        key=lambda item: item.service.short_name):
                    lines.append(f"\n    Service: {service_change.service.short_name}")
                    for param_change in service_change.changed_parameters_of_service:
                        lines.append(f"      {_strip_rich_formatting(param_change.description)}")
                        for attr in param_change.changed_attributes:
                            old_val = str(attr.old_value) if attr.old_value is not None else ""
                            new_val = str(attr.new_value) if attr.new_value is not None else ""
                            lines.append(
                                f"        {attr.attribute}: {old_val if old_val else '<<undefined>>'} -> {new_val if new_val else '<<undefined>>'}"
                            )
        return lines


class YamlExporter(Exporter):

    @override
    def export(self, data: SpecsChangesVariants, target: Path | None) -> Path:
        if yaml is None:
            raise RuntimeError(
                "YAML export requires PyYAML. Install it to use --output-format yaml.")
        destination = Path(target) if target else Path.cwd() / "compare-report.yaml"
        with destination.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data.to_dict(), handle, sort_keys=False)
        return destination


class CsvExporter(Exporter):

    @override
    def export(self, data: SpecsChangesVariants, target: Path | None) -> Path:
        destination = Path(target) if target else Path.cwd() / "compare-report.csv"
        rows: list[list[str]] = [[
            "category", "diag_layer", "service", "attribute", "old_value", "new_value"
        ]]

        for layer in sorted(
                data.new_diagnostic_layers, key=lambda x: (x.variant_type.value, x.short_name)):
            rows.append([
                "new_diagnostic_layer",
                layer.short_name,
                "",
                "NEW_DIAGNOSTIC_LAYER",
                "",
                "",
            ])

        for layer in sorted(
                data.deleted_diagnostic_layers, key=lambda x: (x.variant_type.value, x.short_name)):
            rows.append([
                "deleted_diagnostic_layer",
                layer.short_name,
                "",
                "DELETED_DIAGNOSTIC_LAYER",
                "",
                "",
            ])

        for layer_changes in sorted(
                data.changed_diagnostic_layers, key=lambda x: (x.diag_layer_type, x.diag_layer)):
            for service_change in sorted(
                    layer_changes.services_with_parameter_changes,
                    key=lambda ch: ch.service.short_name):
                for param_change in service_change.changed_parameters_of_service:
                    for attr in param_change.changed_attributes:
                        rows.append([
                            "changed_attribute",
                            layer_changes.diag_layer,
                            service_change.service.short_name,
                            attr.attribute,
                            str(attr.old_value) if attr.old_value is not None else "",
                            str(attr.new_value) if attr.new_value is not None else "",
                        ])
            for service in sorted(layer_changes.new_services, key=lambda s: s.short_name):
                rows.append([
                    "new_service",
                    layer_changes.diag_layer,
                    service.short_name,
                    "NEW_SERVICE",
                    "",
                    "",
                ])
            for service in sorted(layer_changes.deleted_services, key=lambda s: s.short_name):
                rows.append([
                    "deleted_service",
                    layer_changes.diag_layer,
                    service.short_name,
                    "DELETED_SERVICE",
                    "",
                    "",
                ])
            for renamed in sorted(
                    layer_changes.renamed_services, key=lambda item: item.new_service_name):
                rows.append([
                    "renamed_service",
                    layer_changes.diag_layer,
                    renamed.new_service_name,
                    "RENAMED_SERVICE",
                    renamed.old_service_name,
                    renamed.new_service_name,
                ])

        with destination.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        return destination


class ExporterFactory:

    @staticmethod
    def get(output_format: str) -> Exporter:
        format_lower = output_format.lower()
        if format_lower == "text":
            return TextExporter()
        if format_lower == "json":
            return JsonExporter()
        if format_lower == "yaml":
            return YamlExporter()
        if format_lower == "csv":
            return CsvExporter()
        raise ValueError(f"Unsupported output format: {output_format}")


class Comparison:
    """
    Orchestrates the complete comparison workflow for ODX databases and variants.

    This class serves as the main entry point for the comparison tool,
    coordinating all components of the comparison pipeline:

    Workflow:
    1. Load databases (load_file)
    2. Filter diagnostic layers (layer_filter)
    3. Run comparison via DiffEngine
    4. Format results via ReportFormatter
    5. Export reports via ExporterFactory

    Integration Points:
    - DiffEngine: Core comparison logic
    - ReportFormatter: Console output formatting
    - ExporterFactory: File export (JSON, YAML, CSV, Text)

    Attributes:
        detailed: Enable detailed parameter output in console
        output_format: Target export format (text, json, yaml, csv)
        output_file: Path for export file (None for console)
        fail_on_diff: Exit code 1 if differences are detected
        profile_enabled: Enable performance timing
        ignore_patterns: Regex patterns to filter attributes
    """

    def __init__(
        self,
        detailed: bool = False,
        output_format: str = "text",
        output_file: str | None = None,
        fail_on_diff: bool = False,
        profile_enabled: bool = False,
        ignore_patterns: Sequence[str] | None = None,
    ) -> None:
        self.detailed = detailed
        self.output_format = output_format
        self.output_file = output_file
        self.fail_on_diff = fail_on_diff
        self.profile_enabled = profile_enabled
        self.ignore_patterns = list(ignore_patterns or [])
        self.recursive = False
        self.databases: list[Database] = []
        self.diagnostic_layer_names: set[str] = set()
        self.engine = DiffEngine(
            ignore_patterns=self.ignore_patterns, profile_enabled=self.profile_enabled)
        self.formatter = ReportFormatter(detailed=self.detailed)

    def compare_database_files(self, database_new_path: Path,
                               database_old_path: Path) -> SpecsChangesVariants | None:
        """
        Compare two database files (.pdx or .odx).

        Args:
            database_new_path: Path to the newer database.
            database_old_path: Path to the older database.

        Returns:
            SpecsChangesVariants containing all detected changes, or None.
        """
        database_new = load_file(str(database_new_path))
        database_old = load_file(str(database_old_path))
        if not self.diagnostic_layer_names:
            self.diagnostic_layer_names = {
                dl.short_name
                for db in (database_new, database_old)
                for dl in db.diag_layers
            }
        result: SpecsChangesVariants | None = self.engine.compare_databases(
            database_new,
            database_old,
            layer_filter=self.diagnostic_layer_names,
        )
        return result

    def compare_folder(self, folder: Path) -> list[tuple[Path, Path, SpecsChangesVariants | None]]:
        """
        Compare all PDX files in a folder pairwise.

        Args:
            folder: Folder containing PDX files.

        Returns:
            List of tuples with (old_path, new_path, changes).
        """
        pattern = "**/*.pdx" if self.recursive else "*.pdx"
        pdx_files = sorted(folder.glob(pattern), key=lambda p: p.name)
        results: list[tuple[Path, Path, SpecsChangesVariants | None]] = []
        for previous, current in zip(pdx_files, pdx_files[1:], strict=False):
            results.append((previous, current, self.compare_database_files(current, previous)))
        return results

    def export_report(self, data: SpecsChangesVariants, target: str | None, fmt: str) -> Path:
        exporter = ExporterFactory.get(fmt)
        return exporter.export(data, Path(target) if target else None)

    def should_fail(self, data: SpecsChangesVariants | None) -> bool:
        if not self.fail_on_diff or data is None:
            return False
        return bool(data.new_diagnostic_layers or data.deleted_diagnostic_layers or
                    data.changed_diagnostic_layers)


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

    parser.add_argument(
        "--output-format",
        choices=["text", "json", "yaml", "csv"],
        default="text",
        help="Write comparison results to a structured export format.",
    )

    parser.add_argument(
        "--output-file",
        default=None,
        help="Path to write the comparison report when using --output-format.",
    )

    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Return a failing exit code when differences are detected.",
    )

    parser.add_argument(
        "--ignore",
        nargs="+",
        default=None,
        help="Ignore changes for matching attribute regex patterns.",
    )

    parser.add_argument(
        "--profile",
        action="store_true",
        default=False,
        help="Enable comparison profiling for performance investigation.",
    )

    # TODO: Folder comparison mode
    # - Load all PDX files in a folder and sort alphabetically
    # - Compare databases pairwise
    # - Calculate metrics per ECU variant:
    #   - Added services
    #   - Changed services
    #   - Removed services
    #   - Total services
    # - Optionally display metrics graphically
    # Future enhancement: folder comparison mode
    # TODO: implement compare_folder integration


def run(args: argparse.Namespace) -> None:
    # Ensure all optional arguments have defaults if not set (e.g., when called from tests)
    for attr, val in [
        ("output_format", "text"),
        ("output_file", None),
        ("fail_on_diff", False),
        ("profile", False),
        ("ignore", None),
        ("verbose", False),
        ("database", None),
        ("variants", None),
    ]:
        if not hasattr(args, attr):
            setattr(args, attr, val)

    pdx_file = args.pdx_file if isinstance(args.pdx_file, str) else args.pdx_file[0]

    try:
        task = Comparison(
            detailed=args.verbose,
            output_format=args.output_format,
            output_file=args.output_file,
            fail_on_diff=args.fail_on_diff,
            profile_enabled=args.profile,
            ignore_patterns=args.ignore,
        )
    except ValueError as exc:
        rich_print(str(exc))
        sys.exit(1)

    # comparison of specified databases
    if args.database:
        db_names = [str(pdx_file)] + [str(name) for name in args.database]

        task.databases = [load_file(name) for name in db_names]
        diag_layer_names = {dl.short_name for db in task.databases for dl in db.diag_layers}
        # filter diagnostic layers if specified
        if args.variants:
            task.diagnostic_layer_names = diag_layer_names.intersection(set(args.variants))
            for name in args.variants:
                if name not in task.diagnostic_layer_names:
                    rich_print(f"The variant [green3]'{name}'[/green3] could not be found!")
        else:
            task.diagnostic_layer_names = diag_layer_names

        for db_idx in range(len(task.databases) - 1):
            current_name = os.path.basename(db_names[0])
            previous_name = os.path.basename(db_names[db_idx + 1])

            rich_print()
            rich_print(f"Changes in file [orange1]'{current_name}'[/orange1]")
            rich_print(f" (compared to [orange1]'{previous_name}'[/orange1])")

            if args.verbose:
                diag_layers_1 = [
                    dl for dl in task.databases[0].diag_layers
                    if dl.short_name in task.diagnostic_layer_names
                ]
                diag_layers_2 = [
                    dl for dl in task.databases[db_idx + 1].diag_layers
                    if dl.short_name in task.diagnostic_layer_names
                ]
                task.formatter.print_dl_overview(filename=current_name, dls=diag_layers_1)
                task.formatter.print_dl_overview(filename=previous_name, dls=diag_layers_2)

            db_changes = task.engine.compare_databases(
                task.databases[0],
                task.databases[db_idx + 1],
                layer_filter=task.diagnostic_layer_names,
            )
            if db_changes:
                task.formatter.print_database_changes(db_changes)
            elif args.verbose:
                rich_print("No changes detected.")

            if args.output_format != "text" or args.output_file:
                report_data = db_changes or SpecsChangesVariants()
                destination = task.export_report(report_data, args.output_file, args.output_format)
                rich_print(f"Report written to [green3]{destination}[/green3]")

            if task.should_fail(db_changes):
                sys.stderr.write("Differences detected, exiting with code 1\n")
                sys.exit(1)
    # comparison of diagnostic layers (no databases specified)
    elif args.variants:
        odxdb = _parser_utils.load_file(args)
        task.databases = [odxdb]

        selected_layers: list[DiagLayer] = []
        selected_variants: set[str] = set()
        missing_variants: set[str] = set()
        for variant in args.variants:
            selected_variants.add(variant)
            variant_obj = odxdb.diag_layers.get(variant)
            if variant_obj is None:
                missing_variants.add(variant)
                continue
            selected_layers.append(variant_obj)

        if missing_variants:
            for name in missing_variants:
                rich_print(f"The variant [green3]'{name}'[/green3] could not be found! Skipping...")

        if len(selected_layers) < 2:
            rich_print("Please specify at least two existing variants to compare.")
            sys.exit(1)

        task.diagnostic_layer_names = {dl.short_name for dl in selected_layers}

        if args.verbose:
            task.formatter.print_dl_overview(
                filename=os.path.basename(pdx_file),
                dls=selected_layers,
            )

        for db_idx in range(len(selected_layers) - 1):
            dl = selected_layers[db_idx]
            next_layer = selected_layers[db_idx + 1]

            rich_print()
            rich_print(
                f"Changes in diagnostic layer [green3]'{dl.short_name}'[/green3] [medium_spring_green]({dl.variant_type.value})[/medium_spring_green]"
            )
            rich_print(
                f" (compared to '[green3]{next_layer.short_name}'[/green3] [medium_spring_green]({next_layer.variant_type.value})[/medium_spring_green])"
            )

            dl_changes = task.engine.compare_diagnostic_layers(dl, next_layer)
            if dl_changes:
                task.formatter.print_dl_changes(dl_changes)
            elif args.verbose:
                rich_print("No changes detected.")

            report_data = SpecsChangesVariants(
                changed_diagnostic_layers=[dl_changes]) if dl_changes else SpecsChangesVariants()
            if args.output_format != "text" or args.output_file:
                destination = task.export_report(report_data, args.output_file, args.output_format)
                rich_print(f"Report written to [green3]{destination}[/green3]")

            if task.should_fail(report_data):
                sys.stderr.write("Differences detected, exiting with code 1\n")
                sys.exit(1)
    else:
        # no databases & no variants specified
        rich_print("Please specify either a database or variant for a comparison")
