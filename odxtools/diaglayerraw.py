# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, cast
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .admindata import AdminData
from .companydata import CompanyData
from .comparaminstance import ComparamInstance
from .comparamspec import ComparamSpec
from .comparamsubset import ComparamSubset
from .diagcomm import DiagComm
from .diagdatadictionaryspec import DiagDataDictionarySpec
from .diaglayertype import DiagLayerType
from .diagservice import DiagService
from .diagvariable import DiagVariable
from .dyndefinedspec import DynDefinedSpec
from .ecuvariantpattern import EcuVariantPattern
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .parentref import ParentRef
from .protstack import ProtStack
from .request import Request
from .response import Response
from .singleecujob import SingleEcuJob
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .statechart import StateChart
from .utils import dataclass_fields_asdict
from .variablegroup import VariableGroup


@dataclass
class DiagLayerRaw(IdentifiableElement):
    """This class internalizes all data represented by the DIAG-LAYER
    XML tag and its derivatives.

    It does *not* deal with value inheritance.
    """

    variant_type: DiagLayerType
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    functional_classes: NamedItemList[FunctionalClass]
    diag_data_dictionary_spec: Optional[DiagDataDictionarySpec]
    diag_comms_raw: List[Union[OdxLinkRef, DiagComm]]
    requests: NamedItemList[Request]
    positive_responses: NamedItemList[Response]
    negative_responses: NamedItemList[Response]
    global_negative_responses: NamedItemList[Response]
    import_refs: List[OdxLinkRef]
    state_charts: NamedItemList[StateChart]
    additional_audiences: NamedItemList[AdditionalAudience]
    # sub_components: List[DiagLayer] # TODO
    # libraries: List[DiagLayer] # TODO
    sdgs: List[SpecialDataGroup]

    # these attributes are only defined for some kinds of diag layers!
    # TODO: make a proper class hierarchy!
    parent_refs: List[ParentRef]
    comparam_refs: List[ComparamInstance]
    ecu_variant_patterns: List[EcuVariantPattern]
    comparam_spec_ref: Optional[OdxLinkRef]
    prot_stack_snref: Optional[str]
    diag_variables_raw: List[Union[DiagVariable, OdxLinkRef]]
    variable_groups: NamedItemList[VariableGroup]
    dyn_defined_spec: Optional[DynDefinedSpec]
    # base_variant_patterns: List[EcuVariantPattern] # TODO

    @property
    def diag_comms(self) -> NamedItemList[DiagComm]:
        return self._diag_comms

    @property
    def diag_services(self) -> NamedItemList[DiagService]:
        return self._diag_services

    @property
    def services(self) -> NamedItemList[DiagService]:
        """This property is an alias for `.diag_services`"""
        return self._diag_services

    @property
    def single_ecu_jobs(self) -> NamedItemList[SingleEcuJob]:
        return self._single_ecu_jobs

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self._diag_variables

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagLayerRaw":
        try:
            variant_type = DiagLayerType(et_element.tag)
        except ValueError:
            variant_type = cast(DiagLayerType, None)
            odxraise(f"Encountered unknown diagnostic layer type '{et_element.tag}'")

        short_name = odxrequire(et_element.findtext("SHORT-NAME"))

        # extend the applicable ODX "document fragments" for the diag layer objects
        doc_frags = copy(doc_frags)
        doc_frags.append(OdxDocFragment(short_name, "LAYER"))
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = None
        if (admin_data_elem := et_element.find("ADMIN-DATA")) is not None:
            admin_data = AdminData.from_et(admin_data_elem, doc_frags)

        company_datas = [
            CompanyData.from_et(cd_el, doc_frags)
            for cd_el in et_element.iterfind("COMPANY-DATAS/COMPANY-DATA")
        ]

        functional_classes = [
            FunctionalClass.from_et(fc_el, doc_frags)
            for fc_el in et_element.iterfind("FUNCT-CLASSS/FUNCT-CLASS")
        ]

        diag_data_dictionary_spec = None
        if (ddds_elem := et_element.find("DIAG-DATA-DICTIONARY-SPEC")) is not None:
            diag_data_dictionary_spec = DiagDataDictionarySpec.from_et(ddds_elem, doc_frags)

        diag_comms_raw: List[Union[OdxLinkRef, DiagComm]] = []
        if (dc_elems := et_element.find("DIAG-COMMS")) is not None:
            for dc_proxy_elem in dc_elems:
                dc: Union[OdxLinkRef, DiagComm]
                if dc_proxy_elem.tag == "DIAG-COMM-REF":
                    dc = OdxLinkRef.from_et(dc_proxy_elem, doc_frags)
                elif dc_proxy_elem.tag == "DIAG-SERVICE":
                    dc = DiagService.from_et(dc_proxy_elem, doc_frags)
                else:
                    odxassert(dc_proxy_elem.tag == "SINGLE-ECU-JOB")
                    dc = SingleEcuJob.from_et(dc_proxy_elem, doc_frags)

                diag_comms_raw.append(dc)

        requests = NamedItemList([
            Request.from_et(rq_elem, doc_frags)
            for rq_elem in et_element.iterfind("REQUESTS/REQUEST")
        ])

        positive_responses = NamedItemList([
            Response.from_et(rs_elem, doc_frags)
            for rs_elem in et_element.iterfind("POS-RESPONSES/POS-RESPONSE")
        ])

        negative_responses = NamedItemList([
            Response.from_et(rs_elem, doc_frags)
            for rs_elem in et_element.iterfind("NEG-RESPONSES/NEG-RESPONSE")
        ])

        global_negative_responses = NamedItemList([
            Response.from_et(rs_elem, doc_frags)
            for rs_elem in et_element.iterfind("GLOBAL-NEG-RESPONSES/GLOBAL-NEG-RESPONSE")
        ])

        import_refs = [
            OdxLinkRef.from_et(el, doc_frags)
            for el in et_element.iterfind("IMPORT-REFS/IMPORT-REF")
        ]

        state_charts = [
            StateChart.from_et(el, doc_frags)
            for el in et_element.iterfind("STATE-CHARTS/STATE-CHART")
        ]

        additional_audiences = [
            AdditionalAudience.from_et(el, doc_frags)
            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")
        ]

        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        parent_refs = [
            ParentRef.from_et(pr_el, doc_frags)
            for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")
        ]

        comparam_refs = [
            ComparamInstance.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")
        ]

        ecu_variant_patterns = [
            EcuVariantPattern.from_et(el, doc_frags)
            for el in et_element.iterfind("ECU-VARIANT-PATTERNS/ECU-VARIANT-PATTERN")
        ]
        if variant_type is not DiagLayerType.ECU_VARIANT:
            odxassert(
                len(ecu_variant_patterns) == 0,
                "DiagLayer of type other than 'ECU-VARIANT' must not define a ECU-VARIANT-PATTERN")

        comparam_spec_ref = OdxLinkRef.from_et(et_element.find("COMPARAM-SPEC-REF"), doc_frags)
        prot_stack_snref: Optional[str] = None
        if (prot_stack_snref_elem := et_element.find("PROT-STACK-SNREF")) is not None:
            prot_stack_snref = odxrequire(prot_stack_snref_elem.get("SHORT-NAME"))

        diag_variables_raw: List[Union[DiagVariable, OdxLinkRef]] = []
        if (dv_elems := et_element.find("DIAG-VARIABLES")) is not None:
            for dv_proxy_elem in dv_elems:
                dv_proxy: Union[OdxLinkRef, DiagVariable]
                if dv_proxy_elem.tag == "DIAG-VARIABLE-REF":
                    dv_proxy = OdxLinkRef.from_et(dv_proxy_elem, doc_frags)
                elif dv_proxy_elem.tag == "DIAG-VARIABLE":
                    dv_proxy = DiagVariable.from_et(dv_proxy_elem, doc_frags)
                else:
                    odxraise("DIAG-VARIABLES tags may only contain "
                             "DIAG-VARIABLE and DIAG-VARIABLE-REF subtags")

                diag_variables_raw.append(dv_proxy)

        variable_groups = NamedItemList([
            VariableGroup.from_et(vg_elem, doc_frags)
            for vg_elem in et_element.iterfind("VARIABLE-GROUPS/VARIABLE-GROUP")
        ])

        dyn_defined_spec = None
        if (dds_elem := et_element.find("DYN-DEFINED-SPEC")) is not None:
            dyn_defined_spec = DynDefinedSpec.from_et(dds_elem, doc_frags)

        # Create DiagLayer
        return DiagLayerRaw(
            variant_type=variant_type,
            admin_data=admin_data,
            company_datas=NamedItemList(company_datas),
            functional_classes=NamedItemList(functional_classes),
            diag_data_dictionary_spec=diag_data_dictionary_spec,
            diag_comms_raw=diag_comms_raw,
            requests=requests,
            positive_responses=positive_responses,
            negative_responses=negative_responses,
            global_negative_responses=NamedItemList(global_negative_responses),
            import_refs=import_refs,
            state_charts=NamedItemList(state_charts),
            additional_audiences=NamedItemList(additional_audiences),
            sdgs=sdgs,
            parent_refs=parent_refs,
            comparam_refs=comparam_refs,
            ecu_variant_patterns=ecu_variant_patterns,
            comparam_spec_ref=comparam_spec_ref,
            prot_stack_snref=prot_stack_snref,
            diag_variables_raw=diag_variables_raw,
            variable_groups=variable_groups,
            dyn_defined_spec=dyn_defined_spec,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        odxlinks = {self.odx_id: self}

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())
        if self.diag_data_dictionary_spec is not None:
            odxlinks.update(self.diag_data_dictionary_spec._build_odxlinks())

        for company_data in self.company_datas:
            odxlinks.update(company_data._build_odxlinks())
        for functional_class in self.functional_classes:
            odxlinks.update(functional_class._build_odxlinks())
        for dc_proxy in self.diag_comms_raw:
            if isinstance(dc_proxy, OdxLinkRef):
                continue
            odxlinks.update(dc_proxy._build_odxlinks())
        for request in self.requests:
            odxlinks.update(request._build_odxlinks())
        for positive_response in self.positive_responses:
            odxlinks.update(positive_response._build_odxlinks())
        for negative_response in self.negative_responses:
            odxlinks.update(negative_response._build_odxlinks())
        for global_negative_response in self.global_negative_responses:
            odxlinks.update(global_negative_response._build_odxlinks())
        for state_chart in self.state_charts:
            odxlinks.update(state_chart._build_odxlinks())
        for additional_audience in self.additional_audiences:
            odxlinks.update(additional_audience._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())
        for parent_ref in self.parent_refs:
            odxlinks.update(parent_ref._build_odxlinks())
        for comparam in self.comparam_refs:
            odxlinks.update(comparam._build_odxlinks())
        for dv_proxy in self.diag_variables_raw:
            if not isinstance(dv_proxy, OdxLinkRef):
                odxlinks.update(dv_proxy._build_odxlinks())
        if self.dyn_defined_spec is not None:
            odxlinks.update(self.dyn_defined_spec._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all references."""

        if self.comparam_spec_ref is not None:
            spec = odxlinks.resolve(self.comparam_spec_ref)
            if not isinstance(spec, (ComparamSubset, ComparamSpec)):
                odxraise(f"Type {type(spec).__name__} is not allowed for comparam specs")
            self._comparam_spec = spec

        # do ODXLINK reference resolution
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)
        if self.diag_data_dictionary_spec is not None:
            self.diag_data_dictionary_spec._resolve_odxlinks(odxlinks)

        for company_data in self.company_datas:
            company_data._resolve_odxlinks(odxlinks)
        for functional_class in self.functional_classes:
            functional_class._resolve_odxlinks(odxlinks)

        # resolve references to diagnostic communication objects and
        # separate them into services and single-ecu jobs
        self._diag_comms = NamedItemList[DiagComm]()
        self._diag_services = NamedItemList[DiagService]()
        self._single_ecu_jobs = NamedItemList[SingleEcuJob]()
        for dc_proxy in self.diag_comms_raw:
            if isinstance(dc_proxy, OdxLinkRef):
                dc = odxlinks.resolve(dc_proxy, DiagComm)
            else:
                dc = dc_proxy
                dc._resolve_odxlinks(odxlinks)

            self._diag_comms.append(dc)

            if isinstance(dc, DiagService):
                self._diag_services.append(dc)
            elif isinstance(dc, SingleEcuJob):
                self._single_ecu_jobs.append(dc)
            else:
                odxraise()

        for request in self.requests:
            request._resolve_odxlinks(odxlinks)
        for positive_response in self.positive_responses:
            positive_response._resolve_odxlinks(odxlinks)
        for negative_response in self.negative_responses:
            negative_response._resolve_odxlinks(odxlinks)
        for global_negative_response in self.global_negative_responses:
            global_negative_response._resolve_odxlinks(odxlinks)
        for state_chart in self.state_charts:
            state_chart._resolve_odxlinks(odxlinks)
        for additional_audience in self.additional_audiences:
            additional_audience._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)
        for parent_ref in self.parent_refs:
            parent_ref._resolve_odxlinks(odxlinks)
        for comparam in self.comparam_refs:
            comparam._resolve_odxlinks(odxlinks)

        self._diag_variables: NamedItemList[DiagVariable] = NamedItemList()
        for dv_proxy in self.diag_variables_raw:
            if isinstance(dv_proxy, OdxLinkRef):
                dv = odxlinks.resolve(dv_proxy, DiagVariable)
            else:
                dv_proxy._resolve_odxlinks(odxlinks)
                dv = dv_proxy

            self._diag_variables.append(dv)

        if self.dyn_defined_spec is not None:
            self.dyn_defined_spec._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._prot_stack: Optional[ProtStack] = None
        if self.prot_stack_snref is not None:
            cp_spec = self.comparam_spec
            if isinstance(cp_spec, ComparamSpec):
                self._prot_stack = resolve_snref(self.prot_stack_snref, cp_spec.prot_stacks,
                                                 ProtStack)

        # do short-name reference resolution
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)
        if self.diag_data_dictionary_spec is not None:
            self.diag_data_dictionary_spec._resolve_snrefs(context)

        for company_data in self.company_datas:
            company_data._resolve_snrefs(context)
        for functional_class in self.functional_classes:
            functional_class._resolve_snrefs(context)
        for dc_proxy in self.diag_comms_raw:
            if isinstance(dc_proxy, OdxLinkRef):
                continue
            dc_proxy._resolve_snrefs(context)
        for request in self.requests:
            request._resolve_snrefs(context)
        for positive_response in self.positive_responses:
            positive_response._resolve_snrefs(context)
        for negative_response in self.negative_responses:
            negative_response._resolve_snrefs(context)
        for global_negative_response in self.global_negative_responses:
            global_negative_response._resolve_snrefs(context)
        for state_chart in self.state_charts:
            state_chart._resolve_snrefs(context)
        for additional_audience in self.additional_audiences:
            additional_audience._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
        for parent_ref in self.parent_refs:
            parent_ref._resolve_snrefs(context)
        for comparam in self.comparam_refs:
            comparam._resolve_snrefs(context)

        for dv_proxy in self.diag_variables_raw:
            if not isinstance(dv_proxy, OdxLinkRef):
                dv_proxy._resolve_snrefs(context)

        if self.dyn_defined_spec is not None:
            self.dyn_defined_spec._resolve_snrefs(context)

    @property
    def comparam_spec(self) -> Optional[Union[ComparamSpec, ComparamSubset]]:
        return self._comparam_spec

    @property
    def prot_stack(self) -> Optional[ProtStack]:
        return self._prot_stack
