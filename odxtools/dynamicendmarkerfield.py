# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from xml.etree import ElementTree

from typing_extensions import override

from .dataobjectproperty import DataObjectProperty
from .decodestate import DecodeState
from .dynenddopref import DynEndDopRef
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .field import Field
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import AtomicOdxType, ParameterValue
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class DynamicEndmarkerField(Field):
    """Array of a structure with variable length determined by a termination sequence"""

    dyn_end_dop_ref: DynEndDopRef

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DynamicEndmarkerField":
        kwargs = dataclass_fields_asdict(Field.from_et(et_element, doc_frags))

        # ODX 2.0 uses DATA-OBJECT-PROP-REF
        # ODX 2.2 uses DYN-END-DOP-REF
        dop_ref = et_element.find("DYN-END-DOP-REF") or et_element.find("DATA-OBJECT-PROP-REF")
        dyn_end_dop_ref = DynEndDopRef.from_et(odxrequire(dop_ref), doc_frags)

        return DynamicEndmarkerField(dyn_end_dop_ref=dyn_end_dop_ref, **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()
        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self._dyn_end_dop = odxlinks.resolve(self.dyn_end_dop_ref, DataObjectProperty)

        tv_string = self.dyn_end_dop_ref.termination_value_raw
        tv_physical = self._dyn_end_dop.diag_coded_type.base_data_type.from_string(tv_string)

        self._termination_value = tv_physical

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

    @property
    def dyn_end_dop(self) -> DataObjectProperty:
        return self._dyn_end_dop

    @property
    def termination_value(self) -> AtomicOdxType:
        return self._termination_value

    @override
    def encode_into_pdu(self, physical_value: ParameterValue, encode_state: EncodeState) -> None:

        odxassert(encode_state.cursor_bit_position == 0,
                  "No bit position can be specified for dynamic endmarker fields!")
        if not isinstance(physical_value, Sequence):
            odxraise(
                f"Expected a sequence of values for dynamic endmarker field {self.short_name}, "
                f"got {type(physical_value).__name__}", EncodeError)
            return

        orig_is_end_of_pdu = encode_state.is_end_of_pdu
        encode_state.is_end_of_pdu = False
        for i, item in enumerate(physical_value):
            if i == len(physical_value) - 1:
                encode_state.is_end_of_pdu = orig_is_end_of_pdu

            self.structure.encode_into_pdu(item, encode_state)
        encode_state.is_end_of_pdu = orig_is_end_of_pdu

        if not encode_state.is_end_of_pdu:
            # only add an endmarker if we are not at the end of the
            # PDU. note that since section 7.3.6.10.5 of the MCD-2
            # specification states that the data used by the endmarker
            # ought to be considered to be not consumed (why?!), we
            # need to keep the cursor where it is before adding the
            # endmarker. (we still consider its bits to be used
            # "used", in order to produce a warning if it is attempted
            # to be overridden.)
            tmp_cursor = encode_state.cursor_byte_position
            self.dyn_end_dop.encode_into_pdu(self.termination_value, encode_state)
            encode_state.cursor_byte_position = tmp_cursor

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        odxassert(decode_state.cursor_bit_position == 0,
                  "No bit position can be specified for dynamic endmarker fields!")

        orig_origin = decode_state.origin_byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        result: List[ParameterValue] = []
        while True:
            # check if we're at the end of the PDU
            if decode_state.cursor_byte_position == len(decode_state.coded_message):
                break

            # check if the cursor currently points to a termination
            # value
            tmp_cursor = decode_state.cursor_byte_position
            try:
                tv_candidate = self.dyn_end_dop.decode_from_pdu(decode_state)
                if tv_candidate == self.termination_value:
                    # note that section 7.3.6.10.5 of the MCD-2
                    # specification states that the bytes occupied by
                    # the endmarker ought to be considered to be not
                    # consumed (why?!), i.e., we need to keep the
                    # cursor where it is before adding the
                    # endmarker. (we still consider its to be used
                    # "used", though.)
                    decode_state.cursor_byte_position = tmp_cursor
                    break
            except DecodeError:
                pass
            decode_state.cursor_byte_position = tmp_cursor

            result.append(self.structure.decode_from_pdu(decode_state))

        decode_state.origin_byte_position = orig_origin

        return result
