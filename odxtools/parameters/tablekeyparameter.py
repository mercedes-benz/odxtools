# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from typing_extensions import final, override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from ..odxtypes import ParameterValue
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from ..table import Table
    from ..tablerow import TableRow


@dataclass
class TableKeyParameter(Parameter):

    odx_id: OdxLinkId
    table_ref: Optional[OdxLinkRef]
    table_snref: Optional[str]
    table_row_snref: Optional[str]
    table_row_ref: Optional[OdxLinkRef]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "TableKeyParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))

        table_ref = OdxLinkRef.from_et(et_element.find("TABLE-REF"), doc_frags)
        table_snref = None
        if (table_snref_elem := et_element.find("TABLE-SNREF")) is not None:
            table_snref = odxrequire(table_snref_elem.get("SHORT-NAME"))

        table_row_ref = OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags)
        table_row_snref = None
        if (table_row_snref_elem := et_element.find("TABLE-ROW-SNREF")) is not None:
            table_row_snref = odxrequire(table_row_snref_elem.get("SHORT-NAME"))

        return TableKeyParameter(
            odx_id=odx_id,
            table_ref=table_ref,
            table_snref=table_snref,
            table_row_ref=table_row_ref,
            table_row_snref=table_row_snref,
            **kwargs)

    def __post_init__(self) -> None:
        self._table: Table
        self._table_row: Optional[TableRow] = None
        if self.table_ref is None and self.table_snref is None and \
           self.table_row_ref is None and self.table_row_snref is None:
            odxraise("Either a table or a table row must be defined.")

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "TABLE-KEY"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        result[self.odx_id] = self

        return result

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        # Either table_ref or table_row_ref will be defined
        if self.table_ref:
            if TYPE_CHECKING:
                self._table = odxlinks.resolve(self.table_ref, Table)
            else:
                self._table = odxlinks.resolve(self.table_ref)

        if self.table_row_ref:
            if TYPE_CHECKING:
                self._table_row = odxlinks.resolve(self.table_row_ref, TableRow)
            else:
                self._table_row = odxlinks.resolve(self.table_row_ref)
            self._table = self._table_row.table

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        if self.table_snref is not None:
            tables = odxrequire(context.diag_layer).diag_data_dictionary_spec.tables
            if TYPE_CHECKING:
                self._table = resolve_snref(self.table_snref, tables, Table)
            else:
                self._table = resolve_snref(self.table_snref, tables)
        if self.table_row_snref is not None:
            # make sure that we know the table to which the table row
            # SNREF is relative to.
            table = odxrequire(
                self._table, "If a table row is referenced via short name, a table must "
                "be referenced as well")
            if TYPE_CHECKING:
                self._table_row = resolve_snref(self.table_row_snref, table.table_rows, TableRow)
            else:
                self._table_row = resolve_snref(self.table_row_snref, table.table_rows)

    @property
    def table(self) -> "Table":
        if self._table is not None:
            return self._table
        if self._table_row is not None:
            return self._table_row.table
        odxraise(f'Could not resolve the table of {self.short_name}')

    @property
    def table_row(self) -> Optional["TableRow"]:
        return self._table_row

    @property
    @override
    def is_required(self) -> bool:
        # TABLE-KEY parameters can be implicitly determined from the
        # corresponding TABLE-STRUCT
        return False

    @property
    @override
    def is_settable(self) -> bool:
        return True

    @override
    @final
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        # if you get this exception, you ought to use
        # `.encode_placeholder_into_pdu()` followed by (after the
        # value of the table key has been determined)
        # `.encode_value_into_pdu()`.
        raise RuntimeError("_encode_positioned_into_pdu() cannot be called for table keys.")

    def encode_placeholder_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:

        if physical_value is not None:
            key_dop = self.table.key_dop
            if key_dop is None:
                odxraise(
                    f"Table '{self.table.short_name}' does not define "
                    f"a KEY-DOP, but is used by TABLE-KEY parameter "
                    f"'{self.short_name}'", EncodeError)
                return

            if not isinstance(physical_value, str):
                odxraise(f"Invalid type for for table key '{self.short_name}' specified. "
                         f"(expect name of table row.)")

            tkv = encode_state.table_keys.get(self.short_name)
            if tkv is not None and tkv != physical_value:
                odxraise(f"Got conflicting values for table key {self.short_name}: "
                         f"{tkv} and {physical_value!r}")

            encode_state.table_keys[self.short_name] = physical_value

        pos = encode_state.cursor_byte_position
        if self.byte_position is not None:
            pos = encode_state.origin_byte_position + self.byte_position
        encode_state.key_pos[self.short_name] = pos
        encode_state.cursor_byte_position = pos
        encode_state.cursor_bit_position = self.bit_position or 0

        key_dop = self.table.key_dop
        if key_dop is None:
            odxraise(f"No KEY-DOP specified for table {self.table.short_name}")
            return

        sz = key_dop.get_static_bit_length()
        if sz is None:
            odxraise("The DOP of table key {self.short_name} must exhibit a fixed size.",
                     EncodeError)
            return

        # emplace a value of zero into the encode state, but pretend the bits not to be used
        n = sz + encode_state.cursor_bit_position
        tmp_val = b'\x00' * ((n + 7) // 8)
        encode_state.emplace_bytes(tmp_val, obj_used_mask=tmp_val)

        encode_state.cursor_bit_position = 0

    def encode_value_into_pdu(self, encode_state: EncodeState) -> None:

        key_dop = self.table.key_dop
        if key_dop is None:
            odxraise(
                f"Table '{self.table.short_name}' does not define "
                f"a KEY-DOP, but is used by TABLE-KEY parameter "
                f"'{self.short_name}'", EncodeError)
            return

        if self.short_name not in encode_state.table_keys:
            odxraise(f"Table key {self.short_name} has not been defined before "
                     f"it is required.", EncodeError)
            return
        else:
            tr_short_name = encode_state.table_keys[self.short_name]

        # We need to encode the table key using the associated DOP into the PDU.
        tr_candidates = [x for x in self.table.table_rows if x.short_name == tr_short_name]
        if len(tr_candidates) == 0:
            odxraise(f"No table row with short name '{tr_short_name}' found", EncodeError)
            return
        elif len(tr_candidates) > 1:
            odxraise(f"Multiple rows exhibiting short name '{tr_short_name}'", EncodeError)
        tr = tr_candidates[0]

        encode_state.cursor_byte_position = encode_state.key_pos[self.short_name]
        encode_state.cursor_bit_position = self.bit_position or 0

        key_dop.encode_into_pdu(encode_state=encode_state, physical_value=odxrequire(tr.key))

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        if self.table_row is not None:
            # the table row to be used is statically specified -> no
            # need to decode anything!
            phys_val = self.table_row.short_name
        else:
            # Use DOP to decode
            key_dop = odxrequire(self.table.key_dop)
            key_dop_val = key_dop.decode_from_pdu(decode_state)

            table_row_candidates = [x for x in self.table.table_rows if x.key == key_dop_val]
            if len(table_row_candidates) == 0:
                raise DecodeError(f"No table row exhibiting the key '{str(key_dop_val)}' found")
            elif len(table_row_candidates) > 1:
                raise DecodeError(
                    f"Multiple rows exhibiting key '{str(key_dop_val)}' found in table")
            table_row = table_row_candidates[0]
            phys_val = table_row.short_name

            # update the decode_state's table key
            decode_state.table_keys[self.short_name] = table_row

        return phys_val
