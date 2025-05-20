# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from .datafile import Datafile
from .dataformatselection import DataformatSelection
from .element import NamedElement
from .exceptions import odxraise, odxrequire
from .identvalue import IdentValue
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DataRecord(NamedElement):
    rule: str | None = None
    key: str | None = None
    data_id: IdentValue | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    # at most one of the following two attributes is not None
    datafile: Datafile | None = None
    data: str | None = None

    dataformat: DataformatSelection

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DataRecord":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        rule = et_element.findtext("RULE")
        key = et_element.findtext("KEY")
        data_id = None
        if (did_elem := et_element.find("DATA-ID")) is not None:
            data_id = IdentValue.from_et(did_elem, context)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        datafile = None
        if (df_elem := et_element.find("DATA-FILE")) is not None:
            datafile = Datafile.from_et(df_elem, context)
        data = et_element.findtext("DATA")

        dataformat_str = odxrequire(et_element.attrib.get("DATAFORMAT"))
        try:
            dataformat = DataformatSelection(dataformat_str)
        except ValueError:
            dataformat = cast(DataformatSelection, None)
            odxraise(f"Encountered unknown data format selection '{dataformat_str}'")

        return DataRecord(
            rule=rule,
            key=key,
            data_id=data_id,
            sdgs=sdgs,
            datafile=datafile,
            data=data,
            dataformat=dataformat,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
