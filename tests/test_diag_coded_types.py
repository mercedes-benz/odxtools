import unittest

from odxtools.diagcodedtypes import *


class TestDiagCodedType(unittest.TestCase):
    def test_leading_length_info_type_bytefield(self):
        dct = LeadingLengthInfoType("A_BYTEFIELD", 6)
        internal, next_byte = dct.convert_bytes_to_internal(
            bytes([0x2, 0x34, 0x56]), 0, 0)
        self.assertEqual(internal, bytes([0x34, 0x56]))

        dct = LeadingLengthInfoType("A_BYTEFIELD", 5)
        # 0xC2 = 11000010, with bit_position=1 and bit_lenth=5, the extracted bits are 00001, i.e. the leading length is 1, i.e. only the bye 0x3 wshould be extracted.
        internal, next_byte = dct.convert_bytes_to_internal(
            bytes([0x1, 0xC2, 0x3, 0x4]), byte_position=1, bit_position=1)
        self.assertEqual(internal, bytes([0x3]))

    def test_standard_length_type_uint(self):
        dct = StandardLengthType("A_UINT32", 5)
        internal, next_byte = dct.convert_bytes_to_internal(
            bytes([0x1, 0x72, 0x3]), byte_position=1, bit_position=1)
        self.assertEqual(internal, 25)
        self.assertEqual(next_byte, 2)

    def test_standard_length_type_uint_byteorder(self):
        dct = StandardLengthType("A_UINT32", 16, is_highlow_byte_order=False)
        internal, next_byte = dct.convert_bytes_to_internal(
            bytes([0x1, 0x2, 0x3]), byte_position=1, bit_position=0)
        self.assertEqual(internal, 0x0302)
        self.assertEqual(next_byte, 3)

    def test_standard_length_type_bytes(self):
        dct = StandardLengthType("A_BYTEFIELD", 16)
        internal, next_byte = dct.convert_bytes_to_internal(
            bytes([0x12, 0x34, 0x56, 0x78]), byte_position=1, bit_position=0)
        self.assertEqual(internal, bytes([0x34, 0x56]))
        self.assertEqual(next_byte, 3)


if __name__ == '__main__':
    unittest.main()
