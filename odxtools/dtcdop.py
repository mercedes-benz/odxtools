# SPDX-License-Identifier: MIT
# from dataclasses import dataclass, field
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union, cast

from .dataobjectproperty import DataObjectProperty
from .decodestate import DecodeState
from .diagnostictroublecode import DiagnosticTroubleCode
from .encodestate import EncodeState
from .exceptions import EncodeError, odxassert
from .nameditemlist import NamedItemList
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class DtcDop(DataObjectProperty):
    """A DOP describing a diagnostic trouble code"""

    dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]]
    linked_dtc_dop_refs: List[OdxLinkRef]

    @property
    def dtcs(self) -> NamedItemList[DiagnosticTroubleCode]:
        return self._dtcs

    @property
    def linked_dtc_dops(self) -> NamedItemList["DtcDop"]:
        return self._linked_dtc_dops

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:
        trouble_code, cursor_position = super().convert_bytes_to_physical(
            decode_state, bit_position=bit_position)

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
