# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from typing_extensions import override

from .complexdop import ComplexDop
from .dataobjectproperty import DataObjectProperty
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import EncodeError, OdxWarning, odxassert, odxraise
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterDict, ParameterValue, ParameterValueDict
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.createanyparameter import create_any_parameter_from_et
from .parameters.lengthkeyparameter import LengthKeyParameter
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .parameters.parameter import Parameter
from .parameters.parameterwithdop import ParameterWithDOP
from .parameters.physicalconstantparameter import PhysicalConstantParameter
from .parameters.tablekeyparameter import TableKeyParameter
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class BasicStructure(ComplexDop):
    parameters: NamedItemList[Parameter]
    byte_size: Optional[int]

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "BasicStructure":
        """Read a BASIC-STRUCTURE."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, doc_frags))

        parameters = NamedItemList([
            create_any_parameter_from_et(et_parameter, doc_frags)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ])

        byte_size_str = et_element.findtext("BYTE-SIZE")
        byte_size = int(byte_size_str) if byte_size_str is not None else None

        return BasicStructure(parameters=parameters, byte_size=byte_size, **kwargs)

    def get_static_bit_length(self) -> Optional[int]:
        # Explicit size was specified
        if self.byte_size:
            return 8 * self.byte_size

        cursor = 0
        byte_length = 0
        for param in self.parameters:
            param_bit_length = param.get_static_bit_length()
            if param_bit_length is None:
                # We were not able to calculate a static bit length
                return None
            elif param.byte_position is not None:
                cursor = param.byte_position

            cursor += ((param.bit_position or 0) + param_bit_length + 7) // 8
            byte_length = max(byte_length, cursor)

        # Round up to account for padding bits (all structures are
        # byte aligned)
        return byte_length * 8

    def coded_const_prefix(self, request_prefix: bytes = b'') -> bytes:
        encode_state = EncodeState(coded_message=bytearray(), triggering_request=request_prefix)

        for param in self.parameters:
            if (isinstance(param, MatchingRequestParameter) and param.request_byte_position < len(request_prefix)) or \
                isinstance(param, (CodedConstParameter, PhysicalConstantParameter)):
                param.encode_into_pdu(physical_value=None, encode_state=encode_state)
            else:
                break

        return encode_state.coded_message

    @property
    def required_parameters(self) -> List[Parameter]:
        """Return the list of parameters which are required for
        encoding the structure."""
        return [p for p in self.parameters if p.is_required]

    @property
    def free_parameters(self) -> List[Parameter]:
        """Return the list of parameters which can be freely specified by
        the user when encoding the structure.

        This means all required parameters plus the parameters that
        can be omitted minus those which are implicitly specified by
        the corresponding request (in the case of responses).

        """
        result: List[Parameter] = []
        for param in self.parameters:
            if not param.is_settable:
                continue
            result.append(param)

        return result

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the structure's
        free parameters.
        """
        from .parameterinfo import parameter_info

        print(parameter_info(self.free_parameters), end="")

    def _validate_coded_message_size(self, coded_byte_len: int) -> None:

        if self.byte_size is not None:
            # We definitely broke something if we didn't respect the explicit byte_size
            if self.byte_size != coded_byte_len:
                warnings.warn(
                    "Verification of coded message failed: Incorrect size.",
                    OdxWarning,
                    stacklevel=1)

            return

        bit_length = self.get_static_bit_length()

        if bit_length is None:
            # Nothing to check
            return

        if coded_byte_len * 8 != bit_length:
            # We may have broke something
            # but it could be that bit_length was mis calculated and not the actual bytes are wrong
            # Could happen with overlapping parameters and parameters with gaps
            warnings.warn(
                "Verification of coded message possibly failed: Size may be incorrect.",
                OdxWarning,
                stacklevel=1)

    @override
    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        if not isinstance(physical_value, dict):
            odxraise(
                f"Expected a dictionary for the values of structure {self.short_name}, "
                f"got {type(physical_value).__name__}", EncodeError)
        elif encode_state.cursor_bit_position != 0:
            odxraise(
                f"Structures must be byte aligned, but "
                f"{self.short_name} requested to be at bit position "
                f"{encode_state.cursor_bit_position}", EncodeError)
            encode_state.bit_position = 0

        orig_origin = encode_state.origin_byte_position
        encode_state.origin_byte_position = encode_state.cursor_byte_position

        orig_is_end_of_pdu = encode_state.is_end_of_pdu
        encode_state.is_end_of_pdu = False

        # ensure that no values for unknown parameters are specified.
        if not encode_state.allow_unknown_parameters:
            param_names = {param.short_name for param in self.parameters}
            for param_value_name in physical_value:
                if param_value_name not in param_names:
                    odxraise(f"Value for unknown parameter '{param_value_name}' specified "
                             f"for structure {self.short_name}")

        for param in self.parameters:
            if id(param) == id(self.parameters[-1]):
                # The last parameter of the structure is at the end of
                # the PDU if the structure itself is at the end of the
                # PDU. TODO: This assumes that the last parameter
                # specified in the ODX is located last in the PDU...
                encode_state.is_end_of_pdu = orig_is_end_of_pdu

            if isinstance(param, (LengthKeyParameter, TableKeyParameter)):
                # At this point, we encode a placeholder value for length-
                # and table keys, since these can be specified
                # implicitly (i.e., by means of parameters that use
                # these keys). To avoid getting an "overlapping
                # parameter" warning, we must encode a value of zero
                # into the PDU here and add the real value of the
                # parameter in a post-processing step.
                param.encode_placeholder_into_pdu(
                    physical_value=physical_value.get(param.short_name), encode_state=encode_state)

                continue

            if param.is_required and param.short_name not in physical_value:
                odxraise(f"No value for required parameter {param.short_name} specified",
                         EncodeError)

            param_phys_value = physical_value.get(param.short_name)
            param.encode_into_pdu(physical_value=param_phys_value, encode_state=encode_state)

            encode_state.journal.append((param, param_phys_value))

        encode_state.is_end_of_pdu = False
        if self.byte_size is not None:
            actual_len = encode_state.cursor_byte_position - encode_state.origin_byte_position
            if actual_len < self.byte_size:
                # Padding bytes needed. We add an empty object at the
                # position directly after the structure and let
                # EncodeState add the padding as needed.
                encode_state.cursor_byte_position = encode_state.origin_byte_position + self.byte_size
                # Padding bytes needed. these count as "used".
                encode_state.coded_message += b"\x00" * (self.byte_size - actual_len)
                encode_state.used_mask += b"\xff" * (self.byte_size - actual_len)

        # encode the length- and table keys. This cannot be done above
        # because we allow these to be defined implicitly (i.e. they
        # are defined by their respective users)
        for param in self.parameters:
            if not isinstance(param, (LengthKeyParameter, TableKeyParameter)):
                # the current parameter is neither a length- nor a table key
                continue

            # Encode the value of the key parameter into the message
            param.encode_value_into_pdu(encode_state=encode_state)

        # Assert that length is as expected
        self._validate_coded_message_size(encode_state.cursor_byte_position -
                                          encode_state.origin_byte_position)

        encode_state.origin_byte_position = orig_origin

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        # move the origin since positions specified by sub-parameters of
        # structures are relative to the beginning of the structure object.
        orig_origin = decode_state.origin_byte_position
        decode_state.origin_byte_position = decode_state.cursor_byte_position

        result = {}
        for param in self.parameters:
            value = param.decode_from_pdu(decode_state)

            decode_state.journal.append((param, value))
            result[param.short_name] = value

        # decoding of the structure finished. go back the original origin.
        decode_state.origin_byte_position = orig_origin

        return result

    def decode(self, message: bytes) -> ParameterValueDict:
        decode_state = DecodeState(coded_message=message)
        param_values = self.decode_from_pdu(decode_state)

        if not isinstance(param_values, dict):
            odxraise("Decoding structures must result in a dictionary")

        return cast(ParameterValueDict, param_values)

    def parameter_dict(self) -> ParameterDict:
        """
        Returns a dictionary with all parameter short names as keys.

        The values are parameters for simple types or a nested dict for structures.
        """
        from .structure import Structure
        odxassert(
            all(not isinstance(p, ParameterWithDOP) or isinstance(p.dop, DataObjectProperty) or
                isinstance(p.dop, Structure) for p in self.parameters))
        param_dict: ParameterDict = {
            p.short_name: p
            for p in self.parameters
            if not isinstance(p, ParameterWithDOP) or not isinstance(p.dop, Structure)
        }
        param_dict.update({
            struct_param.short_name: struct_param.dop.parameter_dict()
            for struct_param in self.parameters
            if isinstance(struct_param, ParameterWithDOP) and
            isinstance(struct_param.dop, BasicStructure)
        })
        return param_dict

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for param in self.parameters:
            result.update(param._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any references (odxlinks or sn-refs)"""
        super()._resolve_odxlinks(odxlinks)

        for param in self.parameters:
            param._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        """Recursively resolve any references (odxlinks or sn-refs)"""
        context.parameters = self.parameters

        super()._resolve_snrefs(context)

        for param in self.parameters:
            param._resolve_snrefs(context)

        context.parameters = None
