# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from .complexdop import ComplexDop
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxraise, odxrequire
from .multiplexercase import MultiplexerCase
from .multiplexerdefaultcase import MultiplexerDefaultCase
from .multiplexerswitchkey import MultiplexerSwitchKey
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, ParameterValue, odxstr_to_bool
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


@dataclass
class Multiplexer(ComplexDop):
    """This class represents a Multiplexer (MUX)

    Multiplexers are used to interpret data stream depending on the
    value of a switch-key (similar to switch-case statements in
    programming languages like C or Java).
    """

    byte_position: int
    switch_key: MultiplexerSwitchKey
    default_case: Optional[MultiplexerDefaultCase]
    cases: List[MultiplexerCase]
    is_visible_raw: Optional[bool]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Multiplexer":
        """Reads a Multiplexer from Diag Layer."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))

        byte_position = int(et_element.findtext("BYTE-POSITION", "0"))
        switch_key = MultiplexerSwitchKey.from_et(
            odxrequire(et_element.find("SWITCH-KEY")), doc_frags)

        default_case = None
        if (dc_elem := et_element.find("DEFAULT-CASE")) is not None:
            default_case = MultiplexerDefaultCase.from_et(dc_elem, doc_frags)

        cases = []
        if (cases_elem := et_element.find("CASES")) is not None:
            cases = [MultiplexerCase.from_et(el, doc_frags) for el in cases_elem.iterfind("CASE")]

        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        return Multiplexer(
            is_visible_raw=is_visible_raw,
            byte_position=byte_position,
            switch_key=switch_key,
            default_case=default_case,
            cases=cases,
            **kwargs)

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw is True

    def _get_case_limits(self, case: MultiplexerCase) -> Tuple[AtomicOdxType, AtomicOdxType]:
        key_type = self.switch_key.dop.physical_type.base_data_type
        lower_limit = key_type.make_from(case.lower_limit)
        upper_limit = key_type.make_from(case.upper_limit)
        if not isinstance(lower_limit, type(upper_limit)) and not isinstance(
                upper_limit, type(lower_limit)):
            odxraise("Upper and lower bounds of limits must compareable")
        return lower_limit, upper_limit

    def convert_physical_to_bytes(self, physical_value: ParameterValue, encode_state: EncodeState,
                                  bit_position: int) -> bytes:

        if bit_position != 0:
            raise EncodeError("Multiplexer must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")

        if not isinstance(physical_value, dict) or len(physical_value) != 1:
            raise EncodeError("""Multiplexer should be defined as a dict
            with only one key equal to the desired case""")

        case_name, case_value = next(iter(physical_value.items()))
        case_pos = self.byte_position

        for mux_case in self.cases or []:
            if mux_case.short_name == case_name:
                if mux_case._structure:
                    case_bytes = mux_case._structure.convert_physical_to_bytes(
                        case_value, encode_state, 0)
                else:
                    case_bytes = b''

                key_value, _ = self._get_case_limits(mux_case)
                key_bytes = self.switch_key.dop.convert_physical_to_bytes(
                    key_value, encode_state, bit_position=self.switch_key.bit_position or 0)

                mux_len = max(len(key_bytes), len(case_bytes) + case_pos)
                mux_bytes = bytearray(mux_len)
                mux_bytes[:len(key_bytes)] = key_bytes
                mux_bytes[case_pos:case_pos + len(case_bytes)] = case_bytes

                return bytes(mux_bytes)

        raise EncodeError(f"The case {case_name} is not found in Multiplexer {self.short_name}")

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        # multiplexers are structures and thus the origin position
        # must be moved to the start of the multiplexer
        orig_origin = decode_state.origin_byte_position
        orig_cursor = decode_state.cursor_byte_position
        if self.byte_position is not None:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        key_value = self.switch_key.dop.decode_from_pdu(decode_state)

        if not isinstance(key_value, int):
            odxraise(f"Multiplexer keys must be integers (is '{type(key_value).__name__}'"
                     f" for multiplexer '{self.short_name}')")

        case_value: Optional[ParameterValue] = None
        for case in self.cases or []:
            lower, upper = self._get_case_limits(case)
            if lower <= key_value and key_value <= upper:  # type: ignore[operator]
                if case._structure:
                    case_value = case._structure.decode_from_pdu(decode_state)
                break

        if case_value is None and self.default_case is not None:
            if self.default_case._structure:
                case_value = self.default_case._structure.decode_from_pdu(decode_state)

        if case_value is None:
            odxraise(f"Failed to find a matching case in {self.short_name} for value {key_value!r}",
                     DecodeError)

        mux_value = (case.short_name, case_value)

        # go back to the original origin
        decode_state.origin_byte_position = orig_origin
        decode_state.cursor_byte_position = max(orig_cursor, decode_state.cursor_byte_position)

        return mux_value

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        odxlinks.update(self.switch_key._build_odxlinks())
        if self.default_case is not None:
            odxlinks.update(self.default_case._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self.switch_key._resolve_odxlinks(odxlinks)
        if self.default_case is not None:
            self.default_case._resolve_odxlinks(odxlinks)

        for case in self.cases:
            case._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        self.switch_key._resolve_snrefs(diag_layer)
        if self.default_case is not None:
            self.default_case._resolve_snrefs(diag_layer)

        for case in self.cases:
            case._resolve_snrefs(diag_layer)
