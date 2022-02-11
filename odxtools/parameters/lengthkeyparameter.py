# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from ..encodestate import EncodeState

from .parameterwithdop import ParameterWithDOP


class LengthKeyParameter(ParameterWithDOP):
    """Length Keys specify the bit (!) length of another parameter.

    The other parameter references the length key parameter using a ParamLengthInfoType as .diag_coded_type.

    LengthKeyParameters are decoded the same as ValueParameters.
    The main difference to ValueParameters is that a LengthKeyParameter has an `.id` attribute
    and its DOP must be a simple DOP with PHYSICAL-TYPE/BASE-DATA-TYPE="A_UINT32".
    """

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

    def encode_into_pdu(self, encode_state: EncodeState) -> bytearray:
        physical_value = encode_state.parameter_values.get(self.short_name,)

        # TODO: Maybe it'd be nice if the length key value would default to the minimal needed length,
        #       instead of raising a TypeError here. But for that we'd
        #       (1) need to find the parameter that references this length key and determine its bit length
        #       and (2) make sure that we choose a length is a valid physical value for the DOP.
        #       (Restrictions may be e.g. multiple of 8 or 16, depending on the compu method.)
        if physical_value is None:
            raise TypeError(f"A value for the length key '{self.short_name}'"
                            f" must be specified.")

        # Set the value of the length key in the length key dict.
        encode_state.length_keys[self.id] = physical_value

        return super(ParameterWithDOP, self).encode_into_pdu(encode_state)
