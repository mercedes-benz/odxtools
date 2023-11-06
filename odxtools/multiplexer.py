# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast
from xml.etree import ElementTree

from .complexdop import ComplexDop
from .createsdgs import create_sdgs_from_et
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxrequire
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
    """This class represents a Multiplexer (MUX) which are used to interpret data stream depending on the value
    of a switch-key (similar to switch-case statements in programming languages like C or Java)."""

    byte_position: int
    switch_key: MultiplexerSwitchKey
    default_case: Optional[MultiplexerDefaultCase]
    cases: List[MultiplexerCase]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Multiplexer":
        """Reads a Multiplexer from Diag Layer."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)
        byte_position = int(et_element.findtext("BYTE-POSITION", "0"))
        switch_key = MultiplexerSwitchKey.from_et(
            odxrequire(et_element.find("SWITCH-KEY")), doc_frags)

        default_case = None
        if (dc_elem := et_element.find("DEFAULT-CASE")) is not None:
            default_case = MultiplexerDefaultCase.from_et(dc_elem, doc_frags)

        cases = []
        if (cases_elem := et_element.find("CASES")) is not None:
            cases = [MultiplexerCase.from_et(el, doc_frags) for el in cases_elem.iterfind("CASE")]

        return Multiplexer(
            sdgs=sdgs,
            is_visible_raw=is_visible_raw,
            byte_position=byte_position,
            switch_key=switch_key,
            default_case=default_case,
            cases=cases,
            **kwargs)

    def _get_case_limits(self, case: MultiplexerCase) -> Tuple[AtomicOdxType, AtomicOdxType]:
        key_type = self.switch_key.dop.physical_type.base_data_type
        lower_limit = key_type.make_from(case.lower_limit)
        upper_limit = key_type.make_from(case.upper_limit)
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

        for case in self.cases or []:
            if case.short_name == case_name:
                if case._structure:
                    case_bytes = case._structure.convert_physical_to_bytes(
                        case_value, encode_state, 0)
                else:
                    case_bytes = b''

                key_value, _ = self._get_case_limits(case)
                key_bytes = self.switch_key.dop.convert_physical_to_bytes(
                    key_value, encode_state, bit_position=self.switch_key.bit_position or 0)

                mux_len = max(len(key_bytes), len(case_bytes) + case_pos)
                mux_bytes = bytearray(mux_len)
                mux_bytes[:len(key_bytes)] = key_bytes
                mux_bytes[case_pos:case_pos + len(case_bytes)] = case_bytes

                return bytes(mux_bytes)

        raise EncodeError(f"The case {case_name} is not found in Multiplexer {self.short_name}")

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValue, int]:

        if bit_position != 0:
            raise DecodeError("Multiplexers must be byte-aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")
        key_value, key_next_byte = self.switch_key.dop.convert_bytes_to_physical(decode_state)

        byte_code = decode_state.coded_message[decode_state.cursor_position:]
        case_decode_state = DecodeState(
            coded_message=byte_code[self.byte_position:],
            parameter_values={},
            cursor_position=0,
        )
        case_found = False
        case_next_byte = 0
        case_value = None
        for case in self.cases or []:
            lower, upper = self._get_case_limits(case)
            if lower <= key_value and key_value <= upper:
                case_found = True
                if case._structure:
                    case_value, case_next_byte = case._structure.convert_bytes_to_physical(
                        case_decode_state)
                break

        if not case_found and self.default_case is not None:
            case_found = True
            if self.default_case._structure:
                case_value, case_next_byte = self.default_case._structure.convert_bytes_to_physical(
                    case_decode_state)

        if not case_found:
            raise DecodeError(
                f"Failed to find a matching case in {self.short_name} for value {key_value!r}")

        mux_value = {case.short_name: cast(ParameterValue, case_value)}
        mux_next_byte = decode_state.cursor_position + max(
            key_next_byte + self.switch_key.byte_position, case_next_byte + self.byte_position)
        return mux_value, mux_next_byte

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
