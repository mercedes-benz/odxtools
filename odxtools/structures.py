# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import math
import warnings
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, OrderedDict, Tuple, Union

from .dataobjectproperty import DataObjectProperty, DopBase
from .decodestate import DecodeState
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, OdxError, OdxWarning
from .globals import logger
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .odxtypes import ParameterDict, ParameterValueDict, odxstr_to_bool
from .parameters import (CodedConstParameter, MatchingRequestParameter, Parameter, ParameterWithDOP,
                         ValueParameter, create_any_parameter_from_et)
from .parameters.lengthkeyparameter import LengthKeyParameter
from .parameters.tablekeyparameter import TableKeyParameter
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer
    from .endofpdufield import EndOfPduField


class BasicStructure(DopBase):

    def __init__(
        self,
        *,
        parameters: Iterable[Union[Parameter, "EndOfPduField"]],
        byte_size: Optional[int],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.parameters: NamedItemList[Union[Parameter, "EndOfPduField"]] = NamedItemList(
            short_name_as_id, parameters)
        self.byte_size = byte_size

    @property
    def bit_length(self) -> Optional[int]:
        # Explicit size was specified
        if self.byte_size:
            return 8 * self.byte_size

        if all(p.bit_length is not None for p in self.parameters):
            offset = 0
            length = 0
            for param in self.parameters:
                if isinstance(param, ValueParameter) and hasattr(param.dop, "min_number_of_items"):
                    # The param repeats itself, making bit_length calculation invalid
                    # Temporary workaround
                    # Can not import EndOfPduField to check on its type due to circular dependency
                    return None

                if param.byte_position is not None:
                    bit_position_int = param.bit_position if param.bit_position is not None else 0
                    byte_position_int = (
                        param.byte_position if param.byte_position is not None else 0)
                    offset = byte_position_int * 8 + bit_position_int
                offset += param.bit_length

                length = max(length, offset)

            # Round up to account for padding bits
            return math.ceil(length / 8) * 8

        # We were not able to calculate a static bit length
        return None

    def coded_const_prefix(self, request_prefix: bytes = bytes()) -> bytes:
        prefix = bytes()
        encode_state = EncodeState(prefix, parameter_values={}, triggering_request=request_prefix)
        for p in self.parameters:
            if isinstance(p, CodedConstParameter) and p.bit_length % 8 == 0:
                encode_state.coded_message = p.encode_into_pdu(encode_state)
            elif isinstance(p, MatchingRequestParameter):
                encode_state.coded_message = p.encode_into_pdu(encode_state)
            else:
                break
        return encode_state.coded_message

    @property
    def required_parameters(self) -> List[Parameter]:
        """Return the list of parameters which are required for
        encoding the structure."""
        return [p for p in self.parameters if p.is_required()]

    @property
    def free_parameters(self) -> List[Union[Parameter, "EndOfPduField"]]:  # type: ignore
        """Return the list of parameters which can be freely specified by
        the user when encoding the structure.

        This means all required parameters plus the parameters that
        can be omitted minus those which are implicitly specified by
        the corresponding request (in the case of responses).

        """
        from .endofpdufield import EndOfPduField

        result: List[Union[Parameter, EndOfPduField]] = []
        for param in self.parameters:
            if isinstance(param, EndOfPduField):
                result.append(param)
                continue
            elif not param.is_required():
                continue
            # The user cannot specify MatchingRequestParameters freely!
            elif isinstance(param, MatchingRequestParameter):
                continue
            result.append(param)

        return result

    def print_free_parameters_info(self) -> None:
        """Return a human readable description of the structure's
        free parameters.
        """
        from .parameter_info import parameter_info

        print(parameter_info(self.free_parameters), end="")

    def convert_physical_to_internal(self,
                                     param_values: ParameterValueDict,
                                     triggering_coded_request: Optional[bytes],
                                     is_end_of_pdu: bool = True) -> bytes:

        encode_state = EncodeState(
            bytes(),
            dict(param_values),
            triggering_request=triggering_coded_request,
            is_end_of_pdu=False,
        )

        for param in self.parameters:
            if param == self.parameters[-1]:
                # The last parameter is at the end of the PDU if the
                # structure itself is at the end of the PDU. TODO:
                # This assumes that the last parameter specified in
                # the ODX is located last in the PDU...
                encode_state.is_end_of_pdu = is_end_of_pdu

            encode_state.coded_message = param.encode_into_pdu(encode_state)

        if self.byte_size is not None and len(encode_state.coded_message) < self.byte_size:
            # Padding bytes needed
            encode_state.coded_message = encode_state.coded_message.ljust(self.byte_size, b"\0")

        # encode the length- and table keys. This cannot be done above
        # because we allow these to be defined implicitly (i.e. they
        # are defined by their respective users)
        for param in self.parameters:
            if not isinstance(param, (LengthKeyParameter, TableKeyParameter)):
                # the current parameter is neither a length- nor a table key
                continue

            # Encode the key parameter into the message
            encode_state.coded_message = param.encode_into_pdu(encode_state)

        # Assert that length is as expected
        self._validate_coded_message(encode_state.coded_message)

        return bytearray(encode_state.coded_message)

    def _validate_coded_message(self, coded_message: bytes) -> None:

        if self.byte_size is not None:
            # We definitely broke something if we didn't respect the explicit byte_size
            assert len(coded_message) == self.byte_size, self._get_encode_error_str(
                "was", coded_message, self.byte_size * 8)
            # No need to check further
            return

        bit_length = self.bit_length

        if bit_length is None:
            # Nothing to check
            return

        if len(coded_message) * 8 != bit_length:
            # We may have broke something
            # but it could be that bit_length was mis calculated and not the actual bytes are wrong
            # Could happen with overlapping parameters and parameters with gaps
            warnings.warn(
                self._get_encode_error_str("may have been", coded_message, bit_length), OdxWarning)

    def _get_encode_error_str(self, verb: str, coded_message: bytes, bit_length: int) -> str:
        return str(f"Structure {self.short_name} {verb} encoded incorrectly:" +
                   f" actual length is {len(coded_message)}," +
                   f" computed byte length is {bit_length // 8}," +
                   f" computed_rpc is {coded_message.hex()}\n" +
                   "\n".join(self.__message_format_lines()))

    def convert_physical_to_bytes(self,
                                  param_values: ParameterValueDict,
                                  encode_state: EncodeState,
                                  bit_position: int = 0) -> bytes:
        if bit_position != 0:
            raise EncodeError("Structures must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")
        return self.convert_physical_to_internal(
            param_values,
            triggering_coded_request=encode_state.triggering_request,
            is_end_of_pdu=encode_state.is_end_of_pdu,
        )

    def convert_bytes_to_physical(self,
                                  decode_state: DecodeState,
                                  bit_position: int = 0) -> Tuple[ParameterValueDict, int]:
        if bit_position != 0:
            raise DecodeError("Structures must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")
        byte_code = decode_state.coded_message[decode_state.next_byte_position:]
        inner_decode_state = DecodeState(
            coded_message=byte_code, parameter_values={}, next_byte_position=0)

        for parameter in self.parameters:
            value, next_byte_position = parameter.decode_from_pdu(inner_decode_state)

            inner_decode_state.parameter_values[parameter.short_name] = value
            inner_decode_state = DecodeState(
                coded_message=byte_code,
                parameter_values=inner_decode_state.parameter_values,
                next_byte_position=max(inner_decode_state.next_byte_position, next_byte_position),
            )

        return inner_decode_state.parameter_values, decode_state.next_byte_position + inner_decode_state.next_byte_position

    def encode(self, coded_request: Optional[bytes] = None, **params) -> bytes:
        """
        Composes an UDS message as bytes for this service.
        Parameters:
        ----------
        coded_request: bytes
            coded request (only needed when encoding a response)
        params: dict
            Parameters of the RPC as mapping from SHORT-NAME of the parameter to the value
        """
        return self.convert_physical_to_internal(
            params,  # type: ignore[arg-type]
            triggering_coded_request=coded_request,
            is_end_of_pdu=True)

    def decode(self, message: bytes) -> ParameterValueDict:
        # dummy decode state to be passed to convert_bytes_to_physical
        decode_state = DecodeState(parameter_values={}, coded_message=message, next_byte_position=0)
        param_values, next_byte_position = self.convert_bytes_to_physical(decode_state)
        if len(message) != next_byte_position:
            warnings.warn(
                f"The message {message.hex()} is longer than could be parsed."
                f" Expected {next_byte_position} but got {len(message)}.",
                DecodeError,
            )
        return param_values

    def parameter_dict(self) -> ParameterDict:
        """
        Returns a dictionary with all parameter short names as keys.

        The values are parameters for simple types or a nested dict for structures.
        """
        assert all(not isinstance(p, ParameterWithDOP) or isinstance(p.dop, DataObjectProperty) or
                   isinstance(p.dop, Structure) for p in self.parameters)
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

    def _build_odxlinks(self):
        result = super()._build_odxlinks()

        for p in self.parameters:
            result.update(p._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve any references (odxlinks or sn-refs)"""
        super()._resolve_odxlinks(odxlinks)

        for p in self.parameters:
            p._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        """Recursively resolve any references (odxlinks or sn-refs)"""
        super()._resolve_snrefs(diag_layer)

        for p in self.parameters:
            p._resolve_snrefs(diag_layer)

    def __message_format_lines(self, allow_unknown_lengths: bool = False) -> List[str]:
        # sort parameters
        sorted_params: list = list(self.parameters)  # copy list

        def param_sort_key(param: Union[Parameter, "EndOfPduField"]) -> Tuple[int, int]:
            if not isinstance(param, Parameter):
                # -> EndOfPduField should come last!
                return (1000 * 1000, 0)

            byte_position_int = param.byte_position if param.byte_position is not None else 0
            bit_position_int = param.bit_position if param.bit_position is not None else 0
            return (byte_position_int, 8 - bit_position_int)

        sorted_params.sort(key=param_sort_key)

        # replace structure parameters by their sub parameters
        params: List[Parameter] = []
        for p in sorted_params:
            if isinstance(p, ValueParameter) and isinstance(p.dop, BasicStructure):
                params += p.dop.parameters
            else:
                params.append(p)

        param_idx = 0
        byte_idx = 0
        # needs to be one larger than the maximum digit length of a byte number
        indent_for_byte_numbering = 5 * " "
        formatted_lines = [
            indent_for_byte_numbering + "".join(f"   {7-bit_idx}  " for bit_idx in range(8))
        ]

        stop_bit = 0  # absolute bit position where the next parameter starts

        divide_string = indent_for_byte_numbering + 8 * "+-----" + "+"

        error = False
        next_line = ""
        while param_idx <= len(params) and not error:  # For each byte
            if 8 * byte_idx == stop_bit and param_idx == len(params):
                # If we have formatted the last parameter, we're done.
                break

            formatted_lines.append(f"{divide_string}")
            if stop_bit // 8 - byte_idx > 5:
                curr_param = params[param_idx - 1].short_name
                formatted_lines.append(
                    indent_for_byte_numbering +
                    f"  ... {stop_bit // 8 - byte_idx} bytes belonging to {curr_param} ... ")
                byte_idx += stop_bit // 8 - byte_idx
                continue

            next_line = (
                f"{(len(indent_for_byte_numbering) - 1 - len(str(byte_idx))) * ' '}{byte_idx} ")

            for bit_idx in range(8):
                assert 8 * byte_idx + bit_idx <= stop_bit

                if 8 * byte_idx + bit_idx == stop_bit:
                    # END-OF-PDU fields do not exhibit a fixed bit
                    # length, so they need special treatment here
                    dct = None
                    if hasattr(params[param_idx], "dop"):
                        dop = params[param_idx].dop  # type: ignore
                        if hasattr(dop, "diag_coded_type"):
                            dct = dop.diag_coded_type

                    bit_length = None
                    if hasattr(params[param_idx], "bit_length"):
                        bit_length = params[param_idx].bit_length

                    if dct is not None and dct.dct_type == "MIN-MAX-LENGTH-TYPE":
                        name = params[param_idx].short_name + " ("
                        if dct.termination == "END-OF-PDU":
                            name += "End of PDU, "
                        name += f"{dct.min_length}..{dct.max_length} bytes"
                        name += ")"
                        next_line += "| " + name

                        param_idx += 1

                        # adding 8 is is a bit hacky here, but hey, it
                        # works ...
                        stop_bit += 8

                        break

                    elif not bit_length and not allow_unknown_lengths:
                        # The bit length is not set for the current
                        # parameter, i.e. it was either not specified
                        # or the parameter is of variable length and
                        # has an type which is not handled above. In
                        # this case, stop trying.
                        error = True
                        break
                    else:
                        bit_length = 0 if bit_length is None else bit_length
                        stop_bit += bit_length or (allow_unknown_lengths and 8)
                        name = params[param_idx].short_name + f" ({bit_length or 'Unknown'} bits)"
                        next_line += "| " + name

                    param_idx += 1

                    if byte_idx == stop_bit // 8:
                        char_pos = bit_idx * 6 + 2 + len(name)
                        width_of_line = (stop_bit % 8) * 6
                        if char_pos < width_of_line:
                            next_line += " " * (width_of_line - char_pos) + "|"
                        # start next line (belongs to same byte)
                        formatted_lines.append(next_line)
                        # fill next line with white spaces up to the
                        # bit where next parameter starts
                        next_line = indent_for_byte_numbering + (bit_idx + 1) * 6 * " "
                    else:
                        char_pos = 2 + bit_idx * 6 + len(name)
                        width_of_line = 8 * 6
                        if char_pos < width_of_line:
                            next_line += " " * (width_of_line - char_pos) + "|"
                        break
                else:
                    if bit_idx == 0:
                        next_line += "|" + 5 * " "
                    elif bit_idx == 7:
                        next_line += 6 * " " + "|"
                    else:
                        next_line += 6 * " "

            formatted_lines.append(next_line)
            next_line = ""

            byte_idx += 1

        if not error:
            formatted_lines.append(divide_string)
            return formatted_lines
        else:
            return []

    def print_message_format(self, indent: int = 5, allow_unknown_lengths=False):
        """
        Print a description of the message format to `stdout`.
        """

        message_as_lines = self.__message_format_lines(allow_unknown_lengths=allow_unknown_lengths)
        if message_as_lines is not None:
            print(f"{indent * ' '}" + f"\n{indent * ' '}".join(message_as_lines))
        else:
            print("Sorry, couldn't pretty print message layout. :(")
        for p in self.parameters:
            print(indent * " " + str(p).replace("\n", f"\n{indent * ' '}"))


class Structure(BasicStructure):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"Structure('{self.short_name}', byte_size={self.byte_size})"

    def __str__(self) -> str:
        params = ("[\n" + "\n".join([" " + str(p).replace("\n", "\n ") for p in self.parameters]) +
                  "\n]")

        return (f"Structure '{self.short_name}': " + f"Byte size={self.byte_size}, " +
                f"Parameters={params}")


class Request(BasicStructure):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"Request('{self.short_name}')"

    def __str__(self) -> str:
        return f"Request('{self.short_name}')"


class Response(BasicStructure):

    def __init__(self, *, response_type: str, **kwargs):  # "POS-RESPONSE" or "NEG-RESPONSE"
        super().__init__(**kwargs)

        self.response_type = response_type

    def encode(self, coded_request: Optional[bytes] = None, **params) -> bytes:
        if coded_request is not None:
            logger.info(f"Compose response message to the request {coded_request.hex()}")
            # Extract MATCHING-REQUEST-PARAMs from the coded request
            for param in self.parameters:
                if param.parameter_type == "MATCHING-REQUEST-PARAM":
                    logger.info(f"set matching request param value {param.short_name}")
                    byte_pos = param.request_byte_position
                    byte_length = param.byte_length

                    val = coded_request[byte_pos:byte_pos + byte_length]
                    params[param.short_name] = val

        return super().encode(coded_request=coded_request, **params)

    def __repr__(self) -> str:
        return f"Response('{self.short_name}')"

    def __str__(self) -> str:
        return f"Response('{self.short_name}')"


def create_any_structure_from_et(et_element, doc_frags: List[OdxDocFragment]
                                ) -> Union[Structure, Request, Response, None]:

    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    short_name = et_element.findtext("SHORT-NAME")
    long_name = et_element.findtext("LONG-NAME")
    description = create_description_from_et(et_element.find("DESC"))
    parameters = [
        create_any_parameter_from_et(et_parameter, doc_frags)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

    res: Union[Structure, Request, Response, None]
    if et_element.tag == "REQUEST":
        res = Request(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            is_visible_raw=None,
            parameters=parameters,
            byte_size=None,
            sdgs=sdgs,
        )
    elif et_element.tag in ["POS-RESPONSE", "NEG-RESPONSE", "GLOBAL-NEG-RESPONSE"]:
        res = Response(
            odx_id=odx_id,
            short_name=short_name,
            response_type=et_element.tag,
            long_name=long_name,
            description=description,
            is_visible_raw=None,
            parameters=parameters,
            byte_size=None,
            sdgs=sdgs,
        )
    elif et_element.tag == "STRUCTURE":
        byte_size_text = et_element.findtext("BYTE-SIZE")
        byte_size = int(byte_size_text) if byte_size_text is not None else None
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        res = Structure(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            is_visible_raw=is_visible_raw,
            parameters=parameters,
            byte_size=byte_size,
            sdgs=sdgs,
        )
    else:
        res = None
        logger.critical(f"Did not recognize structure {et_element.tag} {short_name}")
    return res
