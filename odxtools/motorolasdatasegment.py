# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .exceptions import odxassert, odxraise


@dataclass(kw_only=True)
class MotorolaSDataSegment:
    """This class represents a single line of binary data in the Motorola-S format.

    This file format is also known as SRECORD or SREC.
    """

    segment_type: int
    byte_count: int
    address: int
    payload: bytes
    checksum: int

    @staticmethod
    def from_string(data_str: str) -> "MotorolaSDataSegment":
        if data_str[0] != "S":
            odxraise("Specified invalid data record")
            return None

        i = 1
        segment_type = ord(data_str[i]) - ord('0')
        i += 1
        byte_count = int(data_str[i:i + 2], 16)
        i += 2

        if segment_type == 0:
            # header
            address = int(data_str[i:i + 4], 16)
            odxassert(address == 0x0)
            i += 4

            payload = bytes.fromhex(data_str[i:i + (byte_count - 3) * 2])
            i += (byte_count - 3) * 2
        elif segment_type == 1:
            # data (16 bit addresses)
            address = int(data_str[i:i + 4], 16)
            i += 4

            payload = bytes.fromhex(data_str[i:i + (byte_count - 3) * 2])
            i += (byte_count - 3) * 2
        elif segment_type == 2:
            # data (24 bit addresses)
            address = int(data_str[i:i + 6], 16)
            i += 6

            payload = bytes.fromhex(data_str[i:i + (byte_count - 3) * 2])
            i += (byte_count - 3) * 2
        elif segment_type == 3:
            # data (32 bit addresses)
            address = int(data_str[i:i + 8], 16)
            i += 8

            payload = bytes.fromhex(data_str[i:i + (byte_count - 3) * 2])
            i += (byte_count - 3) * 2

        elif segment_type == 5:
            # 16 bit record count
            address = int(data_str[i:i + 4], 16)
            i += 4

            odxassert(byte_count == 3)
            payload = bytes.fromhex(data_str[i:i + (byte_count - 3) * 2])
            i += (byte_count - 3) * 2

        elif segment_type == 5:
            # 24 bit record count
            address = int(data_str[i:i + 6], 16)
            i += 6

            odxassert(byte_count == 4)
            payload = bytes.fromhex(data_str[i:i + (byte_count - 4) * 2])
            i += (byte_count - 4) * 2

        elif segment_type == 6:
            # 32 bit record count
            address = int(data_str[i:i + 8], 16)
            i += 8

            odxassert(byte_count == 5)
            payload = bytes.fromhex(data_str[i:i + (byte_count - 5) * 2])
            i += (byte_count - 5) * 2

        elif segment_type == 7:
            # end of block (32 bit variant)
            odxassert(byte_count == 5)
            payload = b''
            address = int(data_str[i:i + (byte_count - 1) * 2], 16)
            i += (byte_count - 1) * 2

        elif segment_type == 8:
            # end of block (24 bit variant)
            odxassert(byte_count == 4)
            payload = b''
            address = int(data_str[i:i + (byte_count - 1) * 2], 16)
            i += (byte_count - 1) * 2

        elif segment_type == 9:
            # end of block (16 bit variant)
            odxassert(byte_count == 3)
            payload = b''
            address = int(data_str[i:i + (byte_count - 1) * 2], 16)
            i += (byte_count - 1) * 2

        else:
            odxraise(f"Unsupported MOTOROLA-S segment type ({segment_type})")

        checksum = int(data_str[i:i + 2], 16)
        i += 2

        odxassert(i == len(data_str))

        return MotorolaSDataSegment(
            segment_type=segment_type,
            byte_count=byte_count,
            address=address,
            payload=payload,
            checksum=checksum,
        )

    def verify_checksum(self) -> bool:
        # bytewise sum of the byte count, address and data
        tmp = 0
        tmp += self.byte_count
        tmp += sum(self.address.to_bytes(4, "big"))
        tmp += sum(self.payload)

        # one-complement
        tmp = 0xff - (tmp & 0xff)

        return tmp == self.checksum

    def dump_into(self, blob: bytearray, base_address: int) -> int:
        """Write the payload of the segment into a byte array object

        Be aware that this function does not deal with overlapping
        data segments, i.e., if such segments are present in the
        dataset, the result should be considered to be
        undefined. (Strictly speaking. In practice, data specified by
        later segments overwrites the data of preceeding ones.)

        :return: The base address that ought to be used for the
                 consecutive segments

        """

        if self.segment_type not in [1, 2, 3]:
            # the current segment does not represent data
            return base_address

        min_length = base_address + self.address + self.byte_count
        if len(blob) < min_length:
            blob += b'\x00' * (min_length - len(blob))

        blob[base_address + self.address:min_length] = self.payload

        return base_address
