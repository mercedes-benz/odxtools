# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, cast
from xml.etree import ElementTree

from ..additionalaudience import AdditionalAudience
from ..admindata import AdminData
from ..companydata import CompanyData
from ..diagcomm import DiagComm
from ..diagdatadictionaryspec import DiagDataDictionarySpec
from ..diagservice import DiagService
from ..element import IdentifiableElement
from ..exceptions import odxassert, odxraise, odxrequire
from ..functionalclass import FunctionalClass
from ..library import Library
from ..nameditemlist import NamedItemList
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..request import Request
from ..response import Response
from ..singleecujob import SingleEcuJob
from ..snrefcontext import SnRefContext
from ..specialdatagroup import SpecialDataGroup
from ..statechart import StateChart
from ..subcomponent import SubComponent
from ..utils import dataclass_fields_asdict
from .diaglayertype import DiagLayerType


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
    sub_components: NamedItemList[SubComponent]
    libraries: NamedItemList[Library]
    sdgs: List[SpecialDataGroup]

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

        libraries = [
            Library.from_et(el, doc_frags) for el in et_element.iterfind("LIBRARYS/LIBRARY")
        ]

        sub_components = [
            SubComponent.from_et(el, doc_frags)
            for el in et_element.iterfind("SUB-COMPONENTS/SUB-COMPONENT")
        ]

        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

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
            libraries=NamedItemList(libraries),
            sub_components=NamedItemList(sub_components),
            sdgs=sdgs,
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
        for library in self.libraries:
            odxlinks.update(library._build_odxlinks())
        for sub_comp in self.sub_components:
            odxlinks.update(sub_comp._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all references."""

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
        for library in self.libraries:
            library._resolve_odxlinks(odxlinks)
        for sub_component in self.sub_components:
            sub_component._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
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
        for library in self.libraries:
            library._resolve_snrefs(context)
        for sub_component in self.sub_components:
            sub_component._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
