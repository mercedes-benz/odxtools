# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from .complexdop import ComplexDop
from .createsdgs import create_sdgs_from_et
from .decodestate import DecodeState
from .encodestate import EncodeState
from .environmentdata import EnvironmentData
from .exceptions import DecodeError, EncodeError, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue, odxstr_to_bool
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class EnvironmentDataDescription(ComplexDop):
    """This class represents Environment Data Description, which is a complex DOP
    that is used to define the interpretation of environment data."""

    # in ODX 2.0.0, ENV-DATAS seems to be a mandatory
    # sub-element of ENV-DATA-DESC, on ODX 2.2 it is not
    # present
    env_datas: List[EnvironmentData]
    env_data_refs: List[OdxLinkRef]
    param_snref: Optional[str]
    param_snpathref: Optional[str]

    def __post_init__(self) -> None:
        self.bit_length = None

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EnvironmentDataDescription":
        """Reads Environment Data Description from Diag Layer."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        param_snref_elem = et_element.find("PARAM-SNREF")
        param_snref = None
        if param_snref_elem is not None:
            param_snref = odxrequire(param_snref_elem.get("SHORT-NAME"))
        param_snpathref_elem = et_element.find("PARAM-SNPATHREF")
        param_snpathref = None
        if param_snpathref_elem is not None:
            param_snpathref = odxrequire(param_snpathref_elem.get("SHORT-NAME-PATH"))
        env_data_refs = [
            odxrequire(OdxLinkRef.from_et(env_data_ref, doc_frags))
            for env_data_ref in et_element.iterfind("ENV-DATA-REFS/ENV-DATA-REF")
        ]

        # ODX 2.0.0 says ENV-DATA-DESC could contain a list of ENV-DATAS
        env_datas = [
            EnvironmentData.from_et(env_data_elem, doc_frags)
            for env_data_elem in et_element.iterfind("ENV-DATAS/ENV-DATA")
        ]

        return EnvironmentDataDescription(
            sdgs=sdgs,
            is_visible_raw=is_visible_raw,
            param_snref=param_snref,
            param_snpathref=param_snpathref,
            env_datas=env_datas,
            env_data_refs=env_data_refs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        for ed in self.env_datas:
            odxlinks.update(ed._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # ODX 2.0 specifies environment data objects here, ODX 2.2
        # uses references
        if self.env_data_refs:
            self.env_datas = [odxlinks.resolve(x) for x in self.env_data_refs]
        else:
            for ed in self.env_datas:
                ed._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        # ODX 2.0 specifies environment data objects here, ODX 2.2
        # uses references
        if self.env_data_refs:
            for ed in self.env_datas:
                ed._resolve_snrefs(diag_layer)

    def convert_physical_to_bytes(self, physical_value: ParameterValue, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        """Convert the physical value into bytes.

        Since environmental data is supposed to never appear on the
        wire, this method just raises an EncodeError exception.
        """
        raise EncodeError("EnvironmentDataDescription DOPs cannot be encoded or decoded")

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:
        """Extract the bytes from the PDU and convert them to the physical value.

        Since environmental data is supposed to never appear on the
        wire, this method just raises an DecodeError exception.
        """
        raise DecodeError("EnvironmentDataDescription DOPs cannot be encoded or decoded")
