from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional
from xml.etree import ElementTree

from .basicstructure import BasicStructure
from .complexdop import ComplexDop
from .createsdgs import create_sdgs_from_et
from .environmentdatadescription import EnvironmentDataDescription
from .exceptions import odxassert, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Field(ComplexDop):
    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]
    env_data_desc_ref: Optional[OdxLinkRef]
    env_data_desc_snref: Optional[str]

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
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

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
            sdgs=sdgs,
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            env_data_desc_ref=env_data_desc_ref,
            env_data_desc_snref=env_data_desc_snref,
            is_visible_raw=is_visible_raw,
            **kwargs)

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

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        """Recursively resolve any short-name references"""
        if self.structure_snref is not None:
            structures = diag_layer.diag_data_dictionary_spec.structures
            self._structure = odxrequire(structures.get(self.structure_snref))

        if self.env_data_desc_snref is not None:
            env_data_descs = diag_layer.diag_data_dictionary_spec.env_data_descs
            self._env_data_desc = odxrequire(env_data_descs.get(self.env_data_desc_snref))
