# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from xml.etree import ElementTree

from .dataobjectproperty import DataObjectProperty
from .exceptions import odxassert, odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValueDict
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.parameter import Parameter
from .parameters.physicalconstantparameter import PhysicalConstantParameter
from .parameters.tablekeyparameter import TableKeyParameter
from .parameters.valueparameter import ValueParameter
from .snrefcontext import SnRefContext
from .state import State
from .statetransitionref import _resolve_in_param
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .statemachine import StateMachine


@dataclass
class PreConditionStateRef(OdxLinkRef):
    """
    This class represents the PRE-CONDITION-STATE-REF XML tag.
    """
    value: Optional[str]

    in_param_if_snref: Optional[str]
    in_param_if_snpathref: Optional[str]

    @property
    def state(self) -> "State":
        return self._state

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element,
            doc_frags: List[OdxDocFragment]) -> "PreConditionStateRef":
        kwargs = dataclass_fields_asdict(OdxLinkRef.from_et(et_element, doc_frags))

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

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._state = odxlinks.resolve(self, State)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    def applies(self, state_machine: "StateMachine", params: List[Parameter],
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

        if state_machine.active_state != self.state:
            # if the active state of the state machine is not the
            # specified one, the precondition does not apply
            return False

        if self.in_param_if_snref is None and self.in_param_if_snpathref is None:
            # no parameter given -> only the specified state is relevant
            return True

        param, param_value = \
            _resolve_in_param(self.in_param_if_snref, self.in_param_if_snpathref, params, param_value_dict)

        if param is None:
            # The referenced parameter does not exist. TODO: is this an error?
            return False
        elif not isinstance(
                param,
            (CodedConstParameter, PhysicalConstantParameter, TableKeyParameter, ValueParameter)):
            # see checker rule 194 in section B.2 of the spec
            odxraise(f"Parameter referenced by state transition ref is of "
                     f"invalid type {type(param).__name__}")
            return False
        elif isinstance(param, (CodedConstParameter, PhysicalConstantParameter,
                                TableKeyParameter)) and self.value is not None:
            # see checker rule 193 in section B.2 of the spec. Why can
            # no values for constant parameters be specified? (This
            # seems to be rather inconvenient...)
            odxraise(f"No value may be specified for state transitions referencing "
                     f"parameters of type {type(param).__name__}")
            return False
        elif isinstance(param, ValueParameter):
            # see checker rule 193 in section B.2 of the spec
            if self.value is None:
                odxraise(f"An expected VALUE must be specified for preconditions "
                         f"referencing VALUE parameters")
                return False

            if param_value is None:
                param_value = param.physical_default_value
                if param_value is None:
                    odxraise(f"No value can be determined for parameter {param.short_name}")
                    return False

            if param.dop is None or not isinstance(param.dop, DataObjectProperty):
                odxraise(f"Parameter {param.short_name} uses a non-simple DOP")
                return False

            expected_value = param.dop.physical_type.base_data_type.from_string(self.value)

            if expected_value != param_value:
                return False

        return True
