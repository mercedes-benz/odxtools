# SPDX-License-Identifier: MIT
import unittest
from typing import List, cast

from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory
from odxtools.compumethods.compurationalcoeffs import CompuRationalCoeffs
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.linearcompumethod import LinearCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diaglayer import DiagLayer
from odxtools.exceptions import EncodeError
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.parameter import Parameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.physicaltype import PhysicalType
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.standardlengthtype import StandardLengthType

doc_frags = [OdxDocFragment("UnitTest", "WinneThePoh")]


class TestEncodeRequest(unittest.TestCase):

    def test_encode_coded_const_infer_order(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            short_name="coded_const_parameter",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x7D,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            short_name="coded_const_parameter",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0xAB,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2]),
            byte_size=None,
        )
        self.assertEqual(req.encode(), bytearray([0x7D, 0xAB]))

    def test_encode_coded_const_reorder(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            short_name="param1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x34,
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            short_name="param2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2]),
            byte_size=None,
        )
        self.assertEqual(req.encode(), bytearray([0x12, 0x34]))

    def test_encode_linear(self) -> None:
        odxlinks = OdxLinkDatabase()
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        # This CompuMethod represents the linear function: decode(x) = 2*x + 8 and encode(x) = (x-8)/2
        compu_method = LinearCompuMethod(
            category=CompuCategory.LINEAR,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_scales=[
                    CompuScale(
                        short_label=None,
                        description=None,
                        lower_limit=None,
                        upper_limit=None,
                        compu_inverse_value=None,
                        compu_const=None,
                        compu_rational_coeffs=CompuRationalCoeffs(
                            numerators=[8, 2],
                            denominators=[1],
                        ),
                        internal_type=DataType.A_INT32,
                        physical_type=DataType.A_INT32),
                ],
                prog_code=None,
                compu_default_value=None),
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            short_name="dop_sn",
            long_name="example dop",
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=compu_method,
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        odxlinks.update({dop.odx_id: dop})
        param1 = ValueParameter(
            short_name="value_parameter",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=None,
            bit_position=None,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request.id", doc_frags),
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1]),
            byte_size=None,
        )

        param1._resolve_odxlinks(odxlinks)
        param1._parameter_resolve_snrefs(cast(DiagLayer, None), param_list=req.parameters)

        # Missing mandatory parameter.
        with self.assertRaises(EncodeError):
            req.encode()

        self.assertEqual(
            req.encode(value_parameter=14),
            bytearray([0x3])  # encode(14) = (14-8)/2 = 3
        )

    def test_encode_nrc_const(self) -> None:
        diag_coded_type = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        dop = DataObjectProperty(
            odx_id=OdxLinkId("dop.id", doc_frags),
            short_name="dop_sn",
            long_name="example dop",
            description=None,
            admin_data=None,
            diag_coded_type=diag_coded_type,
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                compu_internal_to_phys=None,
                compu_phys_to_internal=None,
                internal_type=DataType.A_UINT32,
                physical_type=DataType.A_UINT32),
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        )
        odxlinks = OdxLinkDatabase()
        odxlinks.update(dop._build_odxlinks())
        param1 = CodedConstParameter(
            short_name="param1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_value=0x12,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = NrcConstParameter(
            short_name="param2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=diag_coded_type,
            coded_values=[0x34, 0xAB],
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        param3 = ValueParameter(
            short_name="param3",
            long_name=None,
            description=None,
            semantic=None,
            dop_ref=OdxLinkRef.from_id(dop.odx_id),
            dop_snref=None,
            physical_default_value_raw=None,
            byte_position=1,
            bit_position=None,
            sdgs=[],
        )
        param3._resolve_odxlinks(odxlinks)
        resp = Response(
            odx_id=OdxLinkId("response_id", doc_frags),
            short_name="response_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([param1, param2, param3]),
            byte_size=None,
        )

        with self.assertRaises(EncodeError):
            resp.encode()  # "No value for required parameter param3 specified"
        self.assertEqual(resp.encode(param3=0xAB), bytearray([0x12, 0xAB]))
        self.assertRaises(EncodeError, resp.encode, param2=0xEF)

    def test_encode_overlapping(self) -> None:
        uint24 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=24,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        uint8 = StandardLengthType(
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            bit_length=8,
            bit_mask=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
        )
        param1 = CodedConstParameter(
            short_name="code",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint24,
            coded_value=0x123456,
            byte_position=0,
            bit_position=None,
            sdgs=[],
        )
        param2 = CodedConstParameter(
            short_name="part1",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint8,
            coded_value=0x23,
            byte_position=0,
            bit_position=4,
            sdgs=[],
        )
        param3 = CodedConstParameter(
            short_name="part2",
            long_name=None,
            description=None,
            semantic=None,
            diag_coded_type=uint8,
            coded_value=0x45,
            byte_position=1,
            bit_position=4,
            sdgs=[],
        )
        req = Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([param1, param2, param3]),
            byte_size=None,
        )
        self.assertEqual(req.encode().hex(), "123456")
        self.assertEqual(req.get_static_bit_length(), 24)

    def _create_request(self, parameters: List[Parameter]) -> Request:
        return Request(
            odx_id=OdxLinkId("request_id", doc_frags),
            short_name="request_sn",
            parameters=NamedItemList(parameters),
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            byte_size=None,
        )

    def test_bit_mask(self) -> None:
        inner_dct = StandardLengthType(
            bit_mask=0x3fc,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
            bit_length=14)
        outer_dct = StandardLengthType(
            bit_mask=0xf00f,
            base_data_type=DataType.A_UINT32,
            base_type_encoding=None,
            is_highlow_byte_order_raw=None,
            is_condensed_raw=None,
            bit_length=16)

        physical_type = PhysicalType(
            base_data_type=DataType.A_UINT32, display_radix=None, precision=None)
        compu_method = IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32)

        inner_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.inner', doc_frags),
            short_name="inner_dop",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            diag_coded_type=inner_dct,
            physical_type=physical_type,
            compu_method=compu_method,
            unit_ref=None,
            internal_constr=None,
            physical_constr=None)

        outer_dop = DataObjectProperty(
            odx_id=OdxLinkId('dop.outer', doc_frags),
            short_name="outer_dop",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            diag_coded_type=outer_dct,
            physical_type=physical_type,
            compu_method=compu_method,
            unit_ref=None,
            internal_constr=None,
            physical_constr=None)

        odxlinks = OdxLinkDatabase()
        odxlinks.update(inner_dop._build_odxlinks())
        odxlinks.update(outer_dop._build_odxlinks())
        odxlinks.update(inner_dct._build_odxlinks())
        odxlinks.update(outer_dct._build_odxlinks())

        # Inner
        inner_param = ValueParameter(
            short_name="inner_param",
            long_name=None,
            description=None,
            byte_position=0,
            bit_position=2,
            dop_ref=OdxLinkRef.from_id(inner_dop.odx_id),
            dop_snref=None,
            semantic=None,
            sdgs=[],
            physical_default_value_raw=None)
        inner_param._resolve_odxlinks(odxlinks)
        inner_param._parameter_resolve_snrefs(cast(DiagLayer, None), param_list=[])

        # Outer
        outer_param = ValueParameter(
            short_name="outer_param",
            long_name=None,
            description=None,
            byte_position=0,
            bit_position=None,
            dop_ref=OdxLinkRef.from_id(outer_dop.odx_id),
            dop_snref=None,
            semantic=None,
            sdgs=[],
            physical_default_value_raw=None)
        outer_param._resolve_odxlinks(odxlinks)
        outer_param._parameter_resolve_snrefs(cast(DiagLayer, None), param_list=[])

        req = self._create_request([inner_param, outer_param])

        # the bit shifts here stem from the fact that we placed the
        # inner parameter at bit position 2...
        self.assertEqual(req.encode(inner_param=0x1234 >> 2, outer_param=0x4568).hex(), "4238")
        self.assertEqual(
            req.decode(bytes.fromhex('abcd')), {
                "inner_param": (0xbc << 2),
                "outer_param": 0xa00d
            })


if __name__ == "__main__":
    unittest.main()
