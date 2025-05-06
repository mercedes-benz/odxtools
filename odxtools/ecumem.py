# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .admindata import AdminData
from .element import IdentifiableElement
from .exceptions import odxrequire
from .mem import Mem
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .physmem import PhysMem
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EcuMem(IdentifiableElement):
    admin_data: AdminData | None = None
    mem: Mem
    phys_mem: PhysMem | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuMem":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        mem = Mem.from_et(odxrequire(et_element.find("MEM")), context)
        phys_mem = None
        if (phys_mem_elem := et_element.find("PHYS-MEM")) is not None:
            phys_mem = PhysMem.from_et(phys_mem_elem, context)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return EcuMem(admin_data=admin_data, mem=mem, phys_mem=phys_mem, sdgs=sdgs, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        if self.admin_data is not None:
            odxlinks.update(self.admin_data._build_odxlinks())

        odxlinks.update(self.mem._build_odxlinks())
        if self.phys_mem is not None:
            odxlinks.update(self.phys_mem._build_odxlinks())
        for sdg in self.sdgs:
            odxlinks.update(sdg._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        self.mem._resolve_odxlinks(odxlinks)
        if self.phys_mem is not None:
            self.phys_mem._resolve_odxlinks(odxlinks)
        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)

        self.mem._resolve_snrefs(context)
        if self.phys_mem is not None:
            self.phys_mem._resolve_snrefs(context)
        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
