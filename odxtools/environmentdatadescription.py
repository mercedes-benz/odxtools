# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from typing_extensions import override

from .complexdop import ComplexDop
from .dataobjectproperty import DataObjectProperty
from .decodestate import DecodeState
from .dtcdop import DtcDop
from .encodestate import EncodeState
from .environmentdata import EnvironmentData
from .exceptions import odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import DataType, ParameterValue, ParameterValueDict
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.parameter import Parameter
from .parameters.parameterwithdop import ParameterWithDOP
from .parameters.physicalconstantparameter import PhysicalConstantParameter
from .parameters.valueparameter import ValueParameter
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class EnvironmentDataDescription(ComplexDop):
    """This class represents environment data descriptions

    An environment data description provides a list of all environment
    data objects that are potentially applicable to decode a given
    response. (If a given environment data object is applicable
    depends on the value of the DtcDOP that is associated with it.)

    """

    param_snref: str | None = None
    param_snpathref: str | None = None

    # in ODX 2.0.0, ENV-DATAS seems to be a mandatory
    # sub-element of ENV-DATA-DESC, in ODX 2.2 it is not
    # present
    env_datas: NamedItemList[EnvironmentData] = field(default_factory=NamedItemList)
    env_data_refs: list[OdxLinkRef] = field(default_factory=list)

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "EnvironmentDataDescription":
        """Reads Environment Data Description from Diag Layer."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, context))

        param_snref = None
        if (param_snref_elem := et_element.find("PARAM-SNREF")) is not None:
            param_snref = odxrequire(param_snref_elem.get("SHORT-NAME"))
        param_snpathref = None
        if (param_snpathref_elem := et_element.find("PARAM-SNPATHREF")) is not None:
            param_snpathref = odxrequire(param_snpathref_elem.get("SHORT-NAME-PATH"))

        # ODX 2.0 mandates ENV-DATA-DESC to contain a list of
        # ENV-DATAS and no ENV-DATA-REFS while for ODX 2.2 the
        # situation is reversed. This means that we will create one
        # empty and one non-empty list here. (Which is which depends
        # on the version of the standard used by the file.)
        env_datas = NamedItemList([
            EnvironmentData.from_et(env_data_elem, context)
            for env_data_elem in et_element.iterfind("ENV-DATAS/ENV-DATA")
        ])
        env_data_refs = [
            odxrequire(OdxLinkRef.from_et(env_data_ref, context))
            for env_data_ref in et_element.iterfind("ENV-DATA-REFS/ENV-DATA-REF")
        ]

        return EnvironmentDataDescription(
            param_snref=param_snref,
            param_snpathref=param_snpathref,
            env_datas=env_datas,
            env_data_refs=env_data_refs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        if not self.env_data_refs:
            for ed in self.env_datas:
                odxlinks.update(ed._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # ODX 2.0 specifies environment data objects here, ODX 2.2
        # uses references
        if self.env_data_refs:
            self.env_datas = NamedItemList(
                [odxlinks.resolve(x, EnvironmentData) for x in self.env_data_refs])
        else:
            for ed in self.env_datas:
                ed._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # ODX 2.0 specifies environment data objects here, ODX 2.2
        # uses references
        if self.env_data_refs:
            for ed in self.env_datas:
                ed._resolve_snrefs(context)

    @override
    def encode_into_pdu(self, physical_value: ParameterValue | None,
                        encode_state: EncodeState) -> None:
        """Convert a physical value into bytes and emplace them into a PDU.
        """

        # retrieve the DTC as a numerical value from the referenced
        # parameter (which must be located somewhere before the
        # parameter using the environment data description)
        if self.param_snref is None:
            odxraise("Specifying the DTC parameter for environment data "
                     "descriptions via SNPATHREF is not supported yet")
            return None

        numerical_dtc_value: ParameterValue | None = None
        for prev_param, prev_param_value in reversed(encode_state.journal):
            if prev_param.short_name == self.param_snref:
                numerical_dtc_value = self._get_numerical_dtc_from_parameter(
                    prev_param, prev_param_value)
                break

        if numerical_dtc_value is None:
            odxraise("Environment data description parameters are only allowed following "
                     "the referenced parameter.")
            return

        # deal with the "all value" environment data. This holds
        # parameters that are common to all DTCs. Be aware that the
        # specification mandates that there is at most one such
        # environment data object
        for env_data in self.env_datas:
            if env_data.all_value:
                tmp = encode_state.allow_unknown_parameters
                encode_state.allow_unknown_parameters = True
                env_data.encode_into_pdu(physical_value, encode_state)
                encode_state.allow_unknown_parameters = tmp
                break

        # find the environment data corresponding to the given trouble
        # code
        for env_data in self.env_datas:
            if numerical_dtc_value in env_data.dtc_values:
                tmp = encode_state.allow_unknown_parameters
                encode_state.allow_unknown_parameters = True
                env_data.encode_into_pdu(physical_value, encode_state)
                encode_state.allow_unknown_parameters = tmp
                break

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Extract the bytes from a PDU and convert them to a physical value.
        """

        # retrieve the DTC as a numerical value from the referenced
        # parameter (which must be located somewhere before the
        # parameter using the environment data description)
        if self.param_snref is None:
            odxraise("Specifying the DTC parameter for environment data "
                     "descriptions via SNPATHREF is not supported yet")
            return None

        numerical_dtc_value: ParameterValue | None = None
        for prev_param, prev_param_value in reversed(decode_state.journal):
            if prev_param.short_name == self.param_snref:
                numerical_dtc_value = self._get_numerical_dtc_from_parameter(
                    prev_param, prev_param_value)
                break

        if numerical_dtc_value is None:
            odxraise("Environment data description parameters are only allowed following "
                     "the referenced parameter.")
            return

        result: ParameterValueDict = {}

        # deal with the "all value" environment data. This holds
        # parameters that are common to all DTCs. Be aware that the
        # specification mandates that there is at most one such
        # environment data object
        for env_data in self.env_datas:
            if env_data.all_value:
                tmp = env_data.decode_from_pdu(decode_state)
                if not isinstance(tmp, dict):
                    odxraise()
                result.update(tmp)
                break

        # find the environment data corresponding to the given trouble
        # code
        for env_data in self.env_datas:
            if numerical_dtc_value in env_data.dtc_values:
                tmp = env_data.decode_from_pdu(decode_state)
                if not isinstance(tmp, dict):
                    odxraise()
                result.update(tmp)
                break

        return result

    def _get_numerical_dtc_from_parameter(self, param: Parameter,
                                          param_value: ParameterValue | None) -> int:
        if isinstance(param, ParameterWithDOP):
            dop = param.dop
            if not isinstance(dop, (DataObjectProperty, DtcDop)):
                odxraise(f"The DOP of the parameter referenced by environment data descriptions "
                         f"must use either be DataObjectProperty or a DtcDop (encountered "
                         f"{type(param).__name__} for parameter '{param.short_name}' "
                         f"of ENV-DATA-DESC '{self.short_name}')")
                return 0

            if dop.diag_coded_type.base_data_type != DataType.A_UINT32:
                odxraise(f"The data type used by the DOP of the parameter referenced "
                         f"by environment data descriptions must be A_UINT32 "
                         f"(encountered '{dop.diag_coded_type.base_data_type.value}')")

            if param_value is None:
                if isinstance(param, ValueParameter):
                    param_value = param.physical_default_value
                elif isinstance(param, PhysicalConstantParameter):
                    param_value = param.physical_constant_value
                else:
                    odxraise()  # make mypy happy...
                    return

            if isinstance(dop, DtcDop):
                return dop.convert_to_numerical_trouble_code(odxrequire(param_value))
            elif isinstance(dop, DataObjectProperty):
                return int(dop.compu_method.convert_physical_to_internal(
                    param_value))  # type: ignore[arg-type]

            odxraise()  # not reachable...

        elif isinstance(param, CodedConstParameter):
            if param.diag_coded_type.base_data_type != DataType.A_UINT32:
                odxraise(f"The data type used by the parameter referenced "
                         f"by environment data descriptions must be A_UINT32 "
                         f"(encountered '{param.diag_coded_type.base_data_type.value}')")

                return param.coded_value

            if not isinstance(param.coded_value, int):
                odxraise()

            return param.coded_value

        else:
            odxraise(f"The parameter referenced by environment data descriptions "
                     f"must be a parameter that either specifies a DOP or a constant "
                     f"(encountered {type(param).__name__} for reference '{self.param_snref}' of "
                     f"ENV-DATA-DESC '{self.short_name}')")
            return 0
