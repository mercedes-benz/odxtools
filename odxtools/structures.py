# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

from odxtools.dataobjectproperty import DopBase
from .exceptions import DecodeError, EncodeError
from typing import Iterable, OrderedDict, Union
from .parameters import *
from .nameditemlist import NamedItemList

class BasicStructure(DopBase):
    def __init__(self,
                 id,
                 short_name,
                 parameters: Iterable[Parameter],
                 long_name=None,
                 byte_size=None,
                 description=None):
        super().__init__(id, short_name, long_name=long_name, description=description)
        self.parameters = NamedItemList(lambda par: par.short_name, parameters)

        self._byte_size = byte_size

    @property
    def bit_length(self):
        if self._byte_size:
            return 8 * self._byte_size
        elif all(p.bit_length is not None for p in self.parameters):
            return sum([p.bit_length for p in self.parameters])
        else:
            return None

    def coded_const_prefix(self, request_prefix: Union[bytes, bytearray] = bytes()):
        prefix = bytearray()
        for p in self.parameters:
            if isinstance(p, CodedConstParameter) and p.bit_length % 8 == 0:
                prefix = encode_parameter_value_into_pdu(prefix, p)
            else:
                break
        return prefix

    def get_required_parameters(self):
        return filter(lambda p: p.is_required(), self.parameters)

    def convert_physical_to_internal(self, param_values: dict):
        coded_message = bytearray()
        for param in sorted(self.parameters, key=lambda p: p.byte_position):
            coded_message = encode_parameter_value_into_pdu(coded_message,
                                                            param,
                                                            value=param_values.get(param.short_name))
        return coded_message

    def convert_physical_to_bytes(self, param_values: dict, bit_position=0):
        if bit_position != 0:
            raise EncodeError("Structures must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")
        coded_structure = self.convert_physical_to_internal(param_values)
        if self._byte_size is not None and len(coded_structure) > self._byte_size:
            # TODO
            logger.critical(
                f"The structure expected to be {self._byte_size} bytes long but encoding of parameters only needs {len(coded_structure)} bytes. How to extend length?")
        return coded_structure

    def convert_bytes_to_physical(self, byte_code: int, byte_position=0, bit_position=0):
        if bit_position != 0:
            raise DecodeError("Structures must be aligned, i.e. bit_position=0, but "
                              f"{self.short_name} was passed the bit position {bit_position}")
        byte_code = byte_code[byte_position:]
        param_dict = OrderedDict()
        next_byte_position = 0
        for parameter in self.parameters:
            param_value, byte_pos = parameter.decode_from_pdu(byte_code,
                                                              default_byte_position=next_byte_position)
            next_byte_position = max(next_byte_position, byte_pos)
            param_dict[parameter.short_name] = param_value
        return param_dict, byte_position + next_byte_position

    def encode(self, triggering_coded_request=None, **params) -> bytearray:
        """
        Composes an UDS message as bytes for this service.
        Parameters:
        ----------
        params: dict
            Parameters of the RPC as mapping from SHORT-NAME of the parameter to the value
        """
        logger.debug(f"{self.short_name} encode RPC with params={params}")

        coded_rpc = bytearray()
        bit_length = 0
        for param in self.parameters:
            param_name = param.short_name
            param_value = None

            if isinstance(param, CodedConstParameter):
                if param_name in params \
                   and params[param_name] != param.coded_value:
                    raise TypeError(f"The parameter '{param_name}' is constant {param.coded_value} and can thus not be changed.")
            elif isinstance(param, MatchingRequestParameter):
                if not triggering_coded_request:
                    raise TypeError(f"Parameter '{param_name}' is of matching request type, but no original request has been specified.")
            elif isinstance(param, ValueParameter):
                param_value = params.get(param_name, )
                if param_value is None:
                    param_value = param.physical_default_value

                if param_value is None:
                    raise TypeError(f"A value for parameter '{param_name}' must be specified as the parameter does not exhibit a default.")

            coded_rpc = encode_parameter_value_into_pdu(
                coded_rpc,
                triggering_coded_request=triggering_coded_request,
                parameter=param,
                value=param_value
            )

            # Compute expected length
            if bit_length is not None and param.bit_length is not None:
                bit_length = bit_length + param.bit_length
            else:
                bit_length = None
        # Assert that length is as expected
        if bit_length is not None:
            assert bit_length % 8 == 0, f"Length of coded structure is not divisible by 8, i.e. is not a full sequence of bytes."
            assert len(coded_rpc) == bit_length // 8, f"{self.short_name} can't encode: Actual length is {len(coded_rpc)}, computed byte length is {bit_length // 8}, \n" + '\n'.join(
                self.__message_format_lines())

        return bytearray(coded_rpc)

    def decode(self, message: Union[bytes, bytearray]):
        param_dict, next_byte_position = self.convert_bytes_to_physical(
            message)
        if len(message) != next_byte_position:
            raise DecodeError(
                f"The message {message.hex()} is longer than could be parsed. Expected {next_byte_position} but got {len(message)}.")
        return param_dict

    def parameter_dict(self):
        """
        Returns a dict with parameter short names as keys.
        The values are parameters for simple types or a nested dict for structures.
        """
        params = self.parameters
        assert all(not isinstance(p, ParameterWithDOP) or isinstance(
            p.dop, DataObjectProperty) or isinstance(p.dop, Structure) for p in self.parameters)
        param_dict = {
            p.short_name: p for p in params if not isinstance(p, ParameterWithDOP) or not isinstance(p.dop, BasicStructure)
        }
        param_dict.update({
            struct_param.short_name: struct_param.dop.parameter_dict()
            for struct_param in params if isinstance(struct_param, ParameterWithDOP) and isinstance(struct_param.dop, BasicStructure)
        })
        return param_dict

    def _resolve_references(self, parent_dl, id_lookup):
        """Recursively resolve any references (odxlinks or sn-refs)
        """
        for p in self.parameters:
            if isinstance(p, ParameterWithDOP):
                p.resolve_references(parent_dl, id_lookup)

    def __message_format_lines(self):
        # sort parameters
        sorted_params: list = list(self.parameters) # copy list
        if all(p.byte_position is not None for p in self.parameters):
            sorted_params.sort(key=lambda p: (
                p.byte_position, 8 - p.bit_position))

        # replace structure parameters by their sub parameters
        params = []
        for p in sorted_params:
            if isinstance(p, ValueParameter) and isinstance(p.dop, BasicStructure):
                params += p.dop.parameters
            else:
                params.append(p)

        i = 0
        byte = 0
        # needs to be one larger than the maximum digit length of a byte number
        indent_for_byte_numbering = 5 * " "
        formatted_lines = [indent_for_byte_numbering +
                           "".join(f"   {7-bit}  " for bit in range(8))]

        breakpoint = 0  # absolute bit position where the next parameter starts

        divide_string = indent_for_byte_numbering + 8 * "+-----" + "+"

        error = False
        next_line = ""
        while i <= len(params) and not error:  # For each byte
            if 8 * byte == breakpoint and i == len(params):
                # If we have formatted the last parameter, we're done.
                break

            formatted_lines.append(f"{divide_string}")
            if breakpoint // 8 - byte > 5:
                curr_param = params[i-1].short_name
                formatted_lines.append(
                    indent_for_byte_numbering + f"  ... {breakpoint // 8 - byte} bytes belonging to {curr_param} ... ")
                byte += breakpoint // 8 - byte
                continue

            next_line = f"{(len(indent_for_byte_numbering) - 1 - len(str(byte))) * ' '}{byte} "

            for bit in range(8):
                assert 8 * byte + bit <= breakpoint

                if 8 * byte + bit == breakpoint:
                    # END-OF-PDU fields do not exhibit a fixed bit
                    # length, so they need special treatment here
                    dct = None
                    if hasattr(params[i], 'dop'):
                        dop = params[i].dop
                        if hasattr(dop, 'diag_coded_type'):
                            dct = dop.diag_coded_type

                    if dct is not None and dct.dct_type == 'MIN-MAX-LENGTH-TYPE':
                        name = params[i].short_name + " ("
                        if dct.termination == "END-OF-PDU":
                            name += "End of PDU, "
                        name += f"{dct.min_length}..{dct.max_length} bytes"
                        name += ")"
                        next_line += "| " + name

                        i += 1

                        # adding 8 is is a bit hacky here, but hey, it
                        # works ...
                        breakpoint += 8

                        break

                    elif not params[i].bit_length:
                        # The bit length is not set for the current
                        # parameter, i.e. it was either not specified
                        # or the parameter is of variable length and
                        # has an type which is not handled above. In
                        # this case, stop trying.
                        error = True
                        break
                    else:
                        breakpoint += params[i].bit_length
                        name = params[i].short_name + \
                            f" ({params[i].bit_length} bits)"
                        next_line += "| " + name

                    i += 1

                    if byte == breakpoint // 8:
                        char_pos = bit * 6 + 2 + len(name)
                        width_of_line = (breakpoint % 8) * 6
                        if char_pos < width_of_line:
                            next_line += " " * \
                                (width_of_line - char_pos) + "|"
                        # start next line (belongs to same byte)
                        formatted_lines.append(next_line)
                        # fill next line with white spaces upto the bit where next parameter starts
                        next_line = indent_for_byte_numbering + \
                            (bit + 1) * 6 * " "
                    else:
                        char_pos = 2 + bit * 6 + len(name)
                        width_of_line = 8 * 6
                        if char_pos < width_of_line:
                            next_line += " " * \
                                (width_of_line - char_pos) + "|"
                        break
                else:
                    if bit == 0:
                        next_line += "|" + 5 * " "
                    elif bit == 7:
                        next_line += 6 * " " + "|"
                    else:
                        next_line += 6 * " "

            formatted_lines.append(next_line)
            next_line = ""

            byte += 1

        if not error:
            formatted_lines.append(divide_string)
            return formatted_lines
        else:
            return None

    def print_message_format(self, indent: int = 5):
        """
        Print a description of the message format to `stdout`.
        """

        message_as_lines = self.__message_format_lines()
        if message_as_lines is not None:
            print(f"{indent * ' '}" +
                  f"\n{indent * ' '}".join(message_as_lines))
        else:
            print("Sorry, couldn't pretty print message layout. :(")
        for p in self.parameters:
            print(indent * ' ' +
                  str(p).replace("\n", f"\n{indent * ' '}"))


class Structure(BasicStructure):
    def __init__(self, id, short_name, parameters, long_name=None, byte_size=None, description=None):
        super().__init__(id, short_name, parameters,
                         long_name=long_name, description=description)

        self.parameters = parameters
        self.basic_structure = BasicStructure(id, short_name, parameters,
                                              long_name=long_name, byte_size=byte_size, description=description)

    def __repr__(self) -> str:
        return f"Structure('{self.short_name}', byte_size={self._byte_size})"

    def __str__(self) -> str:
        params = "[\n" + "\n".join([" " + str(p).replace("\n", "\n ")
                                   for p in self.parameters]) + "\n]"

        return \
            f"Structure '{self.short_name}': " + \
            f"Byte size={self._byte_size}, " + \
            f"Parameters={params}"


class Request(BasicStructure):
    def __init__(self, id, short_name, parameters, long_name=None, description=None):
        super().__init__(id, short_name, parameters,
                         long_name=long_name, description=description)

    def __repr__(self) -> str:
        return f"Request('{self.short_name}')"

    def __str__(self) -> str:
        return f"Request('{self.short_name}')"


class Response(BasicStructure):
    def __init__(self, id, short_name, parameters, long_name=None, response_type=None, description=None):
        super().__init__(id, short_name, parameters,
                         long_name=long_name, description=description)
        self.response_type = "POS-RESPONSE" if response_type == "POS-RESPONSE" else "NEG-RESPONSE"

    def encode(self, coded_request: bytearray = None, **params):
        logger.info(f"Compose response message to the request {coded_request}")
        if coded_request is not None:
            # Extract MATCHING-REQUEST-PARAMs from the coded request
            for param in self.parameters:
                if param.parameter_type == "MATCHING-REQUEST-PARAM":
                    logger.info(
                        f"set matching request param value {param.short_name}")
                    byte_pos = param.request_byte_position
                    byte_length = param.byte_length

                    val = coded_request[byte_pos:byte_pos+byte_length]
                    params[param.short_name] = val

        return super().encode(triggering_coded_request=coded_request, **params)

    def __repr__(self) -> str:
        return f"Response('{self.short_name}')"

    def __str__(self) -> str:
        return f"Response('{self.short_name}')"


def read_structure_from_odx(et_element):
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME").text
    description = read_description_from_odx(et_element.find("DESC"))
    parameters = [read_parameter_from_odx(et_parameter)
                  for et_parameter in et_element.iterfind("PARAMS/PARAM")]

    if et_element.tag == "REQUEST":
        res = Request(
            id,
            short_name,
            parameters=parameters,
            long_name=long_name,
            description=description
        )
    elif et_element.tag in ["POS-RESPONSE", "NEG-RESPONSE"]:
        res = Response(
            id,
            short_name,
            parameters=parameters,
            long_name=long_name,
            description=description
        )
    elif et_element.tag == "STRUCTURE":
        byte_size = int(et_element.find(
            "BYTE-SIZE").text) if et_element.find("BYTE-SIZE") is not None else None
        res = Structure(
            id,
            short_name,
            parameters=parameters,
            byte_size=byte_size,
            long_name=long_name,
            description=description
        )
    else:
        res = None
        logger.critical(
            f"Did not recognize structure {et_element.tag} {short_name}")
    return res
