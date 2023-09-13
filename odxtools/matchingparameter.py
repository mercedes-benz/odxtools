# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .exceptions import odxassert, odxraise, odxrequire
from .odxlink import OdxDocFragment
from .utils import is_short_name, is_short_name_path


@dataclass
class MatchingParameter:
    """According to ISO 22901, a MatchingParameter contains a string value identifying
    the active ECU variant. Moreover, it references a DIAG-COMM via snref and one of its
    positiv response's OUT-PARAM-IF via snref or snpathref.

    Unlike other parameters defined in the `parameters` package, a MatchingParameter is
    not transferred over the network.
    """

    # datatype according to ISO 22901-1 Figure 141
    expected_value: str
    diag_comm_snref: str
    out_param_if: str

    def __post_init__(self) -> None:
        odxassert(is_short_name(self.diag_comm_snref))
        odxassert(is_short_name_path(self.out_param_if))

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "MatchingParameter":

        expected_value = odxrequire(et_element.findtext("EXPECTED-VALUE"))
        diag_com_snref_el = odxrequire(et_element.find("DIAG-COMM-SNREF"))
        diag_comm_snref = odxrequire(diag_com_snref_el.get("SHORT-NAME"))
        out_param_snref_el = et_element.find("OUT-PARAM-IF-SNREF")
        out_param_snpathref_el = et_element.find("OUT-PARAM-IF-SNPATHREF")
        out_param_if = None
        if out_param_snref_el is not None:
            out_param_if = out_param_snref_el.get("SHORT-NAME")
        elif out_param_snpathref_el is not None:
            out_param_if = out_param_snpathref_el.get("SHORT-NAME-PATH")
        if out_param_if is None:
            odxraise("Output parameter must not left unspecified")

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
