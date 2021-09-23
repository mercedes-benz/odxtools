# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import abc
from odxtools.utils import read_description_from_odx
from odxtools.exceptions import DecodeError
from typing import Union

from .diagcodedtypes import DiagCodedType, read_diag_coded_type_from_odx
from .dataobjectproperty import DataObjectProperty, DopBase
from .globals import xsi, logger
from .odxtypes import ODX_TYPE_PARSER


class Parameter(abc.ABC):
    def __init__(self,
                 short_name,
                 parameter_type,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        self.short_name = short_name
        self.long_name = long_name
        self.byte_position = byte_position
        self.bit_position = bit_position
        self.parameter_type = parameter_type
        self.semantic = semantic
        self.description = description

    @property
    def bit_length(self):
        return None

    @abc.abstractclassmethod
    def is_required(self):
        pass

    @abc.abstractclassmethod
    def is_optional(self):
        pass

    @abc.abstractclassmethod
    def get_coded_value(self):
        pass

    @abc.abstractclassmethod
    def get_coded_value_as_bytes(self):
        pass

    @abc.abstractclassmethod
    def decode_from_pdu(self, coded_message, default_byte_position=None):
        """Decode the parameter value from the coded message.

        If the paramter does have a byte position property, the coded bytes the parameter covers are extracted
        at this byte position and the function parameter `default_byte_position` is ignored.

        If the parameter does not have a byte position and a byte position is passed,
        the bytes are extracted at the byte position given by the argument `default_byte_position`.

        If the parameter does not have a byte position and the argument `default_byte_position` is None,
        this function throws a `DecodeError`.

        Parameters
        ----------
        coded_message : bytes or bytearray
            the coded message
        default_byte_position : int or None
            Byte position used iff the parameter does not have a byte position in the .odx

        Returns
        -------
        str or int or bytes or bytearray or dict
            the decoded parameter value (the type is defined by the DOP)
        int
            the next byte position after the extracted parameter
        """
        pass

    def _as_dict(self):
        """
        Mostly for pretty printing purposes (specifically not for reconstructing the object)
        """
        d = {
            'short_name': self.short_name,
            'type': self.parameter_type,
            'semantic': self.semantic
        }
        if self.byte_position is not None:
            d['byte_position'] = self.byte_position
        if self.bit_position:
            d['bit_position'] = self.bit_position
        return d

    def __repr__(self):
        repr_str = f"Parameter(parameter_type='{self.parameter_type}', short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        # create list of all parameters. 'short_name' ought to be
        # first, so it needs special treatment...
        param_descs = [f"short_name='{self.short_name}'"]
        for (key, val) in self._as_dict().items():
            if key == "short_name":
                continue
            elif isinstance(val, str):
                param_descs.append(f"{key}='{val}'")
            else:
                param_descs.append(f"{key}={val}")

        return f"Parameter({', '.join(param_descs)})"


class ParameterWithDOP(Parameter):
    def __init__(self,
                 short_name,
                 parameter_type,
                 dop=None,
                 dop_ref=None,
                 dop_snref=None,
                 **kwargs):
        super().__init__(short_name, parameter_type, **kwargs)
        self.dop_ref = dop_ref
        self.dop_snref = dop_snref

        self._dop = dop
        if dop and not dop_ref and not dop_snref:
            self.dop_ref = dop.id
        assert self.dop_ref or self.dop_snref

    @property
    def dop(self) -> Union[DopBase, None]:
        """may be a DataObjectProperty, a Structure or None"""
        return self._dop

    @dop.setter
    def dop(self, dop: DopBase):
        self._dop = dop
        if not self.dop_snref:
            self.dop_ref = dop.id
        else:
            self.dop_snref = dop.short_name

    def resolve_references(self, parent_dl, id_lookup):
        dop = self.dop
        if self.dop_snref:
            dop = parent_dl.data_object_properties[self.dop_snref]
            if not dop:
                logger.info(f"Could not resolve DOP-SNREF {self.dop_snref}")
        elif self.dop_ref:
            dop = id_lookup.get(self.dop_ref)
            if not dop:
                logger.info(f"Could not resolve DOP-REF {self.dop_ref}")
        else:
            logger.warn(f"Parameter without DOP-(SN)REF should not exist!")
        if self.dop and dop != self.dop:
            logger.warn(f"Reference and DOP are inconsistent!")

        self._dop = dop

    @property
    def bit_length(self):
        if self.dop is not None:
            return self.dop.bit_length
        else:
            return None

    @property
    def physical_data_type(self):
        return self.dop.physical_data_type

    def get_coded_value(self, physical_value=None):
        return self.dop.convert_physical_to_internal(physical_value)

    def get_coded_value_as_bytes(self, physical_value):
        return self.dop.convert_physical_to_bytes(physical_value, bit_position=self.bit_position)

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        byte_position = self.byte_position if self.byte_position is not None else default_byte_position
        # Use DOP to decode
        phys_val, next_byte_pos = self.dop.convert_bytes_to_physical(
            coded_message, byte_position=byte_position, bit_position=self.bit_position)
        return phys_val, next_byte_pos

    def _as_dict(self):
        d = super()._as_dict()
        if self.dop is not None:
            if self.bit_length is not None:
                d["bit_length"] = self.bit_length
            d["dop_ref"] = self.dop.id
        elif self.dop_ref is not None:
            d["dop_ref"] = self.dop_ref
        elif self.dop_snref is not None:
            d["dop_snref"] = self.dop_snref

        return d

    def __str__(self):
        lines = [
            super().__str__(),
            " " + str(self.dop).replace("\n", "\n ")
        ]
        return "\n".join(lines)


class CodedConstParameter(Parameter):
    def __init__(self, short_name, diag_coded_type: DiagCodedType, coded_value, **kwargs):
        super().__init__(short_name,
                         parameter_type="CODED-CONST", **kwargs)

        self._diag_coded_type = diag_coded_type
        assert isinstance(coded_value, int)
        self.coded_value = coded_value

    @property
    def diag_coded_type(self):
        return self._diag_coded_type

    @property
    def bit_length(self):
        return self.diag_coded_type.bit_length

    @property
    def internal_data_type(self):
        return self.diag_coded_type.base_data_type

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return self.coded_value

    def get_coded_value_as_bytes(self):
        return self.diag_coded_type.convert_internal_to_bytes(self.coded_value, bit_position=self.bit_position)

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        # Extract coded values
        byte_position = self.byte_position if self.byte_position is not None else default_byte_position
        coded_val, next_byte_pos = self.diag_coded_type.convert_bytes_to_internal(coded_message,
                                                                                  byte_position=byte_position,
                                                                                  bit_position=self.bit_position)

        # Check if the coded value in the message is correct.
        if self.coded_value != coded_val:
            raise DecodeError(
                f"Coded constant parameter does not match! "
                f"The parameter {self.short_name} expected coded value {self.coded_value} but got {coded_val} "
                f"at byte position {self.byte_position if self.byte_position is not None else default_byte_position} "
                f"in coded message {coded_message.hex()}."
            )
        return self.coded_value, next_byte_pos

    def _as_dict(self):
        d = super()._as_dict()
        if self.bit_length is not None:
            d["bit_length"] = self.bit_length
        d["coded_value"] = hex(self.coded_value)
        return d

    def __repr__(self):
        repr_str = f"CodedConstParameter(short_name='{self.short_name}', coded_value={self.coded_value}"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        repr_str += f", diag_coded_type={repr(self.diag_coded_type)}"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        lines = [
            super().__str__(),
        ]
        return "\n".join(lines)

    def get_description_of_valid_values(self) -> str:
        """return a human-understandable description of valid physical values"""
        return f"Constant internal value: {self.coded_value}"


class PhysicalConstantParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 physical_constant_value,
                 **kwargs):
        super().__init__(short_name, parameter_type="PHYS-CONST",
                         **kwargs)
        assert physical_constant_value is not None
        self._physical_constant_value = physical_constant_value

    @property
    def physical_constant_value(self):
        # Cast to physical type
        return ODX_TYPE_PARSER[self.dop.physical_data_type](self._physical_constant_value)

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return self.dop.convert_physical_to_internal(self.physical_constant_value)

    def get_coded_value_as_bytes(self):
        return super().get_coded_value_as_bytes(self.physical_constant_value)

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        phys_val, next_byte_pos = super().decode_from_pdu(
            coded_message, default_byte_position=default_byte_position)

        if phys_val != self.physical_constant_value:
            raise DecodeError(
                f"Physical constant parameter does not match! "
                f"The parameter {self.short_name} expected physical value {self.physical_constant_value} but got {phys_val} "
                f"at byte position {self.byte_position if self.byte_position is not None else default_byte_position} "
                f"in coded message {coded_message.hex()}."
            )
        return phys_val, next_byte_pos

    def __repr__(self):
        repr_str = f"CodedConstParameter(short_name='{self.short_name}', coded_value={self.coded_value}"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        repr_str += f", diag_coded_type={repr(self.diag_coded_type)}"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"


class ReservedParameter(Parameter):
    def __init__(self,
                 short_name,
                 bit_length,
                 **kwargs):
        super().__init__(short_name,
                         parameter_type="RESERVED",
                         **kwargs)
        self._bit_length = bit_length

    @property
    def bit_length(self):
        return self._bit_length

    def is_required(self):
        return False

    def is_optional(self):
        return False

    def get_coded_value(self):
        return 0

    def get_coded_value_as_bytes(self):
        return int(0).to_bytes((self.bit_length + self.bit_position + 7) // 8, "big")

    def decode_from_pdu(self, coded_message, default_byte_position=None):

        byte_position = self.byte_position if self.byte_position is not None else default_byte_position
        byte_length = (self.bit_length + self.bit_position + 7) // 8
        val_as_bytes = coded_message[byte_position:byte_position+byte_length]
        next_byte_pos = byte_position + byte_length

        # Check that reserved bits are 0
        expected = sum(2**i for i in range(self.bit_position,
                       self.bit_position + self.bit_length))
        actual = int.from_bytes(val_as_bytes, "big")

        # Bit-wise compare if reserved bits are 0.
        if expected & actual != 0:
            raise DecodeError(
                f"Reserved bits must be Zero! "
                f"The parameter {self.short_name} expected {self.bit_length} bits to be Zero starting at bit position {self.bit_position} "
                f"at byte position {self.byte_position if self.byte_position is not None else default_byte_position} "
                f"in coded message {coded_message.hex()}."
            )
        return None, next_byte_pos

    def __repr__(self):
        repr_str = f"ReservedParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.bit_length is not None:
            repr_str += f", bit_length='{self.bit_length}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"


class ValueParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 physical_default_value=None,
                 dop_ref=None,
                 dop_snref=None,
                 **kwargs):
        super().__init__(short_name,
                         parameter_type="VALUE",
                         dop_ref=dop_ref,
                         dop_snref=dop_snref,
                         **kwargs)
        # _physical_default_value is a string. Conversion to actual type must happen after parsing
        self._physical_default_value = physical_default_value

    @property
    def physical_default_value(self):
        if self._physical_default_value is None:
            return None
        else:
            return ODX_TYPE_PARSER[self.dop.physical_data_type](self._physical_default_value)

    def is_required(self):
        return True if self.physical_default_value is None else False

    def is_optional(self):
        return True if self._physical_default_value is not None else False

    def get_coded_value(self, physical_value=None):
        if physical_value is not None:
            return self.dop.convert_physical_to_internal(physical_value)
        else:
            return self.dop.convert_physical_to_internal(self.physical_default_value)

    def get_coded_value_as_bytes(self, physical_value=None):
        if physical_value is not None:
            return self.dop.convert_physical_to_bytes(physical_value, bit_position=self.bit_position)
        else:
            return self.dop.convert_physical_to_bytes(self.physical_default_value, bit_position=self.bit_position)

    def get_valid_physical_values(self):
        if isinstance(self.dop, DataObjectProperty):
            return self.dop.get_valid_physical_values()

    def __repr__(self):
        repr_str = f"ValueParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.physical_default_value is not None:
            repr_str += f", physical_default_value='{self.physical_default_value}'"
        if self.dop_ref is not None:
            repr_str += f", dop_ref='{self.dop_ref}'"
        if self.dop_snref is not None:
            repr_str += f", dop_snref='{self.dop_snref}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"


class MatchingRequestParameter(Parameter):
    def __init__(self,
                 short_name,
                 request_byte_position,
                 byte_length,
                 **kwargs):
        super().__init__(short_name,
                         parameter_type="MATCHING-REQUEST-PARAM",
                         **kwargs)
        assert byte_length is not None
        assert request_byte_position is not None
        self.request_byte_position = request_byte_position
        self._byte_length = byte_length

    @property
    def bit_length(self):
        return 8 * self._byte_length

    @property
    def byte_length(self):
        return self._byte_length

    def is_required(self):
        return True

    def is_optional(self):
        return False

    def get_coded_value(self, request_value=None):
        return request_value

    def get_coded_value_as_bytes(self, request_value=None):
        return bytearray(request_value)

    def decode_from_pdu(self, coded_message, default_byte_position=None):

        byte_position = self.byte_position if self.byte_position is not None else default_byte_position
        byte_length = (self.bit_length + self.bit_position + 7) // 8
        val_as_bytes = coded_message[byte_position:byte_position+byte_length]
        next_byte_pos = byte_position + byte_length

        return val_as_bytes, next_byte_pos

    def __repr__(self):
        repr_str = f"ValueParameter(short_name='{self.short_name}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.request_byte_position is not None:
            repr_str += f", request_byte_position='{self.request_byte_position}'"
        if self.byte_length is not None:
            repr_str += f", byte_length='{self.byte_length}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"

    def __str__(self):
        return super().__str__() + f"\n Request byte position = {self.request_byte_position}, byte length = {self._byte_length}"


class SystemParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 sysparam,
                 dop_ref=None,
                 dop_snref=None,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(short_name,
                         parameter_type="SYSTEM",
                         dop_ref=dop_ref,
                         dop_snref=dop_snref,
                         long_name=long_name,
                         byte_position=byte_position,
                         bit_position=bit_position,
                         semantic=semantic,
                         description=description)
        self.sysparam = sysparam

    def is_required(self):
        raise NotImplementedError(
            "SystemParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "SystemParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a SystemParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a SystemParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a SystemParameter is not implemented yet.")

    def __repr__(self):
        repr_str = f"SystemParameter(short_name='{self.short_name}', sysparam='{self.sysparam}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.dop_ref is not None:
            repr_str += f", dop_ref='{self.dop_ref}'"
        if self.dop_snref is not None:
            repr_str += f", dop_snref='{self.dop_snref}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"


class LengthKeyParameter(ParameterWithDOP):
    def __init__(self,
                 short_name,
                 id,
                 dop_ref=None,
                 dop_snref=None,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(short_name,
                         parameter_type="LENGTH-KEY",
                         dop_ref=dop_ref,
                         dop_snref=dop_snref,
                         long_name=long_name,
                         byte_position=byte_position,
                         bit_position=bit_position,
                         semantic=semantic,
                         description=description)
        self.id = id

    def is_required(self):
        raise NotImplementedError(
            "LengthKeyParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "LengthKeyParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a LengthKeyParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a LengthKeyParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a LengthKeyParameter is not implemented yet.")


class DynamicParameter(Parameter):
    def __init__(self,
                 short_name,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(
            short_name=short_name,
            long_name=long_name,
            byte_position=byte_position,
            bit_position=bit_position,
            parameter_type="DYNAMIC",
            semantic=semantic,
            description=description
        )

    def is_required(self):
        raise NotImplementedError(
            "DynamicParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "DynamicParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a DynamicParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a DynamicParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a DynamicParameter is not implemented yet.")

    def __repr__(self):
        repr_str = f"DynamicParameter(short_name='{self.short_name}', sysparam='{self.sysparam}'"
        if self.long_name is not None:
            repr_str += f", long_name='{self.long_name}'"
        if self.byte_position is not None:
            repr_str += f", byte_position='{self.byte_position}'"
        if self.bit_position:
            repr_str += f", bit_position='{self.bit_position}'"
        if self.semantic is not None:
            repr_str += f", semantic='{self.semantic}'"
        if self.description is not None:
            repr_str += f", description='{' '.join(self.description.split())}'"
        return repr_str + ")"


class TableStructParameter(Parameter):
    def __init__(self,
                 short_name,
                 table_key_ref=None,
                 table_key_snref=None,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(
            short_name=short_name,
            long_name=long_name,
            byte_position=byte_position,
            bit_position=bit_position,
            parameter_type="TABLE-STRUCT",
            semantic=semantic,
            description=description
        )
        if table_key_ref:
            self.table_key_ref = table_key_ref
        elif table_key_snref:
            self.table_key_snref = table_key_snref
        else:
            raise ValueError(
                "Either table_key_ref or table_key_snref must be defined.")

    def is_required(self):
        raise NotImplementedError(
            "TableStructParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "TableStructParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a TableStructParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a TableStructParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a TableStructParameter is not implemented yet.")


class TableKeyParameter(Parameter):
    def __init__(self,
                 short_name,
                 table_ref=None,
                 table_snref=None,
                 table_row_snref=None,
                 table_row_ref=None,
                 id=None,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(
            short_name=short_name,
            long_name=long_name,
            byte_position=byte_position,
            bit_position=bit_position,
            parameter_type="TABLE-KEY",
            semantic=semantic,
            description=description
        )
        if table_ref:
            self.table_ref = table_ref
            self.table_row_snref = table_row_snref
        elif table_snref:
            self.table_ref = table_ref
            self.table_row_snref = table_row_snref
        elif table_row_ref:
            self.table_row_ref = table_row_ref
        else:
            raise ValueError(
                "Either table_key_ref or table_key_snref must be defined.")
        self.id = id

    def is_required(self):
        raise NotImplementedError(
            "TableKeyParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "TableKeyParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a TableKeyParameter is not implemented yet.")


class TableEntryParameter(Parameter):
    def __init__(self,
                 short_name,
                 target,
                 table_row_ref,
                 long_name=None,
                 byte_position=None,
                 bit_position=0,
                 semantic=None,
                 description=None):
        super().__init__(
            short_name=short_name,
            long_name=long_name,
            byte_position=byte_position,
            bit_position=bit_position,
            parameter_type="TABLE-ENTRY",
            semantic=semantic,
            description=description
        )
        assert target in ["KEY", "STRUCT"]
        self.target = target
        self.table_row_ref = table_row_ref

    def is_required(self):
        raise NotImplementedError(
            "TableKeyParameter.is_required is not implemented yet.")

    def is_optional(self):
        raise NotImplementedError(
            "TableKeyParameter.is_optional is not implemented yet.")

    def get_coded_value(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def get_coded_value_as_bytes(self):
        raise NotImplementedError(
            "Encoding a TableKeyParameter is not implemented yet.")

    def decode_from_pdu(self, coded_message, default_byte_position=None):
        raise NotImplementedError(
            "Decoding a TableKeyParameter is not implemented yet.")


def read_parameter_from_odx(et_element):
    short_name = et_element.find("SHORT-NAME").text

    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    semantic = et_element.get("SEMANTIC")

    description = read_description_from_odx(et_element.find("DESC"))

    byte_position = int(et_element.find(
        "BYTE-POSITION").text) if et_element.find("BYTE-POSITION") is not None else None
    bit_position = int(et_element.find(
        "BIT-POSITION").text) if et_element.find("BIT-POSITION") is not None else 0

    parameter_type = et_element.get(f"{xsi}type")

    # Which attributes are set depends on the type of the parameter.
    if parameter_type in ["VALUE", "PHYS-CONST", "SYSTEM", "LENGTH-KEY"]:
        dop_ref = et_element.find(
            "DOP-REF").get("ID-REF") if et_element.find("DOP-REF") is not None else None
        dop_snref = et_element.find(
            "DOP-SNREF").get("SHORT-NAME") if et_element.find("DOP-SNREF") is not None else None

        if dop_ref is None and dop_snref is None:
            raise ValueError(
                f"A parameter of type {parameter_type} must reference a DOP! {dop_ref}, {dop_snref}")

    if parameter_type == "VALUE":
        physical_default_value = et_element.find("PHYSICAL-DEFAULT-VALUE").text \
            if et_element.find("PHYSICAL-DEFAULT-VALUE") is not None else None

        return ValueParameter(short_name=short_name,
                              long_name=long_name,
                              semantic=semantic,
                              byte_position=byte_position,
                              bit_position=bit_position,
                              dop_ref=dop_ref,
                              dop_snref=dop_snref,
                              physical_default_value=physical_default_value,
                              description=description)

    elif parameter_type == "PHYS-CONST":
        physical_constant_value = et_element.find(
            "PHYS-CONSTANT-VALUE").text

        return PhysicalConstantParameter(short_name,
                                         long_name=long_name,
                                         semantic=semantic,
                                         byte_position=byte_position,
                                         bit_position=bit_position,
                                         dop_ref=dop_ref,
                                         dop_snref=dop_snref,
                                         physical_constant_value=physical_constant_value,
                                         description=description)

    elif parameter_type == "CODED-CONST":
        diag_coded_type = read_diag_coded_type_from_odx(
            et_element.find("DIAG-CODED-TYPE"))
        coded_value = ODX_TYPE_PARSER[diag_coded_type.base_data_type](
            et_element.find("CODED-VALUE").text)

        return CodedConstParameter(short_name,
                                   long_name=long_name,
                                   semantic=semantic,
                                   diag_coded_type=diag_coded_type,
                                   coded_value=coded_value,
                                   byte_position=byte_position,
                                   bit_position=bit_position,
                                   description=description)

    elif parameter_type == "RESERVED":
        bit_length = int(et_element.find("BIT-LENGTH").text)

        return ReservedParameter(short_name,
                                 long_name=long_name,
                                 semantic=semantic,
                                 byte_position=byte_position,
                                 bit_position=bit_position,
                                 bit_length=bit_length,
                                 description=description)

    elif parameter_type == "MATCHING-REQUEST-PARAM":
        byte_length = int(et_element.find("BYTE-LENGTH").text)
        request_byte_pos = int(
            et_element.find("REQUEST-BYTE-POS").text)

        return MatchingRequestParameter(short_name,
                                        long_name=long_name,
                                        semantic=semantic,
                                        byte_position=byte_position, bit_position=bit_position,
                                        request_byte_position=request_byte_pos, byte_length=byte_length,
                                        description=description)

    elif parameter_type == "SYSTEM":
        sysparam = et_element.get("SYSPARAM")

        return SystemParameter(short_name=short_name,
                               sysparam=sysparam,
                               long_name=long_name,
                               semantic=semantic,
                               byte_position=byte_position,
                               bit_position=bit_position,
                               dop_ref=dop_ref,
                               dop_snref=dop_snref,
                               description=description)

    elif parameter_type == "LENGTH-KEY":
        id = et_element.get("ID")

        return LengthKeyParameter(short_name=short_name,
                                  id=id,
                                  long_name=long_name,
                                  semantic=semantic,
                                  byte_position=byte_position,
                                  bit_position=bit_position,
                                  dop_ref=dop_ref,
                                  dop_snref=dop_snref,
                                  description=description)

    elif parameter_type == "DYNAMIC":

        return DynamicParameter(short_name=short_name,
                                long_name=long_name,
                                semantic=semantic,
                                byte_position=byte_position,
                                bit_position=bit_position,
                                description=description)

    elif parameter_type == "TABLE-STRUCT":
        key_ref = et_element.find(
            "TABLE-KEY-REF").get("ID-REF") if et_element.find("TABLE-KEY-REF") is not None else None
        key_snref = et_element.find(
            "TABLE-KEY-SNREF").get("SHORT-NAME") if et_element.find("TABLE-KEY-SNREF") is not None else None
        return TableStructParameter(short_name=short_name,
                                    table_key_ref=key_ref,
                                    table_key_snref=key_snref,
                                    long_name=long_name,
                                    semantic=semantic,
                                    byte_position=byte_position,
                                    bit_position=bit_position,
                                    description=description)

    elif parameter_type == "TABLE-KEY":

        table_ref = et_element.find(
            "TABLE-REF").get("ID-REF") if et_element.find("TABLE-REF") is not None else None
        table_snref = et_element.find(
            "TABLE-SNREF").get("SHORT-NAME") if et_element.find("TABLE-SNREF") is not None else None
        row_snref = et_element.find(
            "TABLE-ROW-SNREF").get("SHORT-NAME") if et_element.find("TABLE-ROW-SNREF") is not None else None
        row_ref = et_element.find(
            "TABLE-ROW-REF").get("ID-REF") if et_element.find("TABLE-ROW-REF") is not None else None

        return TableKeyParameter(short_name=short_name,
                                 table_ref=table_ref,
                                 table_snref=table_snref,
                                 table_row_snref=row_snref,
                                 table_row_ref=row_ref,
                                 long_name=long_name,
                                 semantic=semantic,
                                 byte_position=byte_position,
                                 bit_position=bit_position,
                                 description=description)

    elif parameter_type == "TABLE-ENTRY":
        target = et_element.find("TARGET").text
        table_row_ref = et_element.find("TABLE-ROW-REF").get("ID-REF")

        return TableEntryParameter(short_name=short_name,
                                   target=target,
                                   table_row_ref=table_row_ref,
                                   long_name=long_name,
                                   byte_position=byte_position,
                                   bit_position=bit_position,
                                   semantic=semantic,
                                   description=description)

    raise NotImplementedError(f"I don't know the type {parameter_type}")


def _insert_byte_value_into(coded_rpc, byte_value, byte_position: int, debug_info=None):
    new_rpc = bytearray(coded_rpc)

    assert byte_position is not None

    min_length = byte_position + len(byte_value)
    if len(coded_rpc) < min_length:
        # Make byte code longer if necessary
        new_rpc += bytearray([0] * (min_length - len(coded_rpc)))
    for byte_idx_val, byte_idx_rpc in enumerate(range(byte_position, byte_position + len(byte_value))):
        # insert byte value
        assert new_rpc[byte_idx_rpc] & byte_value[byte_idx_val] == 0, "Bytes are already set!"
        new_rpc[byte_idx_rpc] |= byte_value[byte_idx_val]
    logger.info(f"Insert at byte pos {byte_position}")
    return new_rpc


def _get_coded_value_as_bytes_for_parameter(parameter: Parameter, value=None, bit_length=None, triggering_coded_request : bytearray = None, debug_info=None):
    if parameter.parameter_type in ["CODED-CONST", "PHYS-CONST", "RESERVED"]:
        coded_value = parameter.get_coded_value_as_bytes()
        assert isinstance(coded_value, (bytes, bytearray)
                          ), f"{parameter.parameter_type} parameter {parameter.short_name} encoded None"
    elif parameter.parameter_type in ["VALUE"]:
        coded_value = parameter.get_coded_value_as_bytes(physical_value=value)
    elif parameter.parameter_type in ["MATCHING-REQUEST-PARAM"]:
        if triggering_coded_request is None:
            raise TypeError(f"Parameter {parameter.short_name} is of type {parameter.parameter_type}, but no coded triggering request has been specified")
        logger.info(
            f"Parameter {parameter.short_name} of type {parameter.parameter_type} is given the coded value {value}")
        rbp = parameter.request_byte_position
        plen = parameter.byte_length
        coded_value = bytes(triggering_coded_request[rbp:rbp+plen])
    else:
        logger.warning(
            f"Coding for parameter {parameter.short_name} of type {parameter.parameter_type} is not implemented. Debug info: {debug_info}")
        coded_value = 0
    return coded_value


def encode_parameter_value_into_pdu(coded_rpc, parameter: Parameter, value=None, byte_position=None, triggering_coded_request=None, debug_info=None):
    """Insert the encoded value of a parameter into the coded RPC.

    If the byte position of the parameter is not defined, the byte code is appended to the coded RPC.

    Parameters:
    ----------
    coded_rpc
    parameter
    value: int | str | bytes
        physical value of the parameter if the parameter type is VALUE else coded value from the request if it is MATCHING-REQUEST-PARAM
    bit_length: int
        bit length of the coded value. Required if the parameter "does not know it itself" (i.e. for a parameter with variable length)
    """
    assert isinstance(coded_rpc, (bytes, bytearray, list))
    logger.debug(
        f"insert_parameter_value_to({coded_rpc}, parameter={parameter.short_name}, phys_val={value})")

    if byte_position is None:
        if parameter.byte_position is not None:
            byte_position = parameter.byte_position
        else:
            byte_position = len(coded_rpc)

    byte_value = _get_coded_value_as_bytes_for_parameter(
        parameter, value=value, triggering_coded_request=triggering_coded_request, debug_info=debug_info)
    logger.debug(
        f"Parameter {parameter.short_name} inserting coded value {byte_value.hex()}")
    debug_info = str(debug_info) + \
        f", Parameter {parameter.short_name} of type {parameter.parameter_type}"
    return _insert_byte_value_into(coded_rpc,
                                   byte_value,
                                   byte_position=byte_position,
                                   debug_info=None)
