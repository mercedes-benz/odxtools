from dataclasses import dataclass, field
from typing import Any, Union, Dict, List, Literal, Optional
from xml.etree.ElementTree import Element

from .dataobjectproperty import DataObjectProperty
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .units import UnitSpec
from .admindata import AdminData
from .companydata import CompanyData, create_company_datas_from_et
from .utils import create_description_from_et, short_name_as_id
from .odxtypes import odxstr_to_bool
from .specialdata import SpecialDataGroup, create_sdgs_from_et

StandardizationLevel = Literal[
    "STANDARD",
    "OEM-SPECIFIC",
    "OPTIONAL",
    "OEM-OPTIONAL",
]

Usage = Literal[
    "ECU-SOFTWARE",
    "ECU-COMM",
    "APPLICATION",
    "TESTER",
]

ComplexValue = List[ Union[str, "ComplexValue"] ]

def create_complex_value_from_et(et_element) -> ComplexValue:
    result = []
    for el in et_element:
        if el.tag == "SIMPLE-VALUE":
            result.append('' if el.text is None else el.text)
        else:
            result.append(create_complex_value_from_et(el))
    return result

@dataclass
class BaseComparam:
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = field(default=None, init=False)
    description: Optional[str] = field(default=None, init=False)
    param_class: str
    cptype: StandardizationLevel
    cpusage: Usage
    display_level: Optional[int] = field(default=None, init=False)

    def __init_from_et__(self, et_element, doc_frags: List[OdxDocFragment]) -> None:
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        self.odx_id = odx_id
        self.short_name = et_element.findtext("SHORT-NAME")
        self.long_name = et_element.findtext("LONG-NAME")
        self.description = create_description_from_et(et_element.find("DESC"))
        self.param_class = et_element.attrib.get("PARAM-CLASS")
        self.cptype = et_element.attrib.get("CPTYPE")
        self.cpusage = et_element.attrib.get("CPUSAGE")
        dl = et_element.attrib.get("DISPLAY_LEVEL")
        self.display_level = None if dl is None else int(dl)

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        pass

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}


@dataclass()
class ComplexComparam(BaseComparam):
    comparams: NamedItemList[BaseComparam]
    complex_physical_default_value: Optional[ComplexValue] = field(default=None, init=False)
    allow_multiple_values_raw: Optional[bool] = None

    @property
    def allow_multiple_values(self) -> bool:
        return self.allow_multiple_values_raw == True

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "ComplexComparam":
        # create an "empty" ComplexComparam object without calling the
        # "official" constructor. We need to do this because we need
        # all data attributes of the class to call the constructor,
        # including those which are supposed to be handled by the base
        # class (i.e., ComparamBase)
        result = ComplexComparam.__new__(ComplexComparam)

        # initialize the new "empty" object from the ElementTree
        result.__init_from_et__(et_element, doc_frags)

        return result

    def __init_from_et__(self, et_element, doc_frags: List[OdxDocFragment]) -> None:
        super().__init_from_et__(et_element, doc_frags)

        self.comparams = NamedItemList(short_name_as_id)
        for cp_el in et_element:
            if cp_el.tag in ('COMPARAM', 'COMPLEX-COMPARAM'):
                self.comparams.append(create_any_comparam_from_et(cp_el, doc_frags))

        if cpdv_elem := et_element.find("COMPLEX-PHYSICAL-DEFAULT-VALUE"):
            self.complex_physical_default_value = create_complex_value_from_et(cpdv_elem)

        self.allow_multiple_values_raw = odxstr_to_bool(et_element.get("ALLOW-MULTIPLE-VALUES"))

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        super()._resolve_references(odxlinks)
        for comparam in self.comparams:
            comparam._resolve_references(odxlinks)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())
        return odxlinks


@dataclass()
class Comparam(BaseComparam):
    dop_ref: OdxLinkRef
    physical_default_value: Optional[str] = field(default=None, init=False)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "Comparam":
        # create an "empty" Comparam object without calling the
        # "official" constructor. We need to do this because we need
        # all data attributes of the class to call the constructor,
        # including those which are supposed to be handled by the base
        # class (i.e., ComparamBase)
        result = Comparam.__new__(Comparam)

        # initialize the new "empty" object from the ElementTree
        result.__init_from_et__(et_element, doc_frags)

        return result

    def __init_from_et__(self, et_element, doc_frags: List[OdxDocFragment]) -> None:
        super().__init_from_et__(et_element, doc_frags)

        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)
        assert dop_ref is not None

        self.dop_ref = dop_ref
        self.physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

    @property
    def dop(self) -> DataObjectProperty:
        """The data object property describing this parameter."""
        return self._dop

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        """Resolves the reference to the dop"""
        super()._resolve_references(odxlinks)

        self._dop = odxlinks.resolve(self.dop_ref)
        assert isinstance(self._dop, DataObjectProperty)


@dataclass()
class ComparamSubset:
    odx_id: Optional[OdxLinkId]
    short_name: str
    category: str
    data_object_props: NamedItemList[DataObjectProperty]
    comparams: NamedItemList[Comparam]
    complex_comparams: NamedItemList[ComplexComparam]
    unit_spec: Optional[UnitSpec]
    long_name: Optional[str]
    description: Optional[str]
    admin_data: Optional[AdminData]
    company_datas: NamedItemList[CompanyData]
    sdgs: List[SpecialDataGroup]

    @staticmethod
    def from_et(et_element: Element) \
            -> "ComparamSubset":

        category = et_element.get("CATEGORY")
        assert category is not None

        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None

        doc_frags = [OdxDocFragment(short_name, str(et_element.tag))]
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        admin_data = \
            AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        company_datas = \
            create_company_datas_from_et(et_element.find("COMPANY-DATAS"), doc_frags)

        data_object_props = [
            DataObjectProperty.from_et(el, doc_frags)
            for el in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ]
        comparams = [
            Comparam.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPARAMS/COMPARAM")
        ]
        complex_comparams = [
            ComplexComparam.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPLEX-COMPARAMS/COMPLEX-COMPARAM")
        ]
        if unit_spec_elem := et_element.find("UNIT-SPEC"):
            unit_spec = UnitSpec.from_et(unit_spec_elem, doc_frags)
        else:
            unit_spec = None

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return ComparamSubset(
            odx_id=odx_id,
            category=category,
            short_name=short_name,
            long_name=long_name,
            description=description,
            admin_data=admin_data,
            company_datas=company_datas,
            data_object_props=NamedItemList(short_name_as_id, data_object_props),
            comparams=NamedItemList(short_name_as_id, comparams),
            complex_comparams=NamedItemList(short_name_as_id, complex_comparams),
            unit_spec=unit_spec,
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        if self.odx_id is not None:
            odxlinks[self.odx_id] = self

        for dop in self.data_object_props:
            odxlinks[dop.odx_id] = dop

        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())

        for comparam in self.complex_comparams:
            odxlinks.update(comparam._build_odxlinks())

        if self.unit_spec:
            odxlinks.update(self.unit_spec._build_odxlinks())

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())

        if self.company_datas is not None:
            for cd in self.company_datas:
                odxlinks.update(cd._build_odxlinks())

        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        for dop in self.data_object_props:
            dop._resolve_references(odxlinks)

        for comparam in self.comparams:
            comparam._resolve_references(odxlinks)

        for comparam in self.complex_comparams:
            comparam._resolve_references(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_references(odxlinks)

        if self.admin_data is not None:
            self.admin_data._resolve_references(odxlinks)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_references(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

def create_any_comparam_from_et(et_element,
                               doc_frags: List[OdxDocFragment]) -> BaseComparam:
    if et_element.tag == "COMPARAM":
        return Comparam.from_et(et_element, doc_frags)
    elif et_element.tag == "COMPLEX-COMPARAM":
        return ComplexComparam.from_et(et_element, doc_frags)

    raise RuntimeError(f"Unhandled communication parameter type {et_element.tag}")
