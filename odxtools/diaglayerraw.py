# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import AdditionalAudience, Audience
from .communicationparameter import CommunicationParameterRef
from .companydata import CompanyData, create_company_datas_from_et
from .dataobjectproperty import DopBase
from .diagdatadictionaryspec import DiagDataDictionarySpec
from .diaglayertype import DiagLayerType
from .ecu_variant_patterns import EcuVariantPattern
from .functionalclass import FunctionalClass
from .globals import xsi
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .parentref import ParentRef
from .service import DiagService
from .singleecujob import SingleEcuJob
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .statechart import StateChart
from .structures import Request, Response, create_any_structure_from_et
from .table import Table
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DiagLayerRaw:
    """This class internalizes all data represented by the DIAG-LAYER
    XML tag and its derivatives.

    It does *not* deal with value inheritance.
    """

    variant_type: DiagLayerType
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    functional_classes: NamedItemList[FunctionalClass]
    diag_data_dictionary_spec: Optional[DiagDataDictionarySpec]
    diag_comms: List[Union[OdxLinkRef, DiagService, SingleEcuJob]]
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
    communication_parameters: List[CommunicationParameterRef]
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

        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        # extend the applicable ODX "document fragments" for the diag layer objects
        doc_frags = copy(doc_frags)
        doc_frags.append(OdxDocFragment(short_name, "LAYER"))

        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

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
        if et_element.find("DIAG-DATA-DICTIONARY-SPEC"):
            diag_data_dictionary_spec = DiagDataDictionarySpec.from_et(
                et_element.find("DIAG-DATA-DICTIONARY-SPEC"), doc_frags)

        diag_comms: List[Union[OdxLinkRef, DiagService, SingleEcuJob]] = []
        if (dc_elems := et_element.find("DIAG-COMMS")) is not None:
            for dc_proxy_elem in dc_elems:
                dc: Union[OdxLinkRef, DiagService, SingleEcuJob]
                if dc_proxy_elem.tag == "DIAG-COMM-REF":
                    dc = OdxLinkRef.from_et(dc_proxy_elem, doc_frags)
                elif dc_proxy_elem.tag == "DIAG-SERVICE":
                    dc = DiagService.from_et(dc_proxy_elem, doc_frags)
                else:
                    assert dc_proxy_elem.tag == "SINGLE-ECU-JOB"
                    dc = SingleEcuJob.from_et(dc_proxy_elem, doc_frags)

                diag_comms.append(dc)

        requests = []
        for rq_elem in et_element.iterfind("REQUESTS/REQUEST"):
            rq = create_any_structure_from_et(rq_elem, doc_frags)
            assert isinstance(rq, Request)
            requests.append(rq)

        positive_responses = []
        for pr_elem in et_element.iterfind("POS-RESPONSES/POS-RESPONSE"):
            pr = create_any_structure_from_et(pr_elem, doc_frags)
            assert isinstance(pr, Response)
            positive_responses.append(pr)

        negative_responses = []
        for nr_elem in et_element.iterfind("NEG-RESPONSES/NEG-RESPONSE"):
            nr = create_any_structure_from_et(nr_elem, doc_frags)
            assert isinstance(nr, Response)
            negative_responses.append(nr)

        global_negative_responses = []
        for nr_elem in et_element.iterfind("GLOBAL-NEG-RESPONSES/GLOBAL-NEG-RESPONSE"):
            nr = create_any_structure_from_et(nr_elem, doc_frags)
            assert isinstance(nr, Response)
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

        communication_parameters = [
            CommunicationParameterRef.from_et(el, doc_frags, variant_type)
            for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")
        ]

        ecu_variant_patterns = [
            EcuVariantPattern.from_et(el, doc_frags)
            for el in et_element.iterfind("ECU-VARIANT-PATTERNS/ECU-VARIANT-PATTERN")
        ]
        if variant_type is not DiagLayerType.ECU_VARIANT:
            assert (
                len(ecu_variant_patterns) == 0
            ), "DiagLayer of type other than 'ECU-VARIANT' must not define a ECU-VARIANT-PATTERN"

        # Create DiagLayer
        return DiagLayerRaw(
            variant_type=variant_type,
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            admin_data=admin_data,
            company_datas=NamedItemList(short_name_as_id, company_datas),
            functional_classes=NamedItemList(short_name_as_id, functional_classes),
            diag_data_dictionary_spec=diag_data_dictionary_spec,
            diag_comms=diag_comms,
            requests=NamedItemList(short_name_as_id, requests),
            positive_responses=NamedItemList(short_name_as_id, positive_responses),
            negative_responses=NamedItemList(short_name_as_id, negative_responses),
            global_negative_responses=NamedItemList(short_name_as_id, global_negative_responses),
            import_refs=import_refs,
            state_charts=NamedItemList(short_name_as_id, state_charts),
            additional_audiences=NamedItemList(short_name_as_id, additional_audiences),
            sdgs=sdgs,
            parent_refs=parent_refs,
            communication_parameters=communication_parameters,
            ecu_variant_patterns=ecu_variant_patterns,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        odxlinks = {self.odx_id: self}

        for obj in chain(
            [self.admin_data],
                self.company_datas,
                self.functional_classes,
            [self.diag_data_dictionary_spec],
                self.diag_comms,
                self.requests,
                self.positive_responses,
                self.negative_responses,
                self.global_negative_responses,
                self.state_charts,
                self.additional_audiences,
                self.sdgs,
                self.parent_refs,
                self.communication_parameters,
        ):
            # the diag_comms may contain references.
            if obj is None or isinstance(obj, OdxLinkRef):
                continue

            odxlinks.update(obj._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all references."""

        # do reference resolution for the objects that do not use
        # short name references
        for obj in chain(
            [self.admin_data],
                self.company_datas,
                self.functional_classes,
            [self.diag_data_dictionary_spec],
                self.diag_comms,
                self.requests,
                self.positive_responses,
                self.negative_responses,
                self.global_negative_responses,
                self.state_charts,
                self.additional_audiences,
                self.sdgs,
                self.parent_refs,
                self.communication_parameters,
        ):
            if obj is None or isinstance(obj, OdxLinkRef):
                continue

            obj._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        # do reference resolution for the objects that may use short name
        # references
        for obj in chain(
            [self.admin_data],
                self.company_datas,
                self.functional_classes,
            [self.diag_data_dictionary_spec],
                self.diag_comms,
                self.requests,
                self.positive_responses,
                self.negative_responses,
                self.global_negative_responses,
                self.state_charts,
                self.additional_audiences,
                self.sdgs,
                self.parent_refs,
                self.communication_parameters,
        ):
            if obj is None or isinstance(obj, OdxLinkRef):
                continue

            obj._resolve_snrefs(diag_layer)

    def __str__(self) -> str:
        return f"DiagLayerRaw('{self.short_name}', type='{self.variant_type.value}')"
