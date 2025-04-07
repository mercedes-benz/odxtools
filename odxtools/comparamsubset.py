# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .comparam import Comparam
from .complexcomparam import ComplexComparam
from .dataobjectproperty import DataObjectProperty
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import DocType, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .unitspec import UnitSpec
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class ComparamSubset(OdxCategory):
    comparams: NamedItemList[Comparam] = field(default_factory=NamedItemList)
    complex_comparams: NamedItemList[ComplexComparam] = field(default_factory=NamedItemList)
    data_object_props: NamedItemList[DataObjectProperty] = field(default_factory=NamedItemList)
    unit_spec: UnitSpec | None = None
    category: str | None  # mandatory in ODX 2.2, but non-existent in ODX 2.0

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ComparamSubset":

        category_attrib = et_element.attrib.get("CATEGORY")

        # In ODX 2.0, COMPARAM-SPEC is used, whereas in ODX 2.2, it
        # refers to something else and has been replaced by
        # COMPARAM-SUBSET.
        # - If the 'CATEGORY' attribute is missing (ODX 2.0), use
        #   COMPARAM_SPEC,
        # - else (ODX 2.2), use COMPARAM_SUBSET.
        doc_type = DocType.COMPARAM_SUBSET if category_attrib is not None else DocType.COMPARAM_SPEC
        base_obj = OdxCategory.category_from_et(et_element, context, doc_type=doc_type)
        kwargs = dataclass_fields_asdict(base_obj)

        comparams = NamedItemList(
            [Comparam.from_et(el, context) for el in et_element.iterfind("COMPARAMS/COMPARAM")])
        complex_comparams = NamedItemList([
            ComplexComparam.from_et(el, context)
            for el in et_element.iterfind("COMPLEX-COMPARAMS/COMPLEX-COMPARAM")
        ])
        data_object_props = NamedItemList([
            DataObjectProperty.from_et(el, context)
            for el in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ])
        unit_spec = None
        if (unit_spec_elem := et_element.find("UNIT-SPEC")) is not None:
            unit_spec = UnitSpec.from_et(unit_spec_elem, context)

        return ComparamSubset(
            category=category_attrib,
            comparams=comparams,
            complex_comparams=complex_comparams,
            data_object_props=data_object_props,
            unit_spec=unit_spec,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for comparam in self.comparams:
            odxlinks.update(comparam._build_odxlinks())

        for ccomparam in self.complex_comparams:
            odxlinks.update(ccomparam._build_odxlinks())

        for dop in self.data_object_props:
            odxlinks[dop.odx_id] = dop

        if self.unit_spec:
            odxlinks.update(self.unit_spec._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for comparam in self.comparams:
            comparam._resolve_odxlinks(odxlinks)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_odxlinks(odxlinks)

        for dop in self.data_object_props:
            dop._resolve_odxlinks(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for comparam in self.comparams:
            comparam._resolve_snrefs(context)

        for ccomparam in self.complex_comparams:
            ccomparam._resolve_snrefs(context)

        for dop in self.data_object_props:
            dop._resolve_snrefs(context)

        if self.unit_spec:
            self.unit_spec._resolve_snrefs(context)
