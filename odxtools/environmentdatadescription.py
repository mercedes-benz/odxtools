# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from typing_extensions import override

from .complexdop import ComplexDop
from .decodestate import DecodeState
from .dtcdop import DtcDop
from .encodestate import EncodeState
from .environmentdata import EnvironmentData
from .exceptions import odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue, ParameterValueDict
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class EnvironmentDataDescription(ComplexDop):
    """This class represents environment data descriptions

    An environment data description provides a list of all environment
    data objects that are potentially applicable to decode a given
    response. (If a given environment data object is applicable
    depends on the value of the DtcDOP that is associated with it.)

    """

    param_snref: Optional[str]
    param_snpathref: Optional[str]

    # in ODX 2.0.0, ENV-DATAS seems to be a mandatory
    # sub-element of ENV-DATA-DESC, in ODX 2.2 it is not
    # present
    env_datas: NamedItemList[EnvironmentData]
    env_data_refs: List[OdxLinkRef]

    @property
    def param(self) -> Parameter:
        # the parameter referenced via SNREF cannot be resolved here
        # because the relevant list of parameters depends on the
        # concrete codec object processed, whilst an environment data
        # description object can be featured in an arbitrary number of
        # responses. Instead, lookup of the appropriate parameter is
        # done within the encode and decode methods.
        odxraise("The parameter of ENV-DATA-DESC objects cannot be resolved "
                 "because it depends on the context")
        return cast(None, Parameter)

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EnvironmentDataDescription":
        """Reads Environment Data Description from Diag Layer."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))

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
        env_data_refs = [
            odxrequire(OdxLinkRef.from_et(env_data_ref, doc_frags))
            for env_data_ref in et_element.iterfind("ENV-DATA-REFS/ENV-DATA-REF")
        ]
        env_datas = NamedItemList([
            EnvironmentData.from_et(env_data_elem, doc_frags)
            for env_data_elem in et_element.iterfind("ENV-DATAS/ENV-DATA")
        ])

        return EnvironmentDataDescription(
            param_snref=param_snref,
            param_snpathref=param_snpathref,
            env_data_refs=env_data_refs,
            env_datas=env_datas,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {self.odx_id: self}

        if not self.env_data_refs:
            for ed in self.env_datas:
                odxlinks.update(ed._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # ODX 2.0 specifies environment data objects here, ODX 2.2
        # uses references
        if self.env_data_refs:
            self.env_datas = NamedItemList([odxlinks.resolve(x) for x in self.env_data_refs])
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
    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        """Convert a physical value into bytes and emplace them into a PDU.
        """

        # retrieve the relevant DTC parameter which must be located in
        # front of the environment data description.
        if self.param_snref is None:
            odxraise("Specifying the DTC parameter for environment data "
                     "descriptions via SNPATHREF is not supported yet")
            return None

        dtc_param: Optional[Parameter] = None
        dtc_dop: Optional[DtcDop] = None
        dtc_param_value: Optional[ParameterValue] = None
        for prev_param, prev_param_value in reversed(encode_state.journal):
            if prev_param.short_name == self.param_snref:
                dtc_param = prev_param
                prev_dop = getattr(prev_param, "dop", None)
                if not isinstance(prev_dop, DtcDop):
                    odxraise(f"The DOP of the parameter referenced by environment data "
                             f"descriptions must be a DTC-DOP (is '{type(prev_dop).__name__}')")
                    return
                dtc_dop = prev_dop
                dtc_param_value = prev_param_value
                break

        if dtc_param is None:
            odxraise("Environment data description parameters are only allowed following "
                     "the referenced value parameter.")
            return

        if dtc_param_value is None or dtc_dop is None:
            # this should never happen
            odxraise()
            return

        numerical_dtc = dtc_dop.convert_to_numerical_trouble_code(dtc_param_value)

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
            if numerical_dtc in env_data.dtc_values:
                tmp = encode_state.allow_unknown_parameters
                encode_state.allow_unknown_parameters = True
                env_data.encode_into_pdu(physical_value, encode_state)
                encode_state.allow_unknown_parameters = tmp
                break

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        """Extract the bytes from a PDU and convert them to a physical value.
        """

        # retrieve the relevant DTC parameter which must be located in
        # front of the environment data description.
        if self.param_snref is None:
            odxraise("Specifying the DTC parameter for environment data "
                     "descriptions via SNPATHREF is not supported yet")
            return None

        dtc_param: Optional[Parameter] = None
        dtc_dop: Optional[DtcDop] = None
        dtc_param_value: Optional[ParameterValue] = None
        for prev_param, prev_param_value in reversed(decode_state.journal):
            if prev_param.short_name == self.param_snref:
                dtc_param = prev_param
                prev_dop = getattr(prev_param, "dop", None)
                if not isinstance(prev_dop, DtcDop):
                    odxraise(f"The DOP of the parameter referenced by environment data "
                             f"descriptions must be a DTC-DOP (is '{type(prev_dop).__name__}')")
                    return
                dtc_dop = prev_dop
                dtc_param_value = prev_param_value
                break

        if dtc_param is None:
            odxraise("Environment data description parameters are only allowed following "
                     "the referenced value parameter.")
            return

        if dtc_param_value is None or dtc_dop is None:
            # this should never happen
            odxraise()
            return

        numerical_dtc = dtc_dop.convert_to_numerical_trouble_code(dtc_param_value)

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
            if numerical_dtc in env_data.dtc_values:
                tmp = env_data.decode_from_pdu(decode_state)
                if not isinstance(tmp, dict):
                    odxraise()
                result.update(tmp)
                break

        return result
