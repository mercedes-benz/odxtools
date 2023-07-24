# SPDX-License-Identifier: MIT
from copy import copy
from typing import TYPE_CHECKING, Any, Dict, Tuple

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..odxtypes import AtomicOdxType
from .parameterbase import Parameter
from .tablekeyparameter import TableKeyParameter

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


class TableStructParameter(Parameter):

    def __init__(self, *, table_key_ref, table_key_snref, **kwargs):
        super().__init__(parameter_type="TABLE-STRUCT", **kwargs)

        self.table_key_ref = table_key_ref
        self.table_key_snref = table_key_snref
        if self.table_key_ref is None and self.table_key_snref is None:
            raise OdxError("Either table_key_ref or table_key_snref "
                           "must be defined.")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.table_key_ref is not None:
            self._table_key = odxlinks.resolve(self.table_key_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.table_key_snref is not None:
            raise NotImplementedError("Table keys cannot yet defined using SNREFs"
                                      " for TableStructParameters.")

    @property
    def table_key(self) -> TableKeyParameter:
        return self._table_key

    def is_required(self):
        return True

    def is_optional(self):
        return False

    def get_coded_value(self, physical_value=None):
        raise EncodeError("TableStructParameters cannot be converted to "
                          "internal values without a table row.")

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        physical_value = encode_state.parameter_values[self.short_name]
        if not isinstance(physical_value, dict):
            raise EncodeError("The physical values to be encoded must be "
                              "specified using a 'name' -> 'value' dictionary")

        # find the selected table row
        key_name = self.table_key.short_name
        table_row = encode_state.table_keys[key_name]

        # use the referenced structure or DOP to encode the parameter
        if table_row.dop is not None:
            dop = table_row.dop

            bit_position = 0 if self.bit_position is None else self.bit_position
            return dop.convert_physical_to_bytes(
                encode_state.parameter_values[self.short_name],
                encode_state,
                bit_position=bit_position)
        elif table_row.structure is not None:
            structure = table_row.structure

            inner_params = encode_state.parameter_values[self.short_name]
            if not isinstance(inner_params, dict):
                raise EncodeError(f"The sub-parameters for '{self.short_name}' must be "
                                  f"specified using a key->value dictionary")
            return structure.convert_physical_to_bytes(
                inner_params,  # type: ignore [arg-type]
                encode_state)
        else:
            # the table row associated with the key neither defines a
            # DOP not a structure -> ignore it
            return b''

    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        return super().encode_into_pdu(encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[Any, int]:
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            next_pos = self.byte_position if self.byte_position is not None else 0
            decode_state = copy(decode_state)
            decode_state.next_byte_position = next_pos

        # find the selected table row
        key_name = self.table_key.short_name
        table_row = decode_state.table_keys[key_name]

        # Use DOP or structure to decode the value
        if table_row.dop is not None:
            dop = table_row.dop

            return dop.convert_bytes_to_physical(decode_state)
        elif table_row.structure is not None:
            structure = table_row.structure

            return structure.convert_bytes_to_physical(decode_state)

        else:
            # the table row associated with the key neither defines a
            # DOP not a structure -> ignore it
            return None, decode_state.next_byte_position
