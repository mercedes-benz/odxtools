# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxraise, odxrequire
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkRef
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType
from .rowfragment import RowFragment

if TYPE_CHECKING:
    from ..tablerow import TableRow


@dataclass(kw_only=True)
class TableEntryParameter(Parameter):
    target: RowFragment
    table_row_ref: OdxLinkRef

    @property
    @override
    def parameter_type(self) -> ParameterType:
        return "TABLE-ENTRY"

    @property
    @override
    def is_required(self) -> bool:
        raise NotImplementedError("TableEntryParameter.is_required is not implemented yet.")

    @property
    @override
    def is_settable(self) -> bool:
        raise NotImplementedError("TableEntryParameter.is_settable is not implemented yet.")

    @property
    def table_row(self) -> "TableRow":
        return self._table_row

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "TableEntryParameter":
        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, context))

        target_str = odxrequire(et_element.findtext("TARGET"))
        try:
            target = RowFragment(target_str)
        except ValueError:
            odxraise(f"Encountered unknown target '{target_str}'")
            target = cast(RowFragment, None)
        table_row_ref = odxrequire(OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), context))

        return TableEntryParameter(target=target, table_row_ref=table_row_ref, **kwargs)

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if TYPE_CHECKING:
            self._table_row = odxlinks.resolve(self.table_row_ref, TableRow)
        else:
            self._table_row = odxlinks.resolve(self.table_row_ref)

    @override
    def _encode_positioned_into_pdu(self, physical_value: ParameterValue | None,
                                    encode_state: EncodeState) -> None:
        raise NotImplementedError("Encoding a TableEntryParameter is not implemented yet.")

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        raise NotImplementedError("Decoding a TableEntryParameter is not implemented yet.")
