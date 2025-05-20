# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .dopbase import DopBase
from .element import NamedElement
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class ConfigItem(NamedElement):
    """This class represents a CONFIG-ITEM.

    CONFIG-ITEM is the base class for CONFIG-ID-ITEM, DATA-ID-ITEM,
    OPTION-ITEM, and SYSTEM-ITEM.
    """
    byte_position: int | None = None
    bit_position: int | None = None

    # according to the spec exactly one of the following two
    # attributes is not None...x
    data_object_prop_ref: OdxLinkRef | None = None
    data_object_prop_snref: str | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    @property
    def data_object_prop(self) -> DopBase:
        return self._data_object_prop

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ConfigItem":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        byte_position = None
        if (byte_pos_elem := et_element.findtext("BYTE-POSITION")) is not None:
            byte_position = int(byte_pos_elem)

        bit_position = None
        if (bit_pos_elem := et_element.findtext("BIT-POSITION")) is not None:
            bit_position = int(bit_pos_elem)

        data_object_prop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), context)
        data_object_prop_snref = None
        if (data_object_prop_snref_elem := et_element.find("DATA-OBJECT-PROP-SNREF")) is not None:
            data_object_prop_snref = odxrequire(
                data_object_prop_snref_elem.attrib.get("SHORT-NAME"))
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        return ConfigItem(
            byte_position=byte_position,
            bit_position=bit_position,
            data_object_prop_ref=data_object_prop_ref,
            data_object_prop_snref=data_object_prop_snref,
            sdgs=sdgs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.data_object_prop_ref is not None:
            self._data_object_prop = odxlinks.resolve(self.data_object_prop_ref, DopBase)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.data_object_prop_snref is not None:
            ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec
            self._data_object_prop = resolve_snref(self.data_object_prop_snref,
                                                   ddds.all_data_object_properties, DopBase)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
