# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .exceptions import odxrequire
from .multipleecujob import MultipleEcuJob
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class MatchingComponent:
    expected_value: str

    # exactly one of the following two attributes must be not None
    out_param_if_snref: str | None = None
    out_param_if_snpathref: str | None = None

    # exactly one of the following two attributes must be not None
    multiple_ecu_job_ref: OdxLinkRef | None = None
    diag_comm_ref: OdxLinkRef | None = None

    @property
    def multiple_ecu_job(self) -> MultipleEcuJob | None:
        return self._multiple_ecu_job

    @property
    def diag_comm(self) -> DiagComm | None:
        return self._diag_comm

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MatchingComponent":
        expected_value = odxrequire(et_element.findtext("EXPECTED-VALUE"))

        out_param_if_snref = None
        if (out_param_if_snref_elem := et_element.find("OUT-PARAM-IF-SNREF")) is not None:
            out_param_if_snref = odxrequire(out_param_if_snref_elem.attrib.get("SHORT-NAME"))

        out_param_if_snpathref = None
        if (out_param_if_snpathref_elem := et_element.find("OUT-PARAM-IF-SNPATHREF")) is not None:
            out_param_if_snpathref = odxrequire(
                out_param_if_snpathref_elem.attrib.get("SHORT-NAME-PATH"))

        multiple_ecu_job_ref = OdxLinkRef.from_et(et_element.find("MULTIPLE-ECU-JOB-REF"), context)
        diag_comm_ref = OdxLinkRef.from_et(et_element.find("DIAG-COMM-REF"), context)

        return MatchingComponent(
            expected_value=expected_value,
            out_param_if_snref=out_param_if_snref,
            out_param_if_snpathref=out_param_if_snpathref,
            multiple_ecu_job_ref=multiple_ecu_job_ref,
            diag_comm_ref=diag_comm_ref)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._multiple_ecu_job = None
        if self.multiple_ecu_job_ref is not None:
            self._multiple_ecu_job = odxlinks.resolve(self.multiple_ecu_job_ref, MultipleEcuJob)

        self._diag_comm = None
        if self.diag_comm_ref is not None:
            self._diag_comm = odxlinks.resolve(self.diag_comm_ref, DiagComm)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # TODO: find a good solution for resolving
        # OUT-PARAM-IF-SNREF. This is probably not possible ahead-of
        # time...
        pass
