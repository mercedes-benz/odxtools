# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError
from ..odxlink import OdxLinkDatabase, OdxLinkId
from ..odxtypes import AtomicOdxType
from .parameterbase import Parameter

if TYPE_CHECKING:
    from ..table import Table
    from ..tablerow import TableRow
    from ..diaglayer import DiagLayer


class TableKeyParameter(Parameter):

    def __init__(self, *, odx_id, table_ref, table_snref, table_row_snref, table_row_ref, **kwargs):
        super().__init__(parameter_type="TABLE-KEY", **kwargs)
        self.odx_id = odx_id
        self.table_ref = table_ref
        self.table_row_ref = table_row_ref
        self.table_snref = table_snref
        self.table_row_snref = table_row_snref

        if self.table_ref is None and self.table_snref is None and \
           self.table_row_ref is None and self.table_row_snref is None:
            raise ValueError("Either a table or a table row must be defined.")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.table_ref:
            if TYPE_CHECKING:
                self._table = odxlinks.resolve(self.table_ref, Table)
            else:
                self._table = odxlinks.resolve(self.table_ref)

        self._table_row: Optional[TableRow] = None
        if self.table_row_ref:
            if TYPE_CHECKING:
                self._table_row = odxlinks.resolve(self.table_row_ref, TableRow)
            else:
                self._table_row = odxlinks.resolve(self.table_row_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        super()._resolve_snrefs(diag_layer)

        if self.table_snref:
            ddd_spec = diag_layer.diag_data_dictionary_spec
            self._table = ddd_spec.tables[self.table_snref]
        if self.table_row_snref:
            # make sure that we know the table to which the table row
            # SNREF is relative to.
            assert self._table is not None, "If a table-row short name " \
                "reference is defined, a table must also be specified."
            self._table_row = self._table.table_rows[self.table_row_snref]

    @property
    def table(self) -> "Table":
        return self._table

    @property
    def table_row(self) -> Optional["TableRow"]:
        return self._table_row

    def is_required(self):
        return self._table_row is None

    def is_optional(self):
        return not self.is_required

    def get_coded_value(self, physical_value=None) -> Any:
        key_dop = self.table.key_dop
        if key_dop is None:
            raise EncodeError(f"Table '{self.table.short_name}' does not define "
                              f"a KEY-DOP, but is used in TABLE-KEY parameter "
                              f"'{self.short_name}'")
        return key_dop.convert_physical_to_internal(physical_value)

    def get_coded_value_as_bytes(self, encode_state: EncodeState) -> bytes:
        tr_short_name = encode_state.parameter_values.get(self.short_name)

        if tr_short_name is None:
            # the table key has not been defined explicitly yet, but
            # it is most likely implicitly defined by the associated
            # TABLE-STRUCT parameters. Use all-zeros as a standin for
            # the real data...
            key_dop = self.table.key_dop
            if key_dop is None:
                raise EncodeError(f"Table '{self.table.short_name}' does not define "
                                  f"a KEY-DOP, but is used in TABLE-KEY parameter "
                                  f"'{self.short_name}'")

            byte_pos = len(encode_state.coded_message
                          ) if self.byte_position is not None else self.byte_position
            byte_len = (key_dop.bit_length + 7) // 8
            if self.bit_position is not None and self.bit_position > 0:
                byte_len += 1

            return bytes([0] * byte_len)

        # the table key is known. We need to encode the associated DOP
        # into the PDU.
        tr_candidates = [x for x in self.table.table_rows if x.short_name == tr_short_name]
        if len(tr_candidates) == 0:
            raise EncodeError(f"No table row with short name '{tr_short_name}' found")
        elif len(tr_candidates) > 1:
            raise EncodeError(f"Multiple rows exhibiting short name '{tr_short_name}'")
        tr = tr_candidates[0]

        key_dop = self.table.key_dop
        if key_dop is None:
            raise EncodeError(f"Table '{self.table.short_name}' does not define "
                              f"a KEY-DOP, but is used in TABLE-KEY parameter "
                              f"'{self.short_name}'")
        bit_position = 0 if self.bit_position is None else self.bit_position
        return key_dop.convert_physical_to_bytes(tr.key, encode_state, bit_position=bit_position)

    def encode_into_pdu(self, encode_state: EncodeState) -> bytes:
        tr_short_name = encode_state.parameter_values.get(self.short_name)

        return super().encode_into_pdu(encode_state)

    def decode_from_pdu(self, decode_state: DecodeState) -> Tuple[Any, int]:
        if self.byte_position is not None and self.byte_position != decode_state.next_byte_position:
            next_byte_position = self.byte_position

        # update the decode_state's table key
        if self.table_row is not None:
            # the table row to be used is statically specified -> no
            # need to decode anything!
            phys_val = self.table_row.short_name
            next_byte_position = decode_state.next_byte_position
        else:
            # Use DOP to decode
            key_dop = self.table.key_dop
            assert key_dop is not None
            bit_position_int = self.bit_position if self.bit_position is not None else 0
            key_dop_val, next_byte_position = key_dop.convert_bytes_to_physical(
                decode_state, bit_position=bit_position_int)

            table_row_candidates = [x for x in self.table.table_rows if x.key == key_dop_val]
            if len(table_row_candidates) == 0:
                raise DecodeError(f"No table row exhibiting the key '{str(key_dop_val)}' found")
            elif len(table_row_candidates) > 1:
                raise DecodeError(
                    f"Multiple rows exhibiting key '{str(key_dop_val)}' found in table")
            phys_val = table_row_candidates[0].short_name

        return phys_val, next_byte_position
