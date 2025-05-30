# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .odxlink import OdxLinkId, OdxDocFragment, OdxLinkDatabase, OdxLinkRef

@dataclass
class PreConditionState:
    """
    Corresponds to PRE-CONDITION-STATE.
    """
    ref: OdxLinkRef
    value: Optional[int]
    in_param_if_snref: Optional[str]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "PreConditionState":
        value = et_element.findtext("VALUE")
        ref = OdxLinkRef.from_et(et_element, doc_frags)
        assert ref is not None

        in_param_if_snref = et_element.findtext("IN-PARAM-IF-SNREF")

        return PreConditionState(ref=ref,
                                 value=value,
                                 in_param_if_snref=in_param_if_snref)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        pass

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        pass
