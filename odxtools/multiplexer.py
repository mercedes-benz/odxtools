# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from xml.etree import ElementTree

from typing_extensions import override

from .complexdop import ComplexDop
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .multiplexercase import MultiplexerCase
from .multiplexerdefaultcase import MultiplexerDefaultCase
from .multiplexerswitchkey import MultiplexerSwitchKey
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, ParameterValue, odxstr_to_bool
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


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
    cases: NamedItemList[MultiplexerCase]
    is_visible_raw: Optional[bool]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Multiplexer":
        """Reads a Multiplexer from Diag Layer."""
        base_obj = ComplexDop.from_et(et_element, doc_frags)
        kwargs = dataclass_fields_asdict(base_obj)

        byte_position = int(et_element.findtext("BYTE-POSITION", "0"))
        switch_key = MultiplexerSwitchKey.from_et(
            odxrequire(et_element.find("SWITCH-KEY")), doc_frags)

        default_case = None
        if (dc_elem := et_element.find("DEFAULT-CASE")) is not None:
            default_case = MultiplexerDefaultCase.from_et(dc_elem, doc_frags)

        cases = NamedItemList(
            [MultiplexerCase.from_et(el, doc_frags) for el in et_element.iterfind("CASES/CASE")])

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
        lower_limit = key_type.make_from(case.lower_limit.value)
        upper_limit = key_type.make_from(case.upper_limit.value)
        if not isinstance(lower_limit, type(upper_limit)) and not isinstance(
                upper_limit, type(lower_limit)):
            odxraise("Upper and lower bounds of limits must compareable")
        return lower_limit, upper_limit

    @override
    def encode_into_pdu(self, physical_value: ParameterValue, encode_state: EncodeState) -> None:

        if encode_state.cursor_bit_position != 0:
            raise EncodeError(f"Multiplexer parameters must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position "
                              f"{encode_state.cursor_bit_position}")

        orig_origin = encode_state.origin_byte_position
        encode_state.origin_byte_position = encode_state.cursor_byte_position

        if isinstance(physical_value, (list, tuple)) and len(physical_value) == 2:
            case_spec, case_value = physical_value
        elif isinstance(physical_value, dict) and len(physical_value) == 1:
            case_spec, case_value = next(iter(physical_value.items()))
        else:
            raise EncodeError(
                f"Values of multiplexer parameters must be defined as a "
                f"(case_name, content_value) tuple instead of as '{physical_value!r}'")

        mux_case: Union[MultiplexerCase, MultiplexerDefaultCase]
        applicable_cases: List[Union[MultiplexerCase, MultiplexerDefaultCase]]

        if isinstance(case_spec, str):
            applicable_cases = [x for x in self.cases if x.short_name == case_spec]
            if not applicable_cases and self.default_case:
                applicable_cases.append(self.default_case)
            if len(applicable_cases) == 0:
                raise EncodeError(
                    f"Multiplexer {self.short_name} does not know any case called {case_spec}")

            odxassert(len(applicable_cases) == 1)
            mux_case = applicable_cases[0]
            if isinstance(mux_case, MultiplexerCase):
                key_value, _ = self._get_case_limits(mux_case)
            else:
                key_value = 0
        elif isinstance(case_spec, int):
            applicable_cases = []
            for x in self.cases:
                lower, upper = cast(Tuple[int, int], self._get_case_limits(x))
                if lower <= case_spec and case_spec <= upper:
                    applicable_cases.append(x)

            if len(applicable_cases) == 0:
                if self.default_case is None:
                    raise EncodeError(
                        f"Multiplexer {self.short_name} does not know any case called {case_spec}")
                mux_case = self.default_case
                key_value = case_spec
            else:
                mux_case = applicable_cases[0]
                key_value = case_spec
        elif isinstance(case_spec, MultiplexerCase):
            mux_case = case_spec
            key_value, _ = self._get_case_limits(mux_case)
        elif case_spec is None:
            if self.default_case is None:
                raise EncodeError(f"Multiplexer {self.short_name} does not define a default case")
            key_value = 0
        else:
            raise EncodeError(f"Illegal case specification '{case_spec}' for "
                              f"multiplexer {self.short_name}")

        # the byte position of the switch key is relative to
        # the multiplexer's position
        encode_state.cursor_byte_position = encode_state.origin_byte_position + self.switch_key.byte_position
        encode_state.cursor_bit_position = self.switch_key.bit_position or 0
        self.switch_key.dop.encode_into_pdu(physical_value=key_value, encode_state=encode_state)
        encode_state.cursor_bit_position = 0

        if mux_case.structure is not None:
            # the byte position of the content is specified by the
            # BYTE-POSITION attribute of the multiplexer
            encode_state.cursor_byte_position = encode_state.origin_byte_position + self.byte_position
            mux_case.structure.encode_into_pdu(physical_value=case_value, encode_state=encode_state)

        encode_state.origin_byte_position = orig_origin

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        orig_origin = decode_state.origin_byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        # Decode the switch key. Its BYTE-POSITION is relative to the
        # that of the multiplexer.
        if self.switch_key.byte_position is not None:
            decode_state.cursor_byte_position = decode_state.origin_byte_position + self.switch_key.byte_position
        decode_state.cursor_bit_position = self.switch_key.bit_position or 0
        key_value = self.switch_key.dop.decode_from_pdu(decode_state)
        decode_state.cursor_bit_position = 0

        if not isinstance(key_value, int):
            odxraise(f"Multiplexer keys must be integers (is '{type(key_value).__name__}'"
                     f" for multiplexer '{self.short_name}')")

        # "If a matching CASE is found, the referenced STRUCTURE is
        # analyzed at the BYTE-POSITION (child element of MUX)
        # relatively to the byte position of the MUX."
        decode_state.cursor_byte_position = decode_state.origin_byte_position + self.byte_position

        applicable_case: Optional[Union[MultiplexerCase, MultiplexerDefaultCase]] = None
        for mux_case in self.cases:
            lower, upper = self._get_case_limits(mux_case)
            if lower <= key_value and key_value <= upper:  # type: ignore[operator]
                applicable_case = mux_case
                break

        if applicable_case is None:
            applicable_case = self.default_case

        if applicable_case is None:
            odxraise(
                f"Cannot find an applicable case for value {key_value} in "
                f"multiplexer {self.short_name}", DecodeError)
            decode_state.origin_byte_position = orig_origin
            return (None, None)

        if applicable_case.structure is not None:
            case_value = applicable_case.structure.decode_from_pdu(decode_state)
        else:
            case_value = {}

        result = (applicable_case.short_name, case_value)

        decode_state.origin_byte_position = orig_origin

        return result

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        odxlinks.update(self.switch_key._build_odxlinks())
        if self.default_case is not None:
            odxlinks.update(self.default_case._build_odxlinks())

        return odxlinks

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self.switch_key._resolve_odxlinks(odxlinks)
        if self.default_case is not None:
            self.default_case._resolve_odxlinks(odxlinks)

        for mux_case in self.cases:
            mux_case._mux_case_resolve_odxlinks(
                odxlinks, key_physical_type=self.switch_key.dop.physical_type.base_data_type)

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        self.switch_key._resolve_snrefs(context)
        if self.default_case is not None:
            self.default_case._resolve_snrefs(context)

        for mux_case in self.cases:
            mux_case._resolve_snrefs(context)
