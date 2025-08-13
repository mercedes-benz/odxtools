# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .componentconnector import ComponentConnector
from .element import IdentifiableElement
from .functioninparam import FunctionInParam
from .functionoutparam import FunctionOutParam
from .multipleecujob import MultipleEcuJob
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class BaseFunctionNode(IdentifiableElement):
    audience: Audience | None = None
    function_in_params: NamedItemList[FunctionInParam] = field(default_factory=NamedItemList)
    function_out_params: NamedItemList[FunctionOutParam] = field(default_factory=NamedItemList)
    component_connectors: list[ComponentConnector] = field(default_factory=list)
    multiple_ecu_job_refs: list[OdxLinkRef] = field(default_factory=list)
    admin_data: AdminData | None = None
    sdg: SpecialDataGroup | None = None

    @property
    def multiple_ecu_jobs(self) -> NamedItemList[MultipleEcuJob]:
        return self._multiple_ecu_jobs

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "BaseFunctionNode":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, context)

        function_in_params = NamedItemList([
            FunctionInParam.from_et(fip_el, context)
            for fip_el in et_element.iterfind("FUNCTION-IN-PARAMS/FUNCTION-IN-PARAM")
        ])

        function_out_params = NamedItemList([
            FunctionOutParam.from_et(fop_el, context)
            for fop_el in et_element.iterfind("FUNCTION-OUT-PARAMS/FUNCTION-OUT-PARAM")
        ])

        component_connectors = [
            ComponentConnector.from_et(cc_el, context)
            for cc_el in et_element.iterfind("COMPONENT-CONNECTORS/COMPONENT-CONNECTOR")
        ]

        multiple_ecu_job_refs = [
            OdxLinkRef.from_et(el, context)
            for el in et_element.iterfind("MULTIPLE-ECU-JOB-REFS/MULTIPLE-ECU-JOB-REF")
        ]

        admin_data = None
        if (admin_data_elem := et_element.find("ADMIN-DATA")) is not None:
            admin_data = AdminData.from_et(admin_data_elem, context)

        # be a aware that for whatever reason, function nodes only
        # exhibit at most one SDG. (quirk of the ODX standard?)
        sdg = None
        if (sdge := et_element.find("SDG")) is not None:
            sdg = SpecialDataGroup.from_et(sdge, context)

        return BaseFunctionNode(
            audience=audience,
            function_in_params=function_in_params,
            function_out_params=function_out_params,
            component_connectors=component_connectors,
            multiple_ecu_job_refs=multiple_ecu_job_refs,
            admin_data=admin_data,
            sdg=sdg,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.audience is not None:
            result.update(self.audience._build_odxlinks())

        for function_in_param in self.function_in_params:
            result.update(function_in_param._build_odxlinks())

        for function_out_param in self.function_out_params:
            result.update(function_out_param._build_odxlinks())

        for component_connector in self.component_connectors:
            result.update(component_connector._build_odxlinks())

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        if self.sdg is not None:
            result.update(self.sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._multiple_ecu_jobs = NamedItemList(
            [odxlinks.resolve(ref, MultipleEcuJob) for ref in self.multiple_ecu_job_refs])

        if self.audience:
            self.audience._resolve_odxlinks(odxlinks)

        for function_in_param in self.function_in_params:
            function_in_param._resolve_odxlinks(odxlinks)

        for function_out_param in self.function_out_params:
            function_out_param._resolve_odxlinks(odxlinks)

        for component_connector in self.component_connectors:
            component_connector._resolve_odxlinks(odxlinks)

        if self.admin_data:
            self.admin_data._resolve_odxlinks(odxlinks)

        if self.sdg is not None:
            self.sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.audience:
            self.audience._resolve_snrefs(context)

        for function_in_param in self.function_in_params:
            function_in_param._resolve_snrefs(context)

        for function_out_param in self.function_out_params:
            function_out_param._resolve_snrefs(context)

        for component_connector in self.component_connectors:
            component_connector._resolve_snrefs(context)

        if self.admin_data:
            self.admin_data._resolve_snrefs(context)

        if self.sdg is not None:
            self.sdg._resolve_snrefs(context)
