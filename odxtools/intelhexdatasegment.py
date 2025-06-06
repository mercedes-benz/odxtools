# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .exceptions import odxassert


@dataclass(kw_only=True)
class IntelHexDataSegment:
    """This class represents a single line of binary data using the Intel-hex format."""
    payload_len: int
    load_offset: int
    segment_type: int
    payload: bytes
    checksum: int

    @staticmethod
    def from_string(data_str: str) -> "IntelHexDataSegment":
        i = 0
        segment_mark = data_str[i]
        i += 1
        odxassert(segment_mark == ":")

        payload_len = int(data_str[i:i + 2], 16)
        i += 2
        load_offset = int(data_str[i:i + 4], 16)
        i += 4
        segment_type = int(data_str[i:i + 2], 16)
        i += 2
        odxassert(0 <= segment_type and segment_type <= 5)
        payload = bytes.fromhex(data_str[i:i + payload_len * 2])
        i += payload_len * 2
        checksum = int(data_str[i:i + 2], 16)
        i += 2

        return IntelHexDataSegment(
            payload_len=payload_len,
            load_offset=load_offset,
            segment_type=segment_type,
            payload=payload,
            checksum=checksum,
        )

    def verify_checksum(self) -> bool:
        # bytewise sum of the whole segment. Since the checksum is the
        # two-complement of last byte of the remaining data, the last
        # byte of that sum must be zero
        tmp = 0
        tmp += self.payload_len
        tmp += self.load_offset & 0xff
        tmp += self.load_offset >> 8
        tmp += self.segment_type
        tmp += sum(self.payload)
        tmp += self.checksum

        return tmp & 0xff == 0

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
        if self.segment_type == 2:
            # extended segment address record: offset for the
            # following segmets shifted by 4 bits.
            odxassert(self.load_offset == 0)
            odxassert(len(self.payload) == 2)
            return int.from_bytes(self.payload, "big") << 4

        elif self.segment_type == 4:
            # extended linear address record: upper 16 bits of the
            # succeeding segments of a 32 bit dataset
            odxassert(self.load_offset == 0)
            odxassert(len(self.payload) == 2)
            return int.from_bytes(self.payload, "big") << 16

        elif self.segment_type != 0:
            # segment does not contain payload
            return base_address

        min_length = base_address + self.load_offset + self.payload_len
        if len(blob) < min_length:
            blob += b'\x00' * (min_length - len(blob))

        blob[base_address + self.load_offset:min_length] = self.payload

        return base_address
