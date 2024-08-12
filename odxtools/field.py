# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .complexdop import ComplexDop
from .environmentdatadescription import EnvironmentDataDescription
from .exceptions import odxassert, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkRef, resolve_snref
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class Field(ComplexDop):
    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]
    env_data_desc_ref: Optional[OdxLinkRef]
    env_data_desc_snref: Optional[str]
    is_visible_raw: Optional[bool]

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None
        self._env_data_desc: Optional[EnvironmentDataDescription] = None
        num_struct_refs = 0 if self.structure_ref is None else 1
        num_struct_refs += 0 if self.structure_snref is None else 1

        num_edd_refs = 0 if self.env_data_desc_ref is None else 1
        num_edd_refs += 0 if self.env_data_desc_snref is None else 1

        odxassert(
            num_struct_refs + num_edd_refs == 1,
            "FIELDs need to specify exactly one reference to a "
            "structure or an environment data description")

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Field":
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))

        structure_ref = OdxLinkRef.from_et(et_element.find("BASIC-STRUCTURE-REF"), doc_frags)
        structure_snref = None
        if (edsnr_elem := et_element.find("BASIC-STRUCTURE-SNREF")) is not None:
            structure_snref = edsnr_elem.get("SHORT-NAME")

        env_data_desc_ref = OdxLinkRef.from_et(et_element.find("ENV-DATA-DESC-REF"), doc_frags)
        env_data_desc_snref = None
        if (edsnr_elem := et_element.find("ENV-DATA-DESC-SNREF")) is not None:
            env_data_desc_snref = edsnr_elem.get("SHORT-NAME")

        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        return Field(
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            env_data_desc_ref=env_data_desc_ref,
            env_data_desc_snref=env_data_desc_snref,
            is_visible_raw=is_visible_raw,
            **kwargs)

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw in (None, True)

    @property
    def structure(self) -> BasicStructure:
        """may be a Structure or a env-data-desc"""
        return odxrequire(self._structure, "EnvironmentDataDescription is not supported")

    def get_static_bit_length(self) -> Optional[int]:
        return None

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any odxlinks references"""
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref, BasicStructure)

        if self.env_data_desc_ref is not None:
            self._env_data_desc = odxlinks.resolve(self.env_data_desc_ref,
                                                   EnvironmentDataDescription)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        """Recursively resolve any short-name references"""
        ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec

        if self.structure_snref is not None:
            self._structure = resolve_snref(self.structure_snref, ddds.structures, BasicStructure)

        if self.env_data_desc_snref is not None:
            self._env_data_desc = resolve_snref(self.env_data_desc_snref, ddds.env_data_descs,
                                                EnvironmentDataDescription)
