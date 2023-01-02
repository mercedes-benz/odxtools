# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from odxtools.odxlink import OdxDocFragment


@dataclass
class MatchingParameter:
    expected_value: int
    diag_comm_snref: str
    out_param_if_snref: str

    @classmethod
    def from_et(cls, et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) \
            -> "MatchingParameter":

        expected_value = et_element.findtext("EXPECTED-VALUE")
        assert expected_value is not None

        diag_com_snref_el = et_element.find("DIAG-COMM-SNREF")
        assert diag_com_snref_el is not None
        diag_comm_snref = diag_com_snref_el.get("SHORT-NAME")
        assert diag_comm_snref is not None

        out_param_snref_el = et_element.find("OUT-PARAM-IF-SNREF")
        assert out_param_snref_el is not None
        out_param_if_snref = out_param_snref_el.get("SHORT-NAME")
        assert out_param_if_snref is not None

        return cls(int(expected_value), diag_comm_snref, out_param_if_snref)

    def is_match(self, ident_value: int) -> bool:
        """
        Returns true iff the provided identification value matches this MatchingParameter's
        expected value.
        """
        return (self.expected_value == ident_value)

@dataclass
class EcuVariantPattern:
    matching_parameters: List[MatchingParameter]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) \
            -> "EcuVariantPattern":

        mp_collection_el = et_element.find("MATCHING-PARAMETERS")
        assert mp_collection_el is not None

        matching_params = []
        for mp_el in mp_collection_el.iterfind("MATCHING-PARAMETER"):
            matching_params.append(MatchingParameter.from_et(mp_el, doc_frags))

        assert len(matching_params) > 0 # required by ISO 22901-1 Figure 141
        return EcuVariantPattern(matching_params)


def read_ecu_variant_patterns_from_odx(et_element: Optional[ElementTree.Element], doc_frags: List[OdxDocFragment]) -> List[EcuVariantPattern]:

    if not et_element:
        return []

    result = []
    for evp_elem in et_element.iterfind("ECU-VARIANT-PATTERN"):
        result.append(EcuVariantPattern.from_et(evp_elem, doc_frags))

    return result