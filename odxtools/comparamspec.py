# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .protstack import ProtStack
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass
class ComparamSpec(OdxCategory):

    prot_stacks: NamedItemList[ProtStack]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: list[OdxDocFragment]) -> "ComparamSpec":

        base_obj = OdxCategory.category_from_et(
            et_element, doc_frags, doc_type=DocType.COMPARAM_SPEC)
        doc_frags = base_obj.odx_id.doc_fragments
        kwargs = dataclass_fields_asdict(base_obj)

        prot_stacks = NamedItemList([
            ProtStack.from_et(dl_element, doc_frags)
            for dl_element in et_element.iterfind("PROT-STACKS/PROT-STACK")
        ])

        return ComparamSpec(prot_stacks=prot_stacks, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for ps in self.prot_stacks:
            odxlinks.update(ps._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for ps in self.prot_stacks:
            ps._resolve_odxlinks(odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for ps in self.prot_stacks:
            ps._resolve_snrefs(context)
