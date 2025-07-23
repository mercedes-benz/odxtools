# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from typing_extensions import override

from .complexdop import ComplexDop
from .compositecodec import (composite_codec_decode_from_pdu, composite_codec_encode_into_pdu,
                             composite_codec_get_free_parameters,
                             composite_codec_get_required_parameters,
                             composite_codec_get_static_bit_length)
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, odxraise
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterValue
from .parameters.createanyparameter import create_any_parameter_from_et
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class BasicStructure(ComplexDop):
    """Base class for structure-like objects

    "Structure-like" objects are structures as well as environment
    data objects. All structure-like objects adhere to the
    `CompositeCodec` type protocol.
    """
    byte_size: int | None = None
    parameters: NamedItemList[Parameter] = field(default_factory=NamedItemList)

    @property
    def required_parameters(self) -> list[Parameter]:
        return composite_codec_get_required_parameters(self)

    @property
    def free_parameters(self) -> list[Parameter]:
        return composite_codec_get_free_parameters(self)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "BasicStructure":
        """Read a BASIC-STRUCTURE."""
        kwargs = dataclass_fields_asdict(ComplexDop.from_et(et_element, context))

        byte_size_str = et_element.findtext("BYTE-SIZE")
        byte_size = int(byte_size_str) if byte_size_str is not None else None
        parameters = NamedItemList([
            create_any_parameter_from_et(et_parameter, context)
            for et_parameter in et_element.iterfind("PARAMS/PARAM")
        ])

        return BasicStructure(byte_size=byte_size, parameters=parameters, **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for param in self.parameters:
            result.update(param._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for param in self.parameters:
            param._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.parameters = self.parameters

        super()._resolve_snrefs(context)
        for param in self.parameters:
            param._resolve_snrefs(context)

        context.parameters = None

    def get_static_bit_length(self) -> int | None:
        # Explicit size was specified, so we do not need to look at
        # the list of parameters
        if self.byte_size is not None:
            return 8 * self.byte_size

        return composite_codec_get_static_bit_length(self)

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the structure's
        free parameters.
        """
        from .parameterinfo import parameter_info

        print(parameter_info(self.free_parameters), end="")

    @override
    def encode_into_pdu(self, physical_value: ParameterValue | None,
                        encode_state: EncodeState) -> None:
        orig_pos = encode_state.cursor_byte_position

        composite_codec_encode_into_pdu(self, physical_value, encode_state)

        if self.byte_size is not None:
            actual_len = encode_state.cursor_byte_position - orig_pos

            if actual_len < self.byte_size:
                # Padding bytes are needed. We add an empty object at
                # the position directly after the structure and let
                # EncodeState add the padding as needed.
                encode_state.cursor_byte_position = encode_state.origin_byte_position + self.byte_size
                # Padding bytes needed. these count as "used".
                encode_state.coded_message += b"\x00" * (self.byte_size - actual_len)
                encode_state.used_mask += b"\xff" * (self.byte_size - actual_len)

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:
        orig_pos = decode_state.cursor_byte_position

        result = composite_codec_decode_from_pdu(self, decode_state)

        if self.byte_size is not None:
            n = decode_state.cursor_byte_position - orig_pos
            if n > self.byte_size:
                odxraise(
                    f"Attempted to decode too large instance of structure "
                    f"{self.short_name} ({n} instead at most "
                    f"{self.byte_size} bytes)", DecodeError)
                return result

            decode_state.cursor_byte_position = orig_pos + self.byte_size

        return result
