# SPDX-License-Identifier: MIT
# from dataclasses import dataclass, field
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast
from xml.etree import ElementTree

from .compumethods.compumethod import CompuMethod
from .compumethods.createanycompumethod import create_any_compu_method_from_et
from .createanydiagcodedtype import create_any_diag_coded_type_from_et
from .decodestate import DecodeState
from .diagcodedtype import DiagCodedType
from .diagnostictroublecode import DiagnosticTroubleCode
from .dopbase import DopBase
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue, odxstr_to_bool
from .physicaltype import PhysicalType
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DtcDop(DopBase):
    """A DOP describing a diagnostic trouble code"""

    diag_coded_type: DiagCodedType
    physical_type: PhysicalType
    compu_method: CompuMethod
    dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]]
    linked_dtc_dop_refs: List[OdxLinkRef]
    is_visible_raw: Optional[bool]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DtcDop":
        """Reads a DTC-DOP."""
        kwargs = dataclass_fields_asdict(DopBase.from_et(et_element, doc_frags))

        diag_coded_type = create_any_diag_coded_type_from_et(
            odxrequire(et_element.find("DIAG-CODED-TYPE")), doc_frags)
        physical_type = PhysicalType.from_et(
            odxrequire(et_element.find("PHYSICAL-TYPE")), doc_frags)
        compu_method = create_any_compu_method_from_et(
            odxrequire(et_element.find("COMPU-METHOD")),
            doc_frags,
            diag_coded_type.base_data_type,
            physical_type.base_data_type,
        )
        dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]] = []
        if (dtcs_elem := et_element.find("DTCS")) is not None:
            for dtc_proxy_elem in dtcs_elem:
                if dtc_proxy_elem.tag == "DTC":
                    dtcs_raw.append(DiagnosticTroubleCode.from_et(dtc_proxy_elem, doc_frags))
                elif dtc_proxy_elem.tag == "DTC-REF":
                    dtcs_raw.append(OdxLinkRef.from_et(dtc_proxy_elem, doc_frags))

        # TODO: NOT-INHERITED-DTC-SNREFS
        linked_dtc_dop_refs = [
            cast(OdxLinkRef, OdxLinkRef.from_et(dtc_ref_elem, doc_frags))
            for dtc_ref_elem in et_element.iterfind("LINKED-DTC-DOPS/"
                                                    "LINKED-DTC-DOP/"
                                                    "DTC-DOP-REF")
        ]
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        return DtcDop(
            diag_coded_type=diag_coded_type,
            physical_type=physical_type,
            compu_method=compu_method,
            dtcs_raw=dtcs_raw,
            linked_dtc_dop_refs=linked_dtc_dop_refs,
            is_visible_raw=is_visible_raw,
            **kwargs)

    @property
    def dtcs(self) -> NamedItemList[DiagnosticTroubleCode]:
        return self._dtcs

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw is True

    @property
    def linked_dtc_dops(self) -> NamedItemList["DtcDop"]:
        return self._linked_dtc_dops

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:

        int_trouble_code, cursor_position = self.diag_coded_type.convert_bytes_to_internal(
            decode_state, bit_position=bit_position)

        if self.compu_method.is_valid_internal_value(int_trouble_code):
            trouble_code = self.compu_method.convert_internal_to_physical(int_trouble_code)
        else:
            # TODO: How to prevent this?
            raise DecodeError(
                f"DTC-DOP {self.short_name} could not convert the coded value "
                f" {repr(int_trouble_code)} to physical type {self.physical_type.base_data_type}.")

        assert isinstance(trouble_code, int)

        dtcs = [x for x in self.dtcs if x.trouble_code == trouble_code]

        odxassert(len(dtcs) < 2, f"Multiple matching DTCs for trouble code 0x{trouble_code:06x}")

        if len(dtcs) == 1:
            # we found exactly one described DTC
            return dtcs[0], cursor_position

        # the DTC was not specified. This probably means that the
        # diagnostic description file is incomplete. We do not bail
        # out but we cannot provide an interpretation for it out of the
        # box...
        dtc = DiagnosticTroubleCode(
            trouble_code=trouble_code,
            odx_id=cast(OdxLinkId, None),
            short_name=f'DTC_{trouble_code:06x}',
            long_name=None,
            description=None,
            text=None,
            display_trouble_code=None,
            level=None,
            is_temporary_raw=None,
            sdgs=[],
        )

        return dtc, cursor_position

    def convert_physical_to_bytes(self, physical_value: ParameterValue, encode_state: EncodeState,
                                  bit_position: int) -> bytes:
        if isinstance(physical_value, DiagnosticTroubleCode):
            trouble_code = physical_value.trouble_code
        elif isinstance(physical_value, int):
            # assume that physical value is the trouble_code
            trouble_code = physical_value
        elif isinstance(physical_value, str):
            # assume that physical value is the short_name
            dtc = next(filter(lambda dtc: dtc.short_name == physical_value, self.dtcs))
            trouble_code = dtc.trouble_code
        else:
            raise EncodeError(f"The DTC-DOP {self.short_name} expected a"
                              f" DiagnosticTroubleCode but got {physical_value!r}.")

        return super().convert_physical_to_bytes(trouble_code, encode_state, bit_position)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                odxlinks.update(dtc_proxy._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self._dtcs = NamedItemList[DiagnosticTroubleCode]()
        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                dtc_proxy._resolve_odxlinks(odxlinks)
                self._dtcs.append(dtc_proxy)
            elif isinstance(dtc_proxy, OdxLinkRef):
                dtc = odxlinks.resolve(dtc_proxy, DiagnosticTroubleCode)
                self._dtcs.append(dtc)

        linked_dtc_dops = [odxlinks.resolve(x, DtcDop) for x in self.linked_dtc_dop_refs]
        self._linked_dtc_dops = NamedItemList(linked_dtc_dops)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                dtc_proxy._resolve_snrefs(diag_layer)
