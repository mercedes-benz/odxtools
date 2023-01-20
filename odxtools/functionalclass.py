# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .utils import create_description_from_et


@dataclass
class FunctionalClass:
    """
    Corresponds to FUNCT-CLASS.
    """

    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str]
    description: Optional[str]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]):
        short_name = et_element.findtext("SHORT-NAME")
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None

        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))

        return FunctionalClass(
            odx_id=odx_id, short_name=short_name, long_name=long_name, description=description)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        pass
