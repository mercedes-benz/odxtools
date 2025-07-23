# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .diaglayers.diaglayer import DiagLayer
from .element import IdentifiableElement
from .exceptions import odxrequire
from .functionalclass import FunctionalClass
from .inputparam import InputParam
from .nameditemlist import NamedItemList
from .negoutputparam import NegOutputParam
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .outputparam import OutputParam
from .progcode import ProgCode
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class MultipleEcuJob(IdentifiableElement):
    """A multiple ECU job is a diagnostic communication primitive.

    A multiple ECU job is more complex than a diagnostic service and is
    not provided natively by the ECU.  In particular, the job is
    defined in external programs which are referenced by the attribute
    `.prog_codes`.

    In contrast to "single ECU jobs", a multiple ECU job only involves
    calls to services provided by more than one ECU.

    Multiple ECU jobs are defined in section 7.3.11 of the ASAM MCD-2
    standard.
    """

    admin_data: AdminData | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    functional_class_refs: list[OdxLinkRef] = field(default_factory=list)
    prog_codes: list[ProgCode] = field(default_factory=list)
    input_params: NamedItemList[InputParam] = field(default_factory=NamedItemList)
    output_params: NamedItemList[OutputParam] = field(default_factory=NamedItemList)
    neg_output_params: NamedItemList[NegOutputParam] = field(default_factory=NamedItemList)
    diag_layer_refs: list[OdxLinkRef] = field(default_factory=list)
    audience: Audience | None = None
    semantic: str | None = None
    is_executable_raw: bool | None = None

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def diag_layers(self) -> NamedItemList[DiagLayer]:
        return self._diag_layers

    @property
    def is_executable(self) -> bool:
        return self.is_executable_raw in (True, None)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MultipleEcuJob":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = None
        if (admin_data_elem := et_element.find("ADMIN-DATA")) is not None:
            admin_data = AdminData.from_et(admin_data_elem, context)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        functional_class_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
        ]
        prog_codes = [
            ProgCode.from_et(pc_elem, context)
            for pc_elem in et_element.iterfind("PROG-CODES/PROG-CODE")
        ]

        input_params = NamedItemList([
            InputParam.from_et(el, context)
            for el in et_element.iterfind("INPUT-PARAMS/INPUT-PARAM")
        ])
        output_params = NamedItemList([
            OutputParam.from_et(el, context)
            for el in et_element.iterfind("OUTPUT-PARAMS/OUTPUT-PARAM")
        ])
        neg_output_params = NamedItemList([
            NegOutputParam.from_et(el, context)
            for el in et_element.iterfind("NEG-OUTPUT-PARAMS/NEG-OUTPUT-PARAM")
        ])
        diag_layer_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("DIAG-LAYER-REFS/DIAG-LAYER-REF")
        ]
        audience = None
        if (aud_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(aud_elem, context)

        semantic = et_element.attrib.get("SEMANTIC")
        is_executable_raw = odxstr_to_bool(et_element.attrib.get("IS-EXECUTABLE"))

        return MultipleEcuJob(
            admin_data=admin_data,
            sdgs=sdgs,
            functional_class_refs=functional_class_refs,
            prog_codes=prog_codes,
            input_params=input_params,
            output_params=output_params,
            neg_output_params=neg_output_params,
            diag_layer_refs=diag_layer_refs,
            audience=audience,
            semantic=semantic,
            is_executable_raw=is_executable_raw,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())
        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())
        for prog_code in self.prog_codes:
            result.update(prog_code._build_odxlinks())
        for input_param in self.input_params:
            result.update(input_param._build_odxlinks())
        for output_param in self.output_params:
            result.update(output_param._build_odxlinks())
        for neg_output_param in self.neg_output_params:
            result.update(neg_output_param._build_odxlinks())
        if self.audience is not None:
            result.update(self.audience._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)
        for prog_code in self.prog_codes:
            prog_code._resolve_odxlinks(odxlinks)
        for input_param in self.input_params:
            input_param._resolve_odxlinks(odxlinks)
        for output_param in self.output_params:
            output_param._resolve_odxlinks(odxlinks)
        for neg_output_param in self.neg_output_params:
            neg_output_param._resolve_odxlinks(odxlinks)
        if self.audience is not None:
            self.audience._resolve_odxlinks(odxlinks)

        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])
        self._diag_layers = NamedItemList(
            [odxlinks.resolve(dl_ref, DiagLayer) for dl_ref in self.diag_layer_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.multiple_ecu_job = self

        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
        for prog_code in self.prog_codes:
            prog_code._resolve_snrefs(context)
        for input_param in self.input_params:
            input_param._resolve_snrefs(context)
        for output_param in self.output_params:
            output_param._resolve_snrefs(context)
        for neg_output_param in self.neg_output_params:
            neg_output_param._resolve_snrefs(context)
        if self.audience is not None:
            self.audience._resolve_snrefs(context)

        context.multiple_ecu_job = None
