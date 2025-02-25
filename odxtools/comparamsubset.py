# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .comparam import Comparam
from .complexcomparam import ComplexComparam
from .dataobjectproperty import DataObjectProperty
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .unitspec import UnitSpec
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass
class ComparamSubset(OdxCategory):
    comparams: NamedItemList[Comparam]
    complex_comparams: NamedItemList[ComplexComparam]
    data_object_props: NamedItemList[DataObjectProperty]
    unit_spec: Optional[UnitSpec]
    category: Optional[str]  # mandatory in ODX 2.2, but non-existent in ODX 2.0

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "ComparamSubset":

        category = et_element.get("CATEGORY")

        # In ODX 2.0, COMPARAM-SPEC is used, whereas in ODX 2.2, it refers to something else and has been replaced by COMPARAM-SUBSET.
        # - If 'category' is missing (ODX 2.0), use COMPARAM_SPEC,
        # - else (ODX 2.2), use COMPARAM_SUBSET.
        doc_type = DocType.COMPARAM_SUBSET if category else DocType.COMPARAM_SPEC
        cat = OdxCategory.category_from_et(et_element, doc_frags, doc_type=doc_type)
        doc_frags = cat.odx_id.doc_fragments
        kwargs = dataclass_fields_asdict(cat)

        data_object_props = NamedItemList([
            DataObjectProperty.from_et(el, doc_frags)
            for el in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ])
        comparams = NamedItemList(
            [Comparam.from_et(el, doc_frags) for el in et_element.iterfind("COMPARAMS/COMPARAM")])
        complex_comparams = NamedItemList([
            ComplexComparam.from_et(el, doc_frags)
            for el in et_element.iterfind("COMPLEX-COMPARAMS/COMPLEX-COMPARAM")
        ])
        if (unit_spec_elem := et_element.find("UNIT-SPEC")) is not None:
            unit_spec = UnitSpec.from_et(unit_spec_elem, doc_frags)
        else:
            unit_spec = None

        return ComparamSubset(
            category=category,
            data_object_props=data_object_props,
            comparams=comparams,
            complex_comparams=complex_comparams,
            unit_spec=unit_spec,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for dop in self.data_object_props:
            odxlinks[dop.odx_id] = dop

        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())

        for ccomparam in self.complex_comparams:
            odxlinks.update(ccomparam._build_odxlinks())

        if self.unit_spec:
            odxlinks.update(self.unit_spec._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for dop in self.data_object_props:
            dop._resolve_odxlinks(odxlinks)

        for comparam in self.comparams:
            comparam._resolve_odxlinks(odxlinks)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_odxlinks(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for dop in self.data_object_props:
            dop._resolve_snrefs(context)

        for comparam in self.comparams:
            comparam._resolve_snrefs(context)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_snrefs(context)

        if self.unit_spec:
            self.unit_spec._resolve_snrefs(context)
