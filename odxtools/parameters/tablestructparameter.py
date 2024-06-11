# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import DecodeError, EncodeError, odxraise, odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from ..odxtypes import ParameterValue
from ..snrefcontext import SnRefContext
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType
from .tablekeyparameter import TableKeyParameter


@dataclass
class TableStructParameter(Parameter):

    table_key_ref: Optional[OdxLinkRef]
    table_key_snref: Optional[str]

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "TableStructParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        table_key_ref = OdxLinkRef.from_et(et_element.find("TABLE-KEY-REF"), doc_frags)
        table_key_snref = None
        if (table_key_snref_elem := et_element.find("TABLE-KEY-SNREF")) is not None:
            table_key_snref = odxrequire(table_key_snref_elem.get("SHORT-NAME"))

        return TableStructParameter(
            table_key_ref=table_key_ref, table_key_snref=table_key_snref, **kwargs)

    def __post_init__(self) -> None:
        if self.table_key_ref is None and self.table_key_snref is None:
            odxraise("Either table_key_ref or table_key_snref must be defined.")

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "TABLE-STRUCT"

    @override
    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return super()._build_odxlinks()

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if self.table_key_ref is not None:
            self._table_key = odxlinks.resolve(self.table_key_ref, TableKeyParameter)

    @override
    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        if self.table_key_snref is not None:
            self._table_key = resolve_snref(self.table_key_snref, odxrequire(context.parameters),
                                            TableKeyParameter)

    @property
    def table_key(self) -> TableKeyParameter:
        return self._table_key

    @property
    @override
    def is_required(self) -> bool:
        return True

    @property
    @override
    def is_settable(self) -> bool:
        return True

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:

        if not isinstance(physical_value, (tuple, list)) or \
           len(physical_value) != 2 or \
           not isinstance(physical_value[0], str):
            odxraise(
                f"The physical value of TableStructParameter 'self.short_name' "
                f"must be a tuple containing the short name of the selected table "
                f"row as the first element and the physical value for the "
                f"row's structure or DOP as the second.", EncodeError)

        tr_short_name = physical_value[0]

        # make sure that the same table row is selected for all
        # TABLE-STRUCT parameters that are using the same key
        tk_short_name = self.table_key.short_name
        tk_value = encode_state.table_keys.get(tk_short_name)
        if tk_value is None:
            # no value for the key has been set yet. Set it to the
            # value which we are using right now
            encode_state.table_keys[tk_short_name] = tr_short_name
        elif tk_value != tr_short_name:
            odxraise(
                f"Cannot determine a unique value for table key '{tk_short_name}':  "
                f"Requested are '{tk_value}' and '{tr_short_name}'", EncodeError)
            return

        # deal with the static case (i.e., the table row is selected
        # by the table key object itself)
        if self.table_key.table_row is not None:
            if tr_short_name is not None and self.table_key.table_row.short_name != tr_short_name:
                odxraise(
                    f"The selected table row for the {self.short_name} "
                    f"parameter must be '{self.table_key.table_row.short_name}' "
                    f"instead of '{tr_short_name}'", EncodeError)
                return

            tr_short_name = self.table_key.table_row.short_name

        # encode the user specified value using the structure (or DOP)
        # of the selected table row
        table = self.table_key.table
        candidate_trs = [tr for tr in table.table_rows if tr.short_name == tr_short_name]
        if len(candidate_trs) == 0:
            odxraise(
                f"Could not find a table row named "
                f"'{tr_short_name}' in table '{table.short_name}'", EncodeError)
            return
        elif len(candidate_trs) > 1:
            odxraise(
                f"Found multiple table rows named "
                f"'{tr_short_name}' in table '{table.short_name}'", EncodeError)

        tr = candidate_trs[0]
        tr_value = physical_value[1]

        if tr.structure is not None:
            # the selected table row references a structure
            tr.structure.encode_into_pdu(tr_value, encode_state)
            return

        # if the table row does not reference a structure, it must
        # point to a DOP!
        if tr.dop is None:
            odxraise(f"Neither a structure nor a DOP has been defined for table row"
                     f"'{tr.short_name}'")
            return

        tr.dop.encode_into_pdu(tr_value, encode_state)

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        # find the selected table row
        key_name = self.table_key.short_name

        decode_state.table_keys[key_name]
        table_row = decode_state.table_keys.get(key_name)
        if table_row is None:
            odxraise(
                f"No table key '{key_name}' found when decoding "
                f"table struct parameter '{str(self.short_name)}'", DecodeError)
            dummy_val = cast(str, None), cast(int, None)
            return dummy_val

        # Use DOP or structure to decode the value
        if table_row.dop is not None:
            dop = table_row.dop
            val = dop.decode_from_pdu(decode_state)
            return (table_row.short_name, val)
        elif table_row.structure is not None:
            val = table_row.structure.decode_from_pdu(decode_state)
            return (table_row.short_name, val)
        else:
            # the table row associated with the key neither defines a
            # DOP nor a structure -> ignore it
            return (table_row.short_name, cast(int, None))
