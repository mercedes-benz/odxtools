# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .exceptions import odxrequire
from .functiondiagcommconnector import FunctionDiagCommConnector
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .physicaltype import PhysicalType
from .snrefcontext import SnRefContext
from .unit import Unit
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class FunctionOutParam(NamedElement):
    unit_ref: OdxLinkRef | None = None
    physical_type: PhysicalType
    out_param_if_snref: str | None = None
    function_diag_comm_connector: FunctionDiagCommConnector | None = None

    @property
    def unit(self) -> Unit | None:
        return self._unit

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "FunctionOutParam":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        unit_ref = OdxLinkRef.from_et(et_element.find("UNIT-REF"), context)
        physical_type = PhysicalType.from_et(odxrequire(et_element.find("PHYSICAL-TYPE")), context)

        out_param_if_snref = None
        if (ipi_snref_elem := et_element.find("OUT-PARAM-IF-SNREF")) is not None:
            out_param_if_snref = odxrequire(ipi_snref_elem.attrib.get("SHORT-NAME"))

        function_diag_comm_connector = None
        if (fpcc_elem := et_element.find("FUNCTION-DIAG-COMM-CONNECTOR")) is not None:
            function_diag_comm_connector = FunctionDiagCommConnector.from_et(fpcc_elem, context)

        return FunctionOutParam(
            unit_ref=unit_ref,
            physical_type=physical_type,
            out_param_if_snref=out_param_if_snref,
            function_diag_comm_connector=function_diag_comm_connector,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        if self.function_diag_comm_connector is not None:
            result.update(self.function_diag_comm_connector._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._unit = None
        if self.unit_ref is not None:
            self._unit = odxlinks.resolve(self.unit_ref, Unit)

        if self.function_diag_comm_connector is not None:
            self.function_diag_comm_connector._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.function_diag_comm_connector is not None:
            self.function_diag_comm_connector._resolve_snrefs(context)
