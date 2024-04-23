# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional
from xml.etree import ElementTree

from typing_extensions import override

from ..decodestate import DecodeState
from ..encodestate import EncodeState
from ..exceptions import odxrequire
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkRef
from ..odxtypes import ParameterValue
from ..utils import dataclass_fields_asdict
from .parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from ..tablerow import TableRow


@dataclass
class TableEntryParameter(Parameter):
    target: str
    table_row_ref: OdxLinkRef

    @staticmethod
    @override
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "TableEntryParameter":

        kwargs = dataclass_fields_asdict(Parameter.from_et(et_element, doc_frags))

        target = odxrequire(et_element.findtext("TARGET"))
        table_row_ref = odxrequire(OdxLinkRef.from_et(et_element.find("TABLE-ROW-REF"), doc_frags))

        return TableEntryParameter(target=target, table_row_ref=table_row_ref, **kwargs)

    @override
    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        if TYPE_CHECKING:
            self._table_row = odxlinks.resolve(self.table_row_ref, TableRow)
        else:
            self._table_row = odxlinks.resolve(self.table_row_ref)

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

    @override
    def _encode_positioned_into_pdu(self, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
        raise NotImplementedError("Encoding a TableEntryParameter is not implemented yet.")

    @property
    def table_row(self) -> "TableRow":
        return self._table_row

    @override
    def _decode_positioned_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        raise NotImplementedError("Decoding a TableEntryParameter is not implemented yet.")
