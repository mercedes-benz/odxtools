# SPDX-License-Identifier: MIT
import typing
from typing import List, Optional, runtime_checkable

from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import EncodeError, odxraise
from .odxtypes import ParameterValue
from .parameters.codedconstparameter import CodedConstParameter
from .parameters.matchingrequestparameter import MatchingRequestParameter
from .parameters.parameter import Parameter
from .parameters.physicalconstantparameter import PhysicalConstantParameter


@runtime_checkable
class Codec(typing.Protocol):
    """Any object which can be en- or decoded to be transferred over
    the wire implements this API.
    """

    @property
    def short_name(self) -> str:
        return ""

    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        ...

    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        ...

    def get_static_bit_length(self) -> Optional[int]:
        ...


@runtime_checkable
class CompositeCodec(Codec, typing.Protocol):
    """Any object which can be en- or decoded to be transferred over
    the wire which is composed of multiple parameter implements this
    API.

    """

    @property
    def parameters(self) -> List[Parameter]:
        return []

    @property
    def required_parameters(self) -> List[Parameter]:
        return []

    @property
    def free_parameters(self) -> List[Parameter]:
        return []


# some helper functions useful for composite codec objects
def composite_codec_get_static_bit_length(codec: CompositeCodec) -> Optional[int]:
    """Compute the length of a composite codec object in bits

    This is basically the sum of the lengths of all parameters. If the
    length of any parameter can only determined at runtime, `None` is
    returned.
    """

    cursor = 0
    byte_length = 0
    for param in codec.parameters:
        param_bit_length = param.get_static_bit_length()
        if param_bit_length is None:
            # We were not able to calculate a static bit length
            return None
        elif param.byte_position is not None:
            cursor = param.byte_position

        cursor += ((param.bit_position or 0) + param_bit_length + 7) // 8
        byte_length = max(byte_length, cursor)

    return byte_length * 8


def composite_codec_get_required_parameters(codec: CompositeCodec) -> List[Parameter]:
    """Return the list of parameters which are required to be
    specified for encoding the composite codec object

    I.e., all free parameters that do not exhibit a default value.
    """
    return [p for p in codec.parameters if p.is_required]


def composite_codec_get_free_parameters(codec: CompositeCodec) -> List[Parameter]:
    """Return the list of parameters which can be freely specified by
    the user when encoding the composite codec object

    This means all required parameters plus parameters that can be
    omitted because they specify a default.
    """
    return [p for p in codec.parameters if p.is_settable]


def composite_codec_get_coded_const_prefix(codec: CompositeCodec,
                                           request_prefix: bytes = b'') -> bytes:
    encode_state = EncodeState(coded_message=bytearray(), triggering_request=request_prefix)

    for param in codec.parameters:
        if (isinstance(param, MatchingRequestParameter) and param.request_byte_position < len(request_prefix)) or \
            isinstance(param, (CodedConstParameter, PhysicalConstantParameter)):
            param.encode_into_pdu(physical_value=None, encode_state=encode_state)
        else:
            break

    return encode_state.coded_message


def composite_codec_encode_into_pdu(codec: CompositeCodec, physical_value: Optional[ParameterValue],
                                    encode_state: EncodeState) -> None:
    from .parameters.lengthkeyparameter import LengthKeyParameter
    from .parameters.tablekeyparameter import TableKeyParameter

    if not isinstance(physical_value, dict):
        odxraise(
            f"Expected a dictionary for the values of {codec.short_name}, "
            f"got {type(physical_value).__name__}", EncodeError)
    elif encode_state.cursor_bit_position != 0:
        odxraise(
            f"Compositional codec objecs must be byte aligned, but "
            f"{codec.short_name} requested to be at bit position "
            f"{encode_state.cursor_bit_position}", EncodeError)
        encode_state.bit_position = 0

    orig_origin = encode_state.origin_byte_position
    encode_state.origin_byte_position = encode_state.cursor_byte_position

    orig_is_end_of_pdu = encode_state.is_end_of_pdu
    encode_state.is_end_of_pdu = False

    # ensure that no values for unknown parameters are specified.
    if not encode_state.allow_unknown_parameters:
        param_names = {param.short_name for param in codec.parameters}
        for param_value_name in physical_value:
            if param_value_name not in param_names:
                odxraise(f"Value for unknown parameter '{param_value_name}' specified "
                         f"for composite codec object {codec.short_name}")

    for param in codec.parameters:
        if id(param) == id(codec.parameters[-1]):
            # The last parameter of the composite codec object is at
            # the end of the PDU if the codec object itself is at the
            # end of the PDU.
            #
            # TODO: This assumes that the last parameter specified in
            # the ODX is located last in the PDU...
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
            odxraise(f"No value for required parameter {param.short_name} specified", EncodeError)

        param_phys_value = physical_value.get(param.short_name)
        param.encode_into_pdu(physical_value=param_phys_value, encode_state=encode_state)

        encode_state.journal.append((param, param_phys_value))

    encode_state.is_end_of_pdu = False

    # encode the length- and table keys. This cannot be done above
    # because we allow these to be defined implicitly (i.e. they
    # are defined by their respective users)
    for param in codec.parameters:
        if not isinstance(param, (LengthKeyParameter, TableKeyParameter)):
            # the current parameter is neither a length- nor a table key
            continue

        # Encode the value of the key parameter into the message
        param.encode_value_into_pdu(encode_state=encode_state)

    encode_state.origin_byte_position = orig_origin


def composite_codec_decode_from_pdu(codec: CompositeCodec,
                                    decode_state: DecodeState) -> ParameterValue:
    # move the origin since positions specified by sub-parameters of
    # composite codec objects are relative to the beginning of the
    # object.
    orig_origin = decode_state.origin_byte_position
    decode_state.origin_byte_position = decode_state.cursor_byte_position

    result = {}
    for param in codec.parameters:
        value = param.decode_from_pdu(decode_state)

        decode_state.journal.append((param, value))
        result[param.short_name] = value

    # decoding of the composite codec object finished. go back the
    # original origin.
    decode_state.origin_byte_position = orig_origin

    return result
