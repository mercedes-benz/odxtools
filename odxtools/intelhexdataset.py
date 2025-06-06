# SPDX-License-Identifier: MIT
import re
from dataclasses import dataclass

from .exceptions import odxassert
from .intelhexdatasegment import IntelHexDataSegment


@dataclass(kw_only=True)
class IntelHexDataSet:
    """This class represents a full data set of binary data using the Intel-hex format."""
    segments: list[IntelHexDataSegment]

    @property
    def start_address(self) -> int | None:
        is_8bit = True
        for segment in self.segments:
            if segment.segment_type not in (0, 1):
                is_8bit = False

            if segment.segment_type == 3:
                # start segment address record. Note that this record
                # type is functionally identical to the linear one:
                # The difference is that the upper two bytes of the
                # payload data of this record are considered to be the
                # "segment address" whilst the lower two are the
                # address within the segment...
                odxassert(segment.load_offset == 0x0)
                odxassert(len(segment.payload) == 4)
                return int.from_bytes(segment.payload)
            elif segment.segment_type == 5:
                # start linear address record
                odxassert(segment.load_offset == 0x0)
                odxassert(len(segment.payload) == 4)
                return int.from_bytes(segment.payload)
            elif segment.segment_type == 1:
                # end of file record
                odxassert(len(segment.payload) == 0)
                if not is_8bit:
                    odxassert(segment.load_offset == 0x0)
                    return None

                return segment.load_offset

        return None

    @property
    def blob(self) -> bytearray:
        base_address = 0
        result = bytearray()
        for segment in self.segments:
            base_address = segment.dump_into(result, base_address)

        return result

    @staticmethod
    def from_string(data_str: str) -> "IntelHexDataSet":
        segments = []
        for line_str in data_str.split("\n"):
            line_str = re.sub(r"\s", "", line_str)
            # ignore empty lines
            if not line_str:
                continue
            segments.append(IntelHexDataSegment.from_string(line_str))

        return IntelHexDataSet(segments=segments,)

    def verify_checksums(self) -> bool:
        for seg in self.segments:
            if not seg.verify_checksum():
                return False

        return True
