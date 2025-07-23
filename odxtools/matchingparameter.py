# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, cast
from xml.etree import ElementTree

from .diaglayers.diaglayer import DiagLayer
from .diagnostictroublecode import DiagnosticTroubleCode
from .diagservice import DiagService
from .exceptions import odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, resolve_snref
from .odxtypes import BytesTypes, ParameterValue, ParameterValueDict
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class MatchingParameter:
    """According to ISO 22901, a MatchingParameter contains a string
    value identifying the active ECU or base variant. Moreover, it
    references a DIAG-COMM via snref and one of its positive
    response's OUT-PARAM-IF via snref or snpathref.

    Unlike other parameters defined in the `parameters` package, a
    MatchingParameter is not transferred over the network.

    """

    expected_value: str
    diag_comm_snref: str

    # be aware that the checker rules 23 and 110 contradict each other
    # here: the first specifies that the referenced parameter must be
    # present in *all* positive responses of the referenced service,
    # whilst the latter mandates it to be present least one positive
    # or negative response. What it probably actually wants to say is
    # that any response that can possibly be received shall exhibit
    # the referenced parameter.
    out_param_if_snref: str | None = None
    out_param_if_snpathref: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MatchingParameter":

        expected_value = odxrequire(et_element.findtext("EXPECTED-VALUE"))
        diag_comm_snref = odxrequire(
            odxrequire(et_element.find("DIAG-COMM-SNREF")).get("SHORT-NAME"))

        out_param_if_snref = None
        out_param_if_snpathref = None
        if (out_param_snref_el := et_element.find("OUT-PARAM-IF-SNREF")) is not None:
            out_param_if_snref = odxrequire(out_param_snref_el.get("SHORT-NAME"))
        elif (out_param_snpathref_el := et_element.find("OUT-PARAM-IF-SNPATHREF")) is not None:
            out_param_if_snpathref = odxrequire(out_param_snpathref_el.get("SHORT-NAME-PATH"))
        else:
            odxraise("Output parameter must not be left unspecified")

        return MatchingParameter(
            expected_value=expected_value,
            diag_comm_snref=diag_comm_snref,
            out_param_if_snref=out_param_if_snref,
            out_param_if_snpathref=out_param_if_snpathref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # note that we do not resolve the SNREF to the diag layer here
        # because it is a component which changes depending on the
        # execution context and for variant patterns the execution
        # context is highly volatile w.r.t. the diag layer in question
        pass

    def get_ident_service(self, diag_layer: DiagLayer) -> DiagService:
        return resolve_snref(self.diag_comm_snref, diag_layer.services, DiagService)

    def matches(self, param_dict: ParameterValueDict) -> bool:
        """
        Returns true iff the provided identification value matches this MatchingParameter's
        expected value.
        """

        if self.out_param_if_snref is not None:
            snpath_chunks = [self.out_param_if_snref]
        elif self.out_param_if_snpathref is not None:
            snpath_chunks = self.out_param_if_snpathref.split(".")
        else:
            odxraise("no out_param_if specified")
            return False

        return self.__matches(param_dict, snpath_chunks)

    def __matches(self, param_dict: ParameterValue, snpath_chunks: list[str]) -> bool:
        if len(snpath_chunks) == 0:
            parameter_value = param_dict
            if isinstance(parameter_value, dict):
                odxraise(f"Parameter must not be a structure")
                return False

            if isinstance(parameter_value, float):
                # allow a slight tolerance if the expected value is
                # floating point
                return abs(float(self.expected_value) - parameter_value) < 1e-8
            elif isinstance(parameter_value, BytesTypes):
                return bytes(parameter_value).hex().upper() == self.expected_value.upper()
            elif isinstance(parameter_value, DiagnosticTroubleCode):
                # TODO: what happens if non-numerical DTCs like
                # "U123456" are specified? Is specifying DTCs even
                # allowed in variant patterns?
                return hex(parameter_value.trouble_code).upper() == self.expected_value.upper()
            else:
                return self.expected_value == str(parameter_value)

        if not isinstance(param_dict, dict):
            odxraise(f"Parameter {snpath_chunks[0]} must be a structure")
            return False

        sub_value = param_dict.get(snpath_chunks[0])
        if sub_value is None:
            return False

        if isinstance(sub_value, tuple) and len(sub_value) == 2:
            # table struct parameter
            sub_value = sub_value[1]

        if isinstance(sub_value, list):
            # the spec mandates that if any item of a field matches,
            # the parameter as a whole matches
            for x in sub_value:
                if self.__matches(x, snpath_chunks[1:]):
                    return True

            return False

        return self.__matches(cast(ParameterValue, sub_value), snpath_chunks[1:])
