# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .exceptions import odxassert, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValueDict
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .state import State
from .statetransitionref import _check_applies
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .statemachine import StateMachine


@dataclass(kw_only=True)
class PreConditionStateRef(OdxLinkRef):
    """
    This class represents the PRE-CONDITION-STATE-REF XML tag.
    """
    value: str | None = None

    in_param_if_snref: str | None = None
    in_param_if_snpathref: str | None = None

    @property
    def state(self) -> "State":
        return self._state

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element, context: OdxDocContext) -> "PreConditionStateRef":
        kwargs = dataclass_fields_asdict(OdxLinkRef.from_et(et_element, context))

        value = et_element.findtext("VALUE")

        in_param_if_snref = None
        if (in_param_if_snref_elem := et_element.find("IN-PARAM-IF-SNREF")) is not None:
            in_param_if_snref = odxrequire(in_param_if_snref_elem.get("SHORT-NAME"))

        in_param_if_snpathref = None
        if (in_param_if_snpathref_elem := et_element.find("IN-PARAM-IF-SNPATHREF")) is not None:
            in_param_if_snpathref = odxrequire(in_param_if_snpathref_elem.get("SHORT-NAME-PATH"))

        return PreConditionStateRef(
            value=value,
            in_param_if_snref=in_param_if_snref,
            in_param_if_snpathref=in_param_if_snpathref,
            **kwargs)

    def __post_init__(self) -> None:
        if self.value is not None:
            odxassert(self.in_param_if_snref is not None or self.in_param_if_snref is not None,
                      "If VALUE is specified, a parameter must be referenced")

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._state = odxlinks.resolve(self, State)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    def applies(self, state_machine: "StateMachine", params: list[Parameter],
                param_value_dict: ParameterValueDict) -> bool:
        """Given a state machine, evaluate whether the precondition is fulfilled or not

        Note that the specification is unclear about what the
        parameters are: It says "The optional VALUE together with the
        also optional IN-PARAM-IF snref at STATE-TRANSITION-REF and
        PRE-CONDITION-STATE-REF can be used if the STATE-TRANSITIONs
        and pre-condition STATEs are dependent on the values of the
        referenced PARAMs.", but it does not specify what the
        "referenced PARAMs" are. For the state transition refs, let's
        assume that they are the parameters of a positive response
        received from the ECU, whilst we assume that they are the
        parameters of the request for PRE-CONDITION-STATE-REFs.
        """

        return _check_applies(self, state_machine, params, param_value_dict)
