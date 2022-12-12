

from dataclasses import dataclass, field
from typing import Any, Union, Dict, List, Literal, Optional
from xml.etree.ElementTree import Element

from .dataobjectproperty import DataObjectProperty, read_data_object_property_from_odx
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .units import UnitSpec, read_unit_spec_from_odx
from .admindata import AdminData, read_admin_data_from_odx
from .companydata import CompanyData, read_company_datas_from_odx
from .utils import read_description_from_odx, short_name_as_id
from .specialdata import SpecialDataGroup, read_sdgs_from_odx

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

def read_complex_value_from_odx(et_element) -> ComplexValue:
    result = []
    for el in et_element:
        if el.tag == "SIMPLE-VALUE":
            result.append('' if el.text is None else el.text)
        else:
            result.append(read_complex_value_from_odx(el))
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

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        pass

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}


@dataclass()
class ComplexComparam(BaseComparam):
    comparams: NamedItemList[BaseComparam]
    complex_physical_default_value: Optional[ComplexValue] = field(default=None, init=False)
    allow_multiple_values: Optional[bool] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
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
    _dop: Optional[DataObjectProperty] = field(default=None, init=False)

    @property
    def dop(self) -> DataObjectProperty:
        """The data object property describing this parameter."""
        assert self._dop is not None
        return self._dop

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        """Resolves the reference to the dop"""
        self._dop = odxlinks.resolve(self.dop_ref)


@dataclass()
class ComparamSubset:
    odx_id: Optional[OdxLinkId]
    short_name: str
    category: str
    data_object_props: NamedItemList[DataObjectProperty]
    comparams: NamedItemList[BaseComparam]
    unit_spec: Optional[UnitSpec] = None
    long_name: Optional[str] = None
    description: Optional[str] = None
    admin_data: Optional[AdminData] = None
    company_datas: Optional[NamedItemList[CompanyData]] = None
    sdgs: List[SpecialDataGroup] = field(default_factory=list)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks: Dict[OdxLinkId, Any] = {}
        if self.odx_id is not None:
            odxlinks[self.odx_id] = self

        for dop in self.data_object_props:
            odxlinks[dop.odx_id] = dop

        for comparam in self.comparams:
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

        if self.unit_spec:
            self.unit_spec._resolve_references(odxlinks)

        if self.admin_data is not None:
            self.admin_data._resolve_references(odxlinks)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_references(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_references(odxlinks)

def read_comparam_from_odx(et_element, doc_frags: List[OdxDocFragment]) -> BaseComparam:
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.findtext("SHORT-NAME")
    param_class = et_element.attrib.get("PARAM-CLASS")
    cptype = et_element.attrib.get("CPTYPE")
    cpusage = et_element.attrib.get("CPUSAGE")

    comparam: BaseComparam
    if et_element.tag == "COMPARAM":
        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)
        assert dop_ref is not None
        comparam = Comparam(
            odx_id=odx_id,
            short_name=short_name,
            param_class=param_class,
            cptype=cptype,
            cpusage=cpusage,
            dop_ref=dop_ref,
        )
        comparam.physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")
    elif et_element.tag == "COMPLEX-COMPARAM":
        comparams = [
            read_comparam_from_odx(el, doc_frags)
            for el in et_element if el.tag in ('COMPARAM', 'COMPLEX-COMPARAM')
        ]
        comparam = ComplexComparam(
            odx_id=odx_id,
            short_name=short_name,
            param_class=param_class,
            cptype=cptype,
            cpusage=cpusage,
            comparams=NamedItemList(short_name_as_id, comparams),
        )
        if cpdv_elem := et_element.find("COMPLEX-PHYSICAL-DEFAULT-VALUE"):
            comparam.complex_physical_default_value=read_complex_value_from_odx(cpdv_elem)

        tmp = et_element.get("ALLOW-MULTIPLE-VALUES")
        comparam.allow_multiple_values = (tmp == "true") if tmp is not None else None
    else:
        assert False, f"Failed to parse COMPARAM {short_name}"

    comparam.long_name = et_element.findtext("LONG-NAME")
    comparam.description = read_description_from_odx(et_element.find("DESC"))
    display_level = et_element.attrib.get("DISPLAY-LEVEL", None)
    if display_level is not None:
        comparam.display_level = int(display_level)

    return comparam


def read_comparam_subset_from_odx(et_element: Element) -> ComparamSubset:

    category = et_element.get("CATEGORY")
    assert category is not None

    short_name = et_element.findtext("SHORT-NAME")
    assert short_name is not None

    doc_frags = [OdxDocFragment(short_name, str(et_element.tag))]
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    admin_data = \
        read_admin_data_from_odx(et_element.find("ADMIN-DATA"), doc_frags)
    company_datas = \
        read_company_datas_from_odx(et_element.find("COMPANY-DATAS"), doc_frags)

    data_object_props = [
        read_data_object_property_from_odx(el, doc_frags)
        for el in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
    ]
    comparams: List[BaseComparam] = []
    comparams += [
        read_comparam_from_odx(el, doc_frags)
        for el in et_element.iterfind("COMPARAMS/COMPARAM")
    ]
    comparams += [
        read_comparam_from_odx(el, doc_frags)
        for el in et_element.iterfind("COMPLEX-COMPARAMS/COMPLEX-COMPARAM")
    ]
    if unit_spec_elem := et_element.find("UNIT-SPEC"):
        unit_spec = read_unit_spec_from_odx(unit_spec_elem, doc_frags)
    else:
        unit_spec = None

    sdgs = read_sdgs_from_odx(et_element.find("SDGS"), doc_frags)

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
        unit_spec=unit_spec,
        sdgs=sdgs,
    )
