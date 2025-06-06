# SPDX-License-Identifier: MIT
import re
from dataclasses import dataclass

from .exceptions import odxassert
from .motorolasdatasegment import MotorolaSDataSegment


@dataclass(kw_only=True)
class MotorolaSDataSet:
    """This class represents a full data set of binary data using the Motorola-S (SREC) format."""
    segments: list[MotorolaSDataSegment]

    @property
    def start_address(self) -> int | None:
        for segment in self.segments:
            if segment.segment_type in (7, 8, 9):
                # start address (32, 24 and 16 bit version)
                odxassert(len(segment.payload) == 0)
                return segment.address

        return None

    @property
    def blob(self) -> bytearray:
        base_address = 0
        result = bytearray()
        for segment in self.segments:
            base_address = segment.dump_into(result, base_address)

        return result

    @staticmethod
    def from_string(data_str: str) -> "MotorolaSDataSet":
        segments = []
        for line_str in data_str.split("\n"):
            line_str = re.sub(r"\s", "", line_str)
            # ignore empty lines
            if not line_str:
                continue
            segments.append(MotorolaSDataSegment.from_string(line_str))

        return MotorolaSDataSet(segments=segments,)

    def verify_checksums(self) -> bool:
        for seg in self.segments:
            if not seg.verify_checksum():
                return False

        return True
