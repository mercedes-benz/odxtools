# SPDX-License-Identifier: MIT
# Copyright (c) 2023 MBition GmbH

from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from odxtools.odxlink import OdxDocFragment
from odxtools.utils import is_short_name, is_short_name_path


class MatchingParameter:
    """According to ISO 22901, a MatchingParameter contains a string value identifying
    the active ECU variant. Moreover, it references a DIAG-COMM via snref and one of its
    positiv response's OUT-PARAM-IF via snref or snpathref.

    Unlike other parameters defined in the `parameters` package, a MatchingParameter is
    not transferred over the network.
    """

    def __init__(self, *, expected_value: str, diag_comm_snref: str, out_param_if: str):
        # datatype according to ISO 22901-1 Figure 141
        self.expected_value: str = expected_value

        assert is_short_name(diag_comm_snref)  # const-correctness
        self.diag_comm_snref: str = diag_comm_snref

        assert is_short_name_path(out_param_if)  # const-correctness
        self.out_param_if: str = out_param_if

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MatchingParameter":

        expected_value = et_element.findtext("EXPECTED-VALUE")
        assert expected_value is not None

        diag_com_snref_el = et_element.find("DIAG-COMM-SNREF")
        assert diag_com_snref_el is not None
        diag_comm_snref = diag_com_snref_el.get("SHORT-NAME")
        assert diag_comm_snref is not None

        out_param_snref_el = et_element.find("OUT-PARAM-IF-SNREF")
        out_param_snpathref_el = et_element.find("OUT-PARAM-IF-SNPATHREF")
        out_param_if = None
        if out_param_snref_el is not None:
            out_param_if = out_param_snref_el.get("SHORT-NAME")
        elif out_param_snpathref_el is not None:
            out_param_if = out_param_snpathref_el.get("SHORT-NAME-PATH")
        assert out_param_if is not None

        return MatchingParameter(
            expected_value=expected_value,
            diag_comm_snref=diag_comm_snref,
            out_param_if=out_param_if,
        )

    def is_match(self, ident_value: str) -> bool:
        """
        Returns true iff the provided identification value matches this MatchingParameter's
        expected value.
        """
        return self.expected_value == ident_value


@dataclass
class EcuVariantPattern:
    matching_parameters: List[MatchingParameter]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EcuVariantPattern":

        mp_collection_el = et_element.find("MATCHING-PARAMETERS")
        assert mp_collection_el is not None

        matching_params = [
            MatchingParameter.from_et(mp_el, doc_frags)
            for mp_el in mp_collection_el.iterfind("MATCHING-PARAMETER")
        ]

        assert len(matching_params) > 0  # required by ISO 22901-1 Figure 141
        return EcuVariantPattern(matching_params)


def create_ecu_variant_patterns_from_et(et_element: Optional[ElementTree.Element],
                                        doc_frags: List[OdxDocFragment]) -> List[EcuVariantPattern]:

    if et_element is None:
        return []

    return [
        EcuVariantPattern.from_et(evp_elem, doc_frags)
        for evp_elem in et_element.iterfind("ECU-VARIANT-PATTERN")
    ]
