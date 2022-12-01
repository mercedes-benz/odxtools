# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .utils import read_description_from_odx
from .odxlink import OdxLinkId, OdxDocFragment, OdxLinkDatabase

@dataclass()
class State:
    """
    Corresponds to STATE.
    """
    odx_id: OdxLinkId
    short_name: str
    long_name: Optional[str] = None
    description: Optional[str] = None

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return { self.odx_id: self }

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        pass

def read_state_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    short_name = et_element.findtext("SHORT-NAME")
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None

    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    return State(odx_id=odx_id,
                 short_name=short_name,
                 long_name=long_name,
                 description=description)
