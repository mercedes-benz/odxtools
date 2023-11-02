# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .admindata import AdminData
from .companydata import CompanyData
from .comparaminstance import ComparamInstance
from .createanystructure import create_any_structure_from_et
from .createsdgs import create_sdgs_from_et
from .diagcomm import DiagComm
from .diagdatadictionaryspec import DiagDataDictionarySpec
from .diaglayertype import DiagLayerType
from .diagservice import DiagService
from .ecuvariantpattern import EcuVariantPattern
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .parentref import ParentRef
from .request import Request
from .response import Response
from .singleecujob import SingleEcuJob
from .specialdatagroup import SpecialDataGroup
from .statechart import StateChart
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


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
    diag_comms: List[Union[OdxLinkRef, DiagComm]]
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
    comparams: List[ComparamInstance]
    ecu_variant_patterns: List[EcuVariantPattern]
    # comparam_spec: OdxLinkRef # TODO
    # prot_stack_snref: str # TODO
    # diag_variables: List[DiagVariable] # TODO
    # diag_variable_groups: List[DiagVariableGroup] # TODO
    # dyn_defined_spec: Optional[DynDefinedSpec] # TODO
    # base_variant_patterns: List[EcuVariantPattern] # TODO

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagLayerRaw":

        variant_type = DiagLayerType(et_element.tag)

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

        diag_comms: List[Union[OdxLinkRef, DiagComm]] = []
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

                diag_comms.append(dc)

        requests = []
        for rq_elem in et_element.iterfind("REQUESTS/REQUEST"):
            rq = odxrequire(create_any_structure_from_et(rq_elem, doc_frags))
            if not isinstance(rq, Request):
                odxraise()
            requests.append(rq)

        positive_responses = []
        for pr_elem in et_element.iterfind("POS-RESPONSES/POS-RESPONSE"):
            pr = odxrequire(create_any_structure_from_et(pr_elem, doc_frags))
            if not isinstance(pr, Response):
                odxraise()
            positive_responses.append(pr)

        negative_responses = []
        for nr_elem in et_element.iterfind("NEG-RESPONSES/NEG-RESPONSE"):
            nr = odxrequire(create_any_structure_from_et(nr_elem, doc_frags))
            if not isinstance(nr, Response):
                odxraise()
            negative_responses.append(nr)

        global_negative_responses = []
        for nr_elem in et_element.iterfind("GLOBAL-NEG-RESPONSES/GLOBAL-NEG-RESPONSE"):
            nr = odxrequire(create_any_structure_from_et(nr_elem, doc_frags))
            if not isinstance(nr, Response):
                odxraise()
            global_negative_responses.append(nr)

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

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        parent_refs = [
            ParentRef.from_et(pr_el, doc_frags)
            for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")
        ]

        comparams = [
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

        # Create DiagLayer
        return DiagLayerRaw(
            variant_type=variant_type,
            admin_data=admin_data,
            company_datas=NamedItemList(company_datas),
            functional_classes=NamedItemList(functional_classes),
            diag_data_dictionary_spec=diag_data_dictionary_spec,
            diag_comms=diag_comms,
            requests=NamedItemList(requests),
            positive_responses=NamedItemList(positive_responses),
            negative_responses=NamedItemList(negative_responses),
            global_negative_responses=NamedItemList(global_negative_responses),
            import_refs=import_refs,
            state_charts=NamedItemList(state_charts),
            additional_audiences=NamedItemList(additional_audiences),
            sdgs=sdgs,
            parent_refs=parent_refs,
            comparams=comparams,
            ecu_variant_patterns=ecu_variant_patterns,
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
        for diag_comm in self.diag_comms:
            if isinstance(diag_comm, OdxLinkRef):
                continue
            odxlinks.update(diag_comm._build_odxlinks())
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
        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())

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
        for diag_comm in self.diag_comms:
            if isinstance(diag_comm, OdxLinkRef):
                continue
            diag_comm._resolve_odxlinks(odxlinks)
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
        for comparam in self.comparams:
            comparam._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        # do short-name reference resolution
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(diag_layer)
        if self.diag_data_dictionary_spec is not None:
            self.diag_data_dictionary_spec._resolve_snrefs(diag_layer)

        for company_data in self.company_datas:
            company_data._resolve_snrefs(diag_layer)
        for functional_classe in self.functional_classes:
            functional_classe._resolve_snrefs(diag_layer)
        for diag_comm in self.diag_comms:
            if isinstance(diag_comm, OdxLinkRef):
                continue
            diag_comm._resolve_snrefs(diag_layer)
        for request in self.requests:
            request._resolve_snrefs(diag_layer)
        for positive_response in self.positive_responses:
            positive_response._resolve_snrefs(diag_layer)
        for negative_response in self.negative_responses:
            negative_response._resolve_snrefs(diag_layer)
        for global_negative_response in self.global_negative_responses:
            global_negative_response._resolve_snrefs(diag_layer)
        for state_chart in self.state_charts:
            state_chart._resolve_snrefs(diag_layer)
        for additional_audience in self.additional_audiences:
            additional_audience._resolve_snrefs(diag_layer)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(diag_layer)
        for parent_ref in self.parent_refs:
            parent_ref._resolve_snrefs(diag_layer)
        for comparam in self.comparams:
            comparam._resolve_snrefs(diag_layer)
