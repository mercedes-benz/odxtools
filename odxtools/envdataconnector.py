# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .element import NamedElement
from .environmentdata import EnvironmentData
from .environmentdatadescription import EnvironmentDataDescription
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EnvDataConnector(NamedElement):
    env_data_desc_ref: OdxLinkRef
    env_data_snref: str

    @property
    def env_data_desc(self) -> EnvironmentDataDescription:
        return self._env_data_desc

    @property
    def env_data(self) -> EnvironmentData:
        return self._env_data

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EnvDataConnector":
        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        env_data_desc_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("ENV-DATA-DESC-REF"), context))
        env_data_snref_el = odxrequire(et_element.find("ENV-DATA-SNREF"))
        env_data_snref = odxrequire(env_data_snref_el.get("SHORT-NAME"))

        return EnvDataConnector(
            env_data_desc_ref=env_data_desc_ref, env_data_snref=env_data_snref, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._env_data_desc = odxlinks.resolve(self.env_data_desc_ref, EnvironmentDataDescription)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self._env_data = resolve_snref(self.env_data_snref, self._env_data_desc.env_datas,
                                       EnvironmentData)
