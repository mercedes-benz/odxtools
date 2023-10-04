# SPDX-License-Identifier: MIT
import warnings
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, cast

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import EncodeError, OdxWarning, odxraise
from ..odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..odxtypes import ParameterValue
from .parameter import Parameter, ParameterType
from .tablekeyparameter import TableKeyParameter

if TYPE_CHECKING:
    from ..diaglayer import DiagLayer


@dataclass
class TableStructParameter(Parameter):

    table_key_ref: Optional[OdxLinkRef]
    table_key_snref: Optional[str]

    def __post_init__(self) -> None:
        if self.table_key_ref is None and self.table_key_snref is None:
            odxraise("Either table_key_ref or table_key_snref must be defined.")

    @property
    def parameter_type(self) -> ParameterType:
        return "TABLE-STRUCT"

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.table_key_ref is not None:
            self._table_key = odxlinks.resolve(self.table_key_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.table_key_snref is not None:
            warnings.warn(
                "Table keys cannot yet be defined using SNREFs"
                " in TableStructParameters.",
                OdxWarning,
                stacklevel=1)

    @property
    def table_key(self) -> TableKeyParameter:
        return self._table_key

    @property
    def is_required(self) -> bool:
        return True

    @property
    def is_settable(self) -> bool:
        return True

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        physical_value = encode_state.parameter_values.get(self.short_name)

        if not isinstance(physical_value, tuple) or \
           len(physical_value) != 2 or \
           not isinstance(physical_value[0], str):
            raise EncodeError(f"The physical value of TableStructParameter 'self.short_name' "
                              f"must be a tuple with  the short name of the selected table "
                              f"row as the first element and the physical value for the "
                              f"row's structure or DOP as the second.")

        tr_short_name = physical_value[0]

        # make sure that the same table row is selected for all
        # TABLE-STRUCT parameters that are using the same key
        tk_short_name = self.table_key.short_name
        tk_value = encode_state.parameter_values.get(tk_short_name)
        if tk_value is None:
            # no value for the key has been set yet. Set it to the
            # value which we are using right now
            encode_state.parameter_values[tk_short_name] = tr_short_name
        elif tk_value != tr_short_name:
            raise EncodeError(f"Cannot determine a unique value for table key '{tk_short_name}':  "
                              f"Requested are '{tk_value}' and '{tr_short_name}'")

        # deal with the static case (i.e., the table row is selected
        # by the table key object itself)
        if self.table_key.table_row is not None and \
           self.table_key.table_row.short_name != tr_short_name:
            raise EncodeError(f"The selected table row for the {self.short_name} "
                              f"parameter must be '{self.table_key.table_row.short_name}' "
                              f"(is: '{tr_short_name}')")

        # encode the user specified value using the structure (or DOP)
        # of the selected table row
        table = self.table_key.table
        candidate_trs = [tr for tr in table.table_rows if tr.short_name == tr_short_name]
        if len(candidate_trs) != 1:
            raise EncodeError(f"Could not uniquely resolve a table row named "
                              f"'{tr_short_name}' in table '{table.short_name}' ")
        tr = candidate_trs[0]
        tr_value = physical_value[1]

        bit_position = self.bit_position or 0
        if tr.structure is not None:
            # the selected table row references a structure
            if not isinstance(tr_value, dict):
                raise EncodeError(f"The value of `{tr_short_name}` must "
                                  f"be a key-value dictionary.")

            inner_encode_state = EncodeState(
                coded_message=b'',
                parameter_values=tr_value,
                triggering_request=encode_state.triggering_request)

            return tr.structure.convert_physical_to_bytes(
                tr_value, inner_encode_state, bit_position=bit_position)

        # if the table row does not reference a structure, it must
        # point to a DOP!
        if tr.dop is None:
            odxraise()

        return tr.dop.convert_physical_to_bytes(
            tr_value, encode_state=encode_state, bit_position=bit_position)

    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        return super().encode_into_pdu(encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[ParameterValue, int]:
        if self.byte_position is not None and self.byte_position != decode_state.cursor_position:
            next_pos = self.byte_position if self.byte_position is not None else 0
            decode_state = copy(decode_state)
            decode_state.cursor_position = next_pos

        # find the selected table row
        key_name = self.table_key.short_name

        table = self.table_key.table
        tr_short_name = decode_state.parameter_values[key_name]
        candidate_trs = [tr for tr in table.table_rows if tr.short_name == tr_short_name]
        if len(candidate_trs) != 1:
            raise EncodeError(f"Could not uniquely resolve a table row named "
                              f"'{str(tr_short_name)}' in table '{str(table.short_name)}' ")
        table_row = candidate_trs[0]

        # Use DOP or structure to decode the value
        if table_row.dop is not None:
            dop = table_row.dop
            val, i = dop.convert_bytes_to_physical(decode_state)
            return (table_row.short_name, val), i
        elif table_row.structure is not None:
            structure = table_row.structure
            val, i = structure.convert_bytes_to_physical(decode_state)
            return (table_row.short_name, val), i
        else:
            # the table row associated with the key neither defines a
            # DOP not a structure -> ignore it
            return (table_row.short_name, cast(int, None)), decode_state.cursor_position
