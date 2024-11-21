#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import pathlib
from enum import IntEnum
from io import BytesIO
from itertools import chain
from typing import Any, Dict
from xml.etree import ElementTree

import odxtools.uds as uds
from odxtools.additionalaudience import AdditionalAudience
from odxtools.admindata import AdminData
from odxtools.audience import Audience
from odxtools.companydata import CompanyData
from odxtools.companydocinfo import CompanyDocInfo
from odxtools.companyspecificinfo import CompanySpecificInfo
from odxtools.comparaminstance import ComparamInstance
from odxtools.comparamspec import ComparamSpec
from odxtools.comparamsubset import ComparamSubset
from odxtools.compumethods.compuconst import CompuConst
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuCategory, CompuMethod
from odxtools.compumethods.compuscale import CompuScale
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.compumethods.limit import Limit
from odxtools.compumethods.texttablecompumethod import TexttableCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.description import Description
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayercontainer import DiagLayerContainer
from odxtools.diaglayers.basevariant import BaseVariant
from odxtools.diaglayers.basevariantraw import BaseVariantRaw
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.diaglayers.protocol import Protocol
from odxtools.diaglayers.protocolraw import ProtocolRaw
from odxtools.diagservice import DiagService
from odxtools.docrevision import DocRevision
from odxtools.exceptions import odxrequire
from odxtools.functionalclass import FunctionalClass
from odxtools.modification import Modification
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.matchingrequestparameter import MatchingRequestParameter
from odxtools.parameters.nrcconstparameter import NrcConstParameter
from odxtools.parameters.tablekeyparameter import TableKeyParameter
from odxtools.parameters.tablestructparameter import TableStructParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.parentref import ParentRef
from odxtools.physicaldimension import PhysicalDimension
from odxtools.physicaltype import PhysicalType
from odxtools.progcode import ProgCode
from odxtools.relateddoc import RelatedDoc
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.singleecujob import SingleEcuJob
from odxtools.standardlengthtype import StandardLengthType
from odxtools.structure import Structure
from odxtools.table import Table
from odxtools.tablerow import TableRow
from odxtools.teammember import TeamMember
from odxtools.unit import Unit
from odxtools.unitgroup import UnitGroup, UnitGroupCategory
from odxtools.unitspec import UnitSpec
from odxtools.xdoc import XDoc


class SomersaultSID(IntEnum):
    """The Somersault-ECU specific service IDs.

    These are ECU specific service IDs allocated by the UDS standard.

    """

    ForwardFlip = 0xBA
    BackwardFlip = 0xBB
    Headstand = 0xBC
    ForwardFlipCondition = 0xBD


# extend the Somersault SIDs by the UDS ones
tmp = [(i.name, i.value) for i in chain(uds.SID, SomersaultSID)]
SID: Any = IntEnum("SID", tmp)  # type: ignore[misc]

dlc_short_name = "somersault"

# document fragment for everything except the communication parameters
doc_frags = [OdxDocFragment(dlc_short_name, "CONTAINER")]

# document fragments for communication parameters
cp_dwcan_doc_frags = [OdxDocFragment("ISO_11898_2_DWCAN", "COMPARAM-SUBSET")]
cp_iso15765_2_doc_frags = [OdxDocFragment("ISO_15765_2", "COMPARAM-SUBSET")]
cp_iso15765_3_doc_frags = [OdxDocFragment("ISO_15765_3", "COMPARAM-SUBSET")]

##################
# Base variant of Somersault ECU
##################

# company datas
somersault_team_members = {
    "doggy":
        TeamMember(
            odx_id=OdxLinkId("TM.Doggy", doc_frags),
            oid=None,
            short_name="Doggy",
            long_name="Doggy the dog",
            description=Description.from_string("<p>Dog is man's best friend</p>"),
            roles=["gymnast", "tracker"],
            department="sniffers",
            address="Some road",
            zip="12345",
            city="New Dogsville",
            phone="+0 1234/5678-9",
            fax="+0 1234/5678-0",
            email="info@suncus.com",
        ),
    "horsey":
        TeamMember(
            odx_id=OdxLinkId("TM.Horsey", doc_frags),
            oid=None,
            short_name="Horsey",
            long_name="Horsey the horse",
            description=Description.from_string("<p>Trustworthy worker</p>"),
            roles=["gymnast"],
            department="haulers",
            address="Some road",
            zip="12345",
            city="New Dogsville",
            phone="+0 1234/5678-91",
            fax="+0 1234/5678-0",
            email="info@suncus.com",
        ),
    "slothy":
        TeamMember(
            odx_id=OdxLinkId("TM.Slothy", doc_frags),
            oid=None,
            short_name="Slothy",
            long_name=None,
            description=None,
            roles=[],
            department=None,
            address=None,
            zip=None,
            city=None,
            phone=None,
            fax=None,
            email=None,
        ),
}

somersault_company_datas = {
    "suncus":
        CompanyData(
            odx_id=OdxLinkId("CD.Suncus", doc_frags),
            oid=None,
            short_name="Suncus",
            long_name="Circus of the sun",
            description=Description.from_string("<p>Prestigious group of performers</p>"),
            roles=["circus", "gym"],
            team_members=NamedItemList([
                somersault_team_members["doggy"],
                somersault_team_members["horsey"],
            ]),
            company_specific_info=CompanySpecificInfo(
                related_docs=[
                    RelatedDoc(
                        description=Description.from_string("<p>We are the best!</p>"),
                        xdoc=XDoc(
                            short_name="best",
                            long_name="suncus is the best",
                            description=Description.from_string("<p>great propaganda...</p>"),
                            number="1",
                            state="published",
                            date="2015-01-15T20:15:20+05:00",
                            publisher="Suncus Publishing",
                            url="https://suncus-is-the-best.com",
                            position="first!",
                        ),
                    ),
                ],
                sdgs=[],
            ),
        ),
    "acme":
        CompanyData(
            odx_id=OdxLinkId("CD.ACME", doc_frags),
            oid=None,
            short_name="ACME_Corporation",
            long_name=None,
            description=None,
            team_members=NamedItemList([
                somersault_team_members["slothy"],
            ]),
            roles=[],
            company_specific_info=None,
        ),
}

somersault_admin_data = AdminData(
    language="en-US",
    company_doc_infos=[
        CompanyDocInfo(
            company_data_ref=OdxLinkRef("CD.Suncus", doc_frags),
            team_member_ref=OdxLinkRef("TM.Doggy", doc_frags),
            doc_label="A really meaningful label",
            sdgs=[],
        ),
    ],
    doc_revisions=[
        DocRevision(
            team_member_ref=OdxLinkRef("TM.Doggy", doc_frags),
            revision_label="1.0",
            state="draft",
            date="1926-07-18T11:11:11+01:00",
            tool="odxtools 0.0.1",
            modifications=[
                Modification(change="add somersault ECU", reason="we needed a new artist"),
                Modification(
                    change="increase robustness to dizzyness", reason="No alcohol anymore"),
            ],
            company_revision_infos=[],
        ),
        DocRevision(
            team_member_ref=OdxLinkRef("TM.Horsey", doc_frags),
            revision_label="1.1",
            state="released",
            date="2020-08-19T12:12:12+08:00",
            tool="odxtools 0.1",
            modifications=[
                Modification(
                    change="rename somersault ECU to somersault_assiduous to enable slothy to add somersault_lazy",
                    reason=None,
                ),
            ],
            company_revision_infos=[],
        ),
        DocRevision(
            team_member_ref=OdxLinkRef("TM.Slothy", doc_frags),
            revision_label="1.0.3.2.1.5.6",
            date="1900-01-01T00:00:00+00:00",
            state=None,
            tool=None,
            modifications=[],
            company_revision_infos=[],
        ),
    ],
)

# functional classes
somersault_functional_classes = {
    "flip":
        FunctionalClass(
            odx_id=OdxLinkId("somersault.FNC.flip", doc_frags),
            oid=None,
            short_name="flip",
            long_name="Flip",
            description=None,
        ),
    "session":
        FunctionalClass(
            odx_id=OdxLinkId("somersault.FNC.session", doc_frags),
            oid=None,
            short_name="session",
            long_name="Session",
            description=None,
        ),
}

# additional audiences
somersault_additional_audiences = {
    "attentive_admirer":
        AdditionalAudience(
            odx_id=OdxLinkId("somersault.AA.attentive_admirer", doc_frags),
            oid=None,
            short_name="attentive_admirer",
            long_name="Attentive Admirer",
            description=None,
        ),
    "anyone":
        AdditionalAudience(
            odx_id=OdxLinkId("somersault.AA.anyone", doc_frags),
            oid=None,
            short_name="anyone",
            long_name="Anyone",
            description=None,
        ),
}

# diag coded types
somersault_diagcodedtypes = {
    "flag":
        StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=1,
            bit_mask=None,
            base_type_encoding=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        ),
    "uint8":
        StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
            base_type_encoding=None,
        ),
    "uint16":
        StandardLengthType(
            base_data_type=DataType.A_UINT32,
            bit_length=16,
            bit_mask=None,
            base_type_encoding=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        ),
    "float32":
        StandardLengthType(
            base_data_type=DataType.A_FLOAT32,
            bit_length=32,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
            base_type_encoding=None,
        ),
}

somersault_physical_dimensions = {
    "time":
        PhysicalDimension(
            odx_id=OdxLinkId("somersault.PD.time", doc_frags),
            oid=None,
            short_name="time",
            long_name="Time",
            time_exp=1,
            length_exp=0,
            mass_exp=0,
            current_exp=0,
            temperature_exp=0,
            molar_amount_exp=0,
            luminous_intensity_exp=0,
            description=None,
        ),
    "temperature":
        PhysicalDimension(
            odx_id=OdxLinkId("somersault.PD.temperature", doc_frags),
            oid=None,
            short_name="temperature",
            long_name="Temperature",
            time_exp=0,
            length_exp=0,
            mass_exp=0,
            current_exp=0,
            temperature_exp=1,
            molar_amount_exp=0,
            luminous_intensity_exp=0,
            description=None,
        )
}

somersault_units = {
    "second":
        Unit(
            odx_id=OdxLinkId("somersault.unit.second", doc_frags),
            oid=None,
            short_name="second",
            display_name="s",
            long_name="Second",
            description=Description.from_string("<p>SI unit for the time</p>"),
            factor_si_to_unit=1,
            offset_si_to_unit=0,
            physical_dimension_ref=OdxLinkRef.from_id(
                somersault_physical_dimensions["time"].odx_id),
        ),
    "minute":
        Unit(
            odx_id=OdxLinkId("somersault.unit.minute", doc_frags),
            oid=None,
            short_name="minute",
            display_name="min",
            long_name="Minute",
            description=None,
            factor_si_to_unit=60,
            offset_si_to_unit=0,
            physical_dimension_ref=OdxLinkRef.from_id(
                somersault_physical_dimensions["time"].odx_id),
        ),
    "celsius":
        Unit(
            odx_id=OdxLinkId("somersault.unit.celsius", doc_frags),
            oid=None,
            short_name="celsius",
            display_name="°C",
            long_name="Degrees Celcius",
            description=None,
            factor_si_to_unit=1,
            offset_si_to_unit=-273.15,
            physical_dimension_ref=OdxLinkRef.from_id(
                somersault_physical_dimensions["temperature"].odx_id),
        ),
}

somersault_unit_groups = {
    "european_duration":
        UnitGroup(
            oid=None,
            short_name="european_duration",
            category=UnitGroupCategory.COUNTRY,
            unit_refs=[
                OdxLinkRef.from_id(somersault_units["second"].odx_id),
                OdxLinkRef.from_id(somersault_units["minute"].odx_id),
            ],
            long_name="Duration",
            description=Description.from_string("<p>Units for measuring a duration</p>"),
        ),
}

# computation methods
somersault_compumethods: Dict[str, CompuMethod] = {
    "uint_passthrough":
        IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32),
    "float_passthrough":
        IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            compu_internal_to_phys=None,
            compu_phys_to_internal=None,
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32),
    "boolean":
        TexttableCompuMethod(
            category=CompuCategory.TEXTTABLE,
            compu_phys_to_internal=None,
            compu_internal_to_phys=CompuInternalToPhys(
                compu_default_value=None,
                prog_code=None,
                compu_scales=[
                    CompuScale(
                        compu_const=CompuConst(v=None, vt="false", data_type=DataType.A_UTF8STRING),
                        lower_limit=Limit(
                            value_raw="0", value_type=DataType.A_UINT32, interval_type=None),
                        upper_limit=Limit(
                            value_raw="0", value_type=DataType.A_UINT32, interval_type=None),
                        short_label=None,
                        description=None,
                        domain_type=DataType.A_UINT32,
                        range_type=DataType.A_UNICODE2STRING,
                        compu_inverse_value=None,
                        compu_rational_coeffs=None),
                    CompuScale(
                        compu_const=CompuConst(v=None, vt="true", data_type=DataType.A_UTF8STRING),
                        lower_limit=Limit(
                            value_raw="1", value_type=DataType.A_UINT32, interval_type=None),
                        upper_limit=Limit(
                            value_raw="1", value_type=DataType.A_UINT32, interval_type=None),
                        short_label=None,
                        description=None,
                        domain_type=DataType.A_UINT32,
                        range_type=DataType.A_UNICODE2STRING,
                        compu_inverse_value=None,
                        compu_rational_coeffs=None),
                ],
            ),
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UNICODE2STRING,
        ),
}

# data object properties
somersault_dops = {
    "num_flips":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.num_flips", doc_frags),
            oid=None,
            short_name="num_flips",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "soberness_check":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.soberness_check", doc_frags),
            oid=None,
            short_name="soberness_check",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "dizzyness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.dizzyness_level", doc_frags),
            oid=None,
            short_name="dizzyness_level",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "happiness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.happiness_level", doc_frags),
            oid=None,
            short_name="happiness_level",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "duration":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.duration", doc_frags),
            oid=None,
            short_name="duration",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["second"].odx_id),
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "temperature":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.temperature", doc_frags),
            oid=None,
            short_name="temperature",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["celsius"].odx_id),
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "error_code":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.error_code", doc_frags),
            oid=None,
            short_name="error_code",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "boolean":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.boolean", doc_frags),
            oid=None,
            short_name="boolean",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(
                DataType.A_UNICODE2STRING, display_radix=None, precision=None),
            compu_method=somersault_compumethods["boolean"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "uint8":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.uint8", doc_frags),
            oid=None,
            short_name="uint8",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "uint16":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.uint16", doc_frags),
            oid=None,
            short_name="uint16",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["uint16"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
    "float":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.float", doc_frags),
            oid=None,
            short_name="float",
            long_name=None,
            description=None,
            admin_data=None,
            diag_coded_type=somersault_diagcodedtypes["float32"],
            physical_type=PhysicalType(DataType.A_FLOAT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["float_passthrough"],
            unit_ref=None,
            sdgs=[],
            internal_constr=None,
            physical_constr=None,
        ),
}

last_flip_details_table_id = OdxLinkId("somersault.table.last_flip_details", doc_frags)
last_flip_details_table_ref = OdxLinkRef.from_id(last_flip_details_table_id)

# positive responses
somersault_positive_responses = {
    "session":
        Response(
            odx_id=OdxLinkId("somersault.PR.session_start", doc_frags),
            oid=None,
            short_name="session",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.DiagnosticSessionControl.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="can_do_backward_flips",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "tester_ok":
        Response(
            odx_id=OdxLinkId("somersault.PR.tester_present", doc_frags),
            oid=None,
            short_name="tester_present",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.TesterPresent.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="status",
                    long_name=None,
                    semantic=None,
                    description=None,
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                    dop_snref=None,
                    physical_default_value_raw="0",
                    byte_position=1,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "forward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_forward", doc_frags),
            oid=None,
            short_name="grudging_forward",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.ForwardFlip.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    oid=None,
                    short_name="num_flips_done",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=2,
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="sault_time",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw="255",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.duration", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "forward_flips_happily_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.happy_forward", doc_frags),
            oid=None,
            short_name="happy_forward",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.ForwardFlip.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    oid=None,
                    short_name="num_flips_done",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="yeha_level",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "backward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_backward", doc_frags),
            oid=None,
            short_name="grudging_backward",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.BackwardFlip.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="num_flips_done",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                    dop_snref=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="grumpiness_level",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                    dop_snref=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    # Note that there is no such thing as a "backwards flip done happily"!
    "status_report":
        Response(
            odx_id=OdxLinkId("somersault.PR.status_report", doc_frags),
            oid=None,
            short_name="status_report",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.ReadDataByIdentifier.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="dizzyness_level",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.dizzyness_level", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="happiness_level",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.happiness_level", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
                TableKeyParameter(
                    oid=None,
                    odx_id=OdxLinkId("somersault.PR.report_status.last_pos_response_key",
                                     doc_frags),
                    short_name="last_pos_response_key",
                    long_name=None,
                    semantic=None,
                    description=None,
                    table_ref=last_flip_details_table_ref,
                    table_snref=None,
                    table_row_ref=None,
                    table_row_snref=None,
                    byte_position=3,
                    bit_position=None,
                    sdgs=[],
                ),
                TableStructParameter(
                    oid=None,
                    short_name="last_pos_response",
                    long_name=None,
                    semantic=None,
                    description=None,
                    table_key_ref=OdxLinkRef("somersault.PR.report_status.last_pos_response_key",
                                             doc_frags),
                    table_key_snref=None,
                    byte_position=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "set_operation_params":
        Response(
            odx_id=OdxLinkId("somersault.PR.set_operation_params", doc_frags),
            oid=None,
            short_name="set_operation_params",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.positive_response_id(
                        SID.ForwardFlipCondition.value),  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
}

somersault_structures = {
    "forward_flips_grudgingly_done":
        Structure(
            short_name="forward_flips_grudgingly_done_recall",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            oid=None,
            odx_id=OdxLinkId("somersault.struct.recall.forward_flips_grudgingly_done", doc_frags),
            parameters=somersault_positive_responses["forward_flips_grudgingly_done"].parameters,
            byte_size=None),
    "forward_flips_happily_done":
        Structure(
            short_name="forward_flips_happily_done_recall",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            oid=None,
            odx_id=OdxLinkId("somersault.struct.recall.forward_flips_happily_done", doc_frags),
            parameters=somersault_positive_responses["forward_flips_happily_done"].parameters,
            byte_size=None),
    "backward_flips_grudgingly_done":
        Structure(
            short_name="backward_flips_grudgingly_done_recall",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            oid=None,
            odx_id=OdxLinkId("somersault.struct.recall.backward_flips_grudgingly_done", doc_frags),
            parameters=somersault_positive_responses["backward_flips_grudgingly_done"].parameters,
            byte_size=None),
}

# this is a hack to get around a catch-22: we need to specify the
# value of a positive response to the tester present parameter to
# specify ISO_15765_3.CP_TesterPresentMessage communication parameter,
# but we need the comparam for the raw diaglayer which we need for
# retrieving the DOP of the "status" parameter in order to convert the
# raw physical default value.
param = somersault_positive_responses["tester_ok"].parameters.status
assert isinstance(param, ValueParameter)
param._dop = somersault_dops["uint8"]
param._physical_default_value = int(odxrequire(param.physical_default_value_raw))

# negative responses
somersault_negative_responses = {
    "general":
        Response(
            odx_id=OdxLinkId("somersault.NR.general_negative_response", doc_frags),
            oid=None,
            short_name="general_negative_response",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.NegativeResponseId,
                    bit_position=None,
                    sdgs=[],
                ),
                MatchingRequestParameter(
                    oid=None,
                    short_name="rq_sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="response_code",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.error_code", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    # the tester present request needs separate negative and positive
    # responses because it must be fully specified a-priory to be able
    # to extract it for the COMPARAMS.
    "tester_nok":
        Response(
            odx_id=OdxLinkId("somersault.NR.tester_nok", doc_frags),
            oid=None,
            short_name="tester_nok",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.NegativeResponseId,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="rq_sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=uds.SID.TesterPresent.value,  # type: ignore[attr-defined]
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
    "flips_not_done":
        Response(
            odx_id=OdxLinkId("somersault.NR.flips_not_done", doc_frags),
            oid=None,
            short_name="flips_not_done",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.NegativeResponseId,
                    bit_position=None,
                    sdgs=[],
                ),
                MatchingRequestParameter(
                    oid=None,
                    short_name="rq_sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
                NrcConstParameter(
                    oid=None,
                    short_name="reason",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=2,
                    coded_values=[0, 1, 2],
                    # possible values (TODO: make this an enum parameter):
                    # 0 -> not sober
                    # 1 -> too dizzy
                    # 2 -> stumbled
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="flips_successfully_done",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                    dop_snref=None,
                    byte_position=3,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
}

somersault_global_negative_responses = {
    "general":
        Response(
            odx_id=OdxLinkId("GNR.too_hot", doc_frags),
            oid=None,
            short_name="too_hot",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.GLOBAL_NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=uds.NegativeResponseId,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="too_hot_dummy",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=0xfe,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="too_hot_id",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=2,
                    coded_value=0xa7,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="temperature",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=3,
                    dop_ref=OdxLinkRef("somersault.DOP.temperature", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        )
}

# tables
flip_quality_table_id = OdxLinkId("somersault.table.flip_quality", doc_frags)
flip_quality_table_ref = OdxLinkRef.from_id(flip_quality_table_id)
somersault_tables = {
    "last_flip_details":
        Table(
            odx_id=last_flip_details_table_id,
            oid=None,
            short_name="last_flip_details",
            long_name="Flip Details",
            description=Description.from_string(
                "<p>The details the last successfully executed request</p>"),
            semantic="DETAILS",
            admin_data=None,
            key_label="key",
            struct_label="response",
            key_dop_ref=OdxLinkRef.from_id(somersault_dops["uint8"].odx_id),
            table_rows_raw=[
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.none", doc_frags),
                    oid=None,
                    short_name="none",
                    long_name="No Flips Done Yet",
                    key_raw="0",
                    structure_ref=None,
                    structure_snref=None,
                    description=Description.from_string("<p>We have not done any flips yet!</p>"),
                    semantic="DETAILS-KEY",
                    dop_ref=OdxLinkRef.from_id(somersault_dops["soberness_check"].odx_id),
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_grudging",
                                     doc_frags),
                    oid=None,
                    short_name="forward_grudging",
                    long_name="Forward Flips Grudgingly Done",
                    key_raw="3",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["forward_flips_grudgingly_done"].odx_id),
                    structure_snref=None,
                    description=Description.from_string(
                        "<p>The the last forward flip was grudgingly done</p>"),
                    semantic="DETAILS-KEY",
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_happy", doc_frags),
                    oid=None,
                    short_name="forward_happily",
                    long_name="Forward Flips Happily Done",
                    description=None,
                    semantic=None,
                    key_raw="5",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["forward_flips_happily_done"].odx_id),
                    structure_snref=None,
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.backward", doc_frags),
                    oid=None,
                    short_name="backward_grudging",
                    long_name="Backward Flips",
                    description=None,
                    semantic=None,
                    key_raw="10",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["backward_flips_grudgingly_done"].odx_id),
                    structure_snref=None,
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
            ],
            sdgs=[],
        )
}

# requests
somersault_requests = {
    "start_session":
        Request(
            odx_id=OdxLinkId("somersault.RQ.start_session", doc_frags),
            oid=None,
            short_name="start_session",
            long_name="Start the diagnostic session & do some mischief",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.DiagnosticSessionControl  # type: ignore[attr-defined,arg-type]
                    .value,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="id",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=0x0,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "stop_session":
        Request(
            odx_id=OdxLinkId("somersault.RQ.stop_session", doc_frags),
            oid=None,
            short_name="stop_session",
            long_name="Terminate the current diagnostic session",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.DiagnosticSessionControl  # type: ignore[attr-defined,arg-type]
                    .value,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="id",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=0x1,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "tester_present":
        Request(
            odx_id=OdxLinkId("somersault.RQ.tester_present", doc_frags),
            oid=None,
            short_name="tester_present",
            long_name="Prevent the current diagnostic session from timing out",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.TesterPresent.value,  # type: ignore[attr-defined,arg-type]
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="id",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=0x0,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "set_operation_params":
        Request(
            odx_id=OdxLinkId("somersault.RQ.set_operation_params", doc_frags),
            oid=None,
            short_name="set_operation_params",
            long_name="Specify the mode of operation for the ECU; e.g. if rings "
            "of fire ought to be used for maximum effect",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ForwardFlipCondition  # type: ignore[attr-defined,arg-type]
                    .value,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="use_fire_ring",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "forward_flips":
        Request(
            odx_id=OdxLinkId("somersault.RQ.do_forward_flips", doc_frags),
            oid=None,
            short_name="do_forward_flips",
            long_name="Do forward somersaults & some other mischief",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ForwardFlip.value,  # type: ignore[attr-defined,arg-type]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="forward_soberness_check",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                    dop_snref=None,
                    byte_position=1,
                    # value must be 0x12 for the request to be accepted
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="num_flips",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "backward_flips":
        Request(
            odx_id=OdxLinkId("somersault.RQ.do_backward_flips", doc_frags),
            oid=None,
            short_name="do_backward_flips",
            long_name="Do a backward somersault & some other mischief",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.BackwardFlip.value,  # type: ignore[attr-defined,arg-type]
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="backward_soberness_check",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                    dop_snref=None,
                    byte_position=1,
                    # value must be 0x21 for the request to be accepted
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="num_flips",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
    "report_status":
        Request(
            odx_id=OdxLinkId("somersault.RQ.report_status", doc_frags),
            oid=None,
            short_name="report_status",
            long_name="Report back the current level of dizzy- & happiness.",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=[
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ReadDataByIdentifier  # type: ignore[attr-defined,arg-type]
                    .value,
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
                    oid=None,
                    short_name="id",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value=0x0,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        ),
}

# services
somersault_services = {
    "start_session":
        DiagService(
            odx_id=OdxLinkId("somersault.service.session_start", doc_frags),
            oid=None,
            short_name="session_start",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(somersault_requests["start_session"].odx_id),
            semantic="SESSION",
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["session"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            functional_class_refs=[
                OdxLinkRef.from_id(somersault_functional_classes["session"].odx_id),
            ],
            sdgs=[],
        ),
    "stop_session":
        DiagService(
            odx_id=OdxLinkId("somersault.service.session_stop", doc_frags),
            oid=None,
            short_name="session_stop",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="SESSION",
            request_ref=OdxLinkRef.from_id(somersault_requests["stop_session"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["session"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            functional_class_refs=[
                OdxLinkRef.from_id(somersault_functional_classes["session"].odx_id)
            ],
            sdgs=[],
        ),
    "tester_present":
        DiagService(
            odx_id=OdxLinkId("somersault.service.tester_present", doc_frags),
            oid=None,
            short_name="tester_present",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id),
                    OdxLinkRef.from_id(somersault_additional_audiences["anyone"].odx_id),
                ],
                disabled_audience_refs=[],
                is_supplier_raw=None,
                is_aftersales_raw=None,
                is_aftermarket_raw=None,
                is_manufacturing_raw=None,
                is_development_raw=False,
            ),
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="TESTERPRESENT",
            request_ref=OdxLinkRef.from_id(somersault_requests["tester_present"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["tester_ok"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["tester_nok"].odx_id),
            ],
            sdgs=[],
        ),
    "set_operation_params":
        DiagService(
            odx_id=OdxLinkId("somersault.service.set_operation_params", doc_frags),
            oid=None,
            short_name="set_operation_params",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="FUNCTION",
            request_ref=OdxLinkRef.from_id(somersault_requests["set_operation_params"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["set_operation_params"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            sdgs=[],
        ),
    "forward_flips":
        DiagService(
            odx_id=OdxLinkId("somersault.service.do_forward_flips", doc_frags),
            oid=None,
            short_name="do_forward_flips",
            long_name=None,
            description=Description.from_string("<p>Do a forward flip.</p>"),
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                disabled_audience_refs=[],
                is_supplier_raw=None,
                is_aftersales_raw=None,
                is_aftermarket_raw=None,
                is_manufacturing_raw=None,
                is_development_raw=False,
            ),
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="FUNCTION",
            request_ref=OdxLinkRef.from_id(somersault_requests["forward_flips"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(
                    somersault_positive_responses["forward_flips_grudgingly_done"].odx_id),
                # TODO: implement handling of multiple responses
                # OdxLinkRef.from_id(somersault_positive_responses["forward_flips_happily_done"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["flips_not_done"].odx_id),
                # TODO (?): implement handling of multiple possible responses
                # OdxLinkRef.from_id(somersault_negative_responses["stumbled"].odx_id),
                # OdxLinkRef.from_id(somersault_negative_responses["too_dizzy"].odx_id),
                # OdxLinkRef.from_id(somersault_negative_responses["not_sober"].odx_id),
            ],
            functional_class_refs=[
                OdxLinkRef.from_id(somersault_functional_classes["flip"].odx_id)
            ],
            sdgs=[],
        ),
    "backward_flips":
        DiagService(
            odx_id=OdxLinkId("somersault.service.do_backward_flips", doc_frags),
            oid=None,
            short_name="do_backward_flips",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                disabled_audience_refs=[],
                is_supplier_raw=None,
                is_aftersales_raw=None,
                is_aftermarket_raw=None,
                is_manufacturing_raw=None,
                is_development_raw=False,
            ),
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="FUNCTION",
            request_ref=OdxLinkRef.from_id(somersault_requests["backward_flips"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(
                    somersault_positive_responses["backward_flips_grudgingly_done"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["flips_not_done"].odx_id),
            ],
            functional_class_refs=[
                OdxLinkRef.from_id(somersault_functional_classes["flip"].odx_id)
            ],
            sdgs=[],
        ),
    "report_status":
        DiagService(
            odx_id=OdxLinkId("somersault.service.report_status", doc_frags),
            oid=None,
            short_name="report_status",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=Audience(
                disabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                enabled_audience_refs=[],
                is_supplier_raw=None,
                is_manufacturing_raw=None,
                is_development_raw=None,
                is_aftersales_raw=False,
                is_aftermarket_raw=False,
            ),
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="CURRENTDATA",
            request_ref=OdxLinkRef.from_id(somersault_requests["report_status"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["status_report"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            sdgs=[],
        ),
}

somersault_single_ecu_jobs = {
    "compulsory_program":
        SingleEcuJob(
            audience=None,
            odx_id=OdxLinkId("somersault.service.compulsory_program", doc_frags),
            oid=None,
            short_name="compulsory_program",
            long_name="Compulsory Program",
            description=Description.from_string("<p>Do several fancy moves.</p>"),
            admin_data=None,
            semantic=None,
            functional_class_refs=[],
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            diagnostic_class=None,
            prog_codes=[
                ProgCode(
                    code_file="jobs.py",
                    encryption=None,
                    syntax="PYTHON3",
                    entrypoint="compulsory_program",
                    revision="1.23.4",
                    library_refs=[],
                ),
            ],
            input_params=NamedItemList(),
            output_params=NamedItemList(),
            neg_output_params=NamedItemList(),
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            sdgs=[],
        )
}

# communication parameters
tester_present_value = somersault_requests["tester_present"].encode()
tester_pr_value = somersault_positive_responses["tester_ok"].encode()
tester_nr_value = somersault_negative_responses["tester_nok"].encode()
somersault_comparam_refs = [
    ###
    # basic parameters
    ###
    # bus speed
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_11898_2_DWCAN.CP_Baudrate", cp_dwcan_doc_frags),
        value="500000",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # parameters of the CAN diagnostics frames
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_2.CP_UniqueRespIdTable", cp_iso15765_2_doc_frags),
        value=[
            # CP_CanPhysReqFormat
            "normal segmented 11-bit transmit with FC",
            # CP_CanPhysReqId
            "123",
            # CP_CanPhysReqExtAddr
            "0",
            # CP_CanRespUSDTFormat
            "normal segmented 11-bit receive with FC",
            # CP_CanRespUSDTId
            "456",
            # CP_CanRespUSDTExtAddr
            "0",
            # CP_CanRespUUDTFormat
            "normal unsegmented 11-bit receive",
            # CP_CanRespUUDTId
            "4294967295",  # -> -1. this seems to be mandated by the standard. what a hack!
            # CP_CanRespUUDTExtAddr
            "0",
            # CP_ECULayerShortName
            "Somersault",
        ],
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # timeout for responses [us]
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_RC21CompletionTimeout", cp_iso15765_3_doc_frags),
        value="1000000",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    ###
    # "tester present" message handling
    ###
    # expected "tester present" message
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentMessage", cp_iso15765_3_doc_frags),
        value=f"{tester_present_value.hex()}",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # a response is mandatory
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # positive response to "tester present"
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpPosResp", cp_iso15765_3_doc_frags),
        value=f"{tester_pr_value.hex()}",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # negative response to "tester present"
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpNegResp", cp_iso15765_3_doc_frags),
        value=f"{tester_nr_value.hex()}",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # when a tester present message must be send
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentSendType", cp_iso15765_3_doc_frags),
        value="On idle",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # "tester present" messages are send directly to the CAN IDs
    # (i.e., they are not embedded in the ISO-TP telegram?)
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentAddrMode", cp_iso15765_3_doc_frags),
        value="Physical",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    # is a response from the ECU to "tester present" messages expected
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
    ###
    # ISO-TP parameters:
    ###
    # maximum number of frames between flow control ACKs
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_2.CP_BlockSize", cp_iso15765_2_doc_frags),
        value="4",
        protocol_snref="somersault_protocol",
        prot_stack_snref=None,
        description=None,
    ),
]

somersault_diag_data_dictionary_spec = DiagDataDictionarySpec(
    admin_data=None,
    data_object_props=NamedItemList(somersault_dops.values()),
    unit_spec=UnitSpec(
        unit_groups=NamedItemList(somersault_unit_groups.values()),
        units=NamedItemList(somersault_units.values()),
        physical_dimensions=NamedItemList(somersault_physical_dimensions.values()),
        sdgs=[],
    ),
    tables=NamedItemList(somersault_tables.values()),
    muxs=NamedItemList(),
    env_datas=NamedItemList(),
    env_data_descs=NamedItemList(),
    dtc_dops=NamedItemList(),
    structures=NamedItemList(somersault_structures.values()),
    static_fields=NamedItemList(),
    end_of_pdu_fields=NamedItemList(),
    dynamic_length_fields=NamedItemList(),
    dynamic_endmarker_fields=NamedItemList(),
    sdgs=[],
)

# diagnostics layer for the protocol
somersault_protocol_raw = ProtocolRaw(
    variant_type=DiagLayerType.PROTOCOL,
    odx_id=OdxLinkId("somersault.protocol", doc_frags),
    oid=None,
    short_name="somersault_protocol",
    long_name="Somersault protocol info",
    description=Description.from_string(
        "<p>Protocol information of the somersault ECUs &amp; cetera</p>"),
    admin_data=None,
    company_datas=NamedItemList(),
    functional_classes=NamedItemList(),
    diag_data_dictionary_spec=None,
    diag_comms_raw=[],
    requests=NamedItemList(),
    positive_responses=NamedItemList(),
    negative_responses=NamedItemList(),
    global_negative_responses=NamedItemList(),
    import_refs=[],
    state_charts=NamedItemList(),
    additional_audiences=NamedItemList(),
    sdgs=[],
    parent_refs=[],
    comparam_spec_ref=OdxLinkRef("CPS_ISO_15765_3_on_ISO_15765_2",
                                 [OdxDocFragment("ISO_15765_3_on_ISO_15765_2", "COMPARAM-SPEC")]),
    comparam_refs=somersault_comparam_refs,
    libraries=NamedItemList(),
    prot_stack_snref=None,
    sub_components=NamedItemList(),
)
somersault_protocol = Protocol(diag_layer_raw=somersault_protocol_raw)

# diagnostics layer for the base variant
somersault_base_variant_raw = BaseVariantRaw(
    variant_type=DiagLayerType.BASE_VARIANT,
    odx_id=OdxLinkId("somersault", doc_frags),
    oid=None,
    short_name="somersault",
    long_name="Somersault base variant",
    description=Description.from_string("<p>Base variant of the somersault ECU &amp; cetera</p>"),
    admin_data=None,
    company_datas=NamedItemList(),
    functional_classes=NamedItemList(somersault_functional_classes.values()),
    diag_data_dictionary_spec=somersault_diag_data_dictionary_spec,
    diag_comms_raw=[*somersault_services.values(), *somersault_single_ecu_jobs.values()],
    requests=NamedItemList(somersault_requests.values()),
    positive_responses=NamedItemList(somersault_positive_responses.values()),
    negative_responses=NamedItemList(somersault_negative_responses.values()),
    global_negative_responses=NamedItemList(somersault_global_negative_responses.values()),
    import_refs=[],
    state_charts=NamedItemList(),
    additional_audiences=NamedItemList(somersault_additional_audiences.values()),
    sdgs=[],
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_protocol.odx_id),
            not_inherited_diag_comms=[],
            not_inherited_dops=[],
            not_inherited_variables=[],
            not_inherited_tables=[],
            not_inherited_global_neg_responses=[],
        )
    ],
    comparam_refs=[],
    diag_variables_raw=[],
    variable_groups=NamedItemList(),
    libraries=NamedItemList(),
    sub_components=NamedItemList(),
    dyn_defined_spec=None)
somersault_base_variant = BaseVariant(diag_layer_raw=somersault_base_variant_raw)

##################
# Lazy variant of Somersault ECU: this one is lazy and cuts corners
##################

somersault_lazy_ecu_raw = EcuVariantRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_lazy", doc_frags),
    oid=None,
    short_name="somersault_lazy",
    long_name="Somersault lazy ECU",
    description=Description.from_string(
        "<p>Sloppy variant of the somersault ECU (lazy &lt; assiduous)</p>"),
    admin_data=None,
    company_datas=NamedItemList(),
    functional_classes=NamedItemList(),
    diag_data_dictionary_spec=None,
    diag_comms_raw=[],
    requests=NamedItemList(),
    positive_responses=NamedItemList(),
    negative_responses=NamedItemList(),
    global_negative_responses=NamedItemList(),
    import_refs=[],
    state_charts=NamedItemList(),
    additional_audiences=NamedItemList(),
    sdgs=[],
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_base_variant.odx_id),
            # this variant does not do backflips and does not like
            # being told under which conditions it operates.
            not_inherited_diag_comms=[
                somersault_requests["backward_flips"].short_name,
                somersault_requests["set_operation_params"].short_name,
            ],
            not_inherited_dops=[],
            not_inherited_variables=[],
            not_inherited_tables=[],
            not_inherited_global_neg_responses=[],
        )
    ],
    comparam_refs=[],
    ecu_variant_patterns=[],
    diag_variables_raw=[],
    variable_groups=NamedItemList(),
    libraries=NamedItemList(),
    dyn_defined_spec=None,
    sub_components=NamedItemList(),
)
somersault_lazy_ecu = EcuVariant(diag_layer_raw=somersault_lazy_ecu_raw)

##################
# Assiduous production variant of Somersault ECU: This one works
# harder than it needs to
##################

# the assiduous ECU also does headstands...
somersault_assiduous_requests = {
    "headstand":
        Request(
            odx_id=OdxLinkId("somersault_assiduous.RQ.do_headstand", doc_frags),
            oid=None,
            short_name="do_headstand",
            long_name="Do a headstand & whatever else is required to entertain the customer",
            description=None,
            admin_data=None,
            sdgs=[],
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=0x3,
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
                    oid=None,
                    short_name="duration",
                    long_name=None,
                    semantic=None,
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.duration", doc_frags),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
}

# positive responses
somersault_assiduous_positive_responses = {
    "headstand_done":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.PR.headstand_done", doc_frags),
            oid=None,
            short_name="headstand_done",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=0x1,
                    bit_position=None,
                    sdgs=[],
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    oid=None,
                    short_name="duration",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=1,
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
}

# negative responses
somersault_assiduous_negative_responses = {
    "fell_over":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.NR.fell_over", doc_frags),
            oid=None,
            short_name="fell_over",
            long_name=None,
            description=None,
            admin_data=None,
            sdgs=[],
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    oid=None,
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=0x20,
                    bit_position=None,
                    sdgs=[],
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    oid=None,
                    short_name="duration",
                    long_name=None,
                    semantic=None,
                    description=None,
                    request_byte_position=1,  # somersault_assiduous_requests["headstand"]["duration"].byte_position
                    byte_position=1,
                    byte_length=1,
                    bit_position=None,
                    sdgs=[],
                ),
            ]),
        ),
}

# services
somersault_assiduous_services = {
    "headstand":
        DiagService(
            odx_id=OdxLinkId("somersault_assiduous.service.headstand", doc_frags),
            oid=None,
            short_name="headstand",
            long_name=None,
            description=None,
            admin_data=None,
            protocol_snrefs=[],
            related_diag_comm_refs=[],
            diagnostic_class=None,
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            semantic=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request_ref=OdxLinkRef.from_id(somersault_assiduous_requests["headstand"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(
                    somersault_assiduous_positive_responses["headstand_done"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_assiduous_negative_responses["fell_over"].odx_id),
            ],
            comparam_refs=[],
            is_cyclic_raw=None,
            is_multiple_raw=None,
            addressing_raw=None,
            transmission_mode_raw=None,
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                disabled_audience_refs=[],
                is_supplier_raw=None,
                is_manufacturing_raw=None,
                is_development_raw=None,
                is_aftersales_raw=None,
                is_aftermarket_raw=None,
            ),
            sdgs=[],
        ),
}

somersault_assiduous_ecu_raw = EcuVariantRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_assiduous", doc_frags),
    oid=None,
    short_name="somersault_assiduous",
    long_name="Somersault assiduous ECU",
    description=Description.from_string(
        "<p>Hard-working variant of the somersault ECU (lazy &lt; assiduous)</p>"),
    admin_data=None,
    company_datas=NamedItemList(),
    functional_classes=NamedItemList(),
    diag_data_dictionary_spec=DiagDataDictionarySpec(
        admin_data=None,
        dtc_dops=NamedItemList(),
        data_object_props=NamedItemList(),
        static_fields=NamedItemList(),
        structures=NamedItemList(),
        end_of_pdu_fields=NamedItemList(),
        dynamic_length_fields=NamedItemList(),
        dynamic_endmarker_fields=NamedItemList(),
        tables=NamedItemList(),
        env_datas=NamedItemList(),
        env_data_descs=NamedItemList(),
        muxs=NamedItemList(),
        unit_spec=None,
        sdgs=[],
    ),
    diag_comms_raw=list(somersault_assiduous_services.values()),
    requests=NamedItemList(somersault_assiduous_requests.values()),
    positive_responses=NamedItemList(somersault_assiduous_positive_responses.values()),
    negative_responses=NamedItemList(somersault_assiduous_negative_responses.values()),
    global_negative_responses=NamedItemList(),
    import_refs=[],
    state_charts=NamedItemList(),
    additional_audiences=NamedItemList(),
    sdgs=[],
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_base_variant.odx_id),
            # this variant does everything which the base variant does
            # and more
            not_inherited_diag_comms=[],
            not_inherited_dops=[],
            not_inherited_variables=[],
            not_inherited_tables=[],
            not_inherited_global_neg_responses=[],
        )
    ],
    comparam_refs=somersault_comparam_refs,
    ecu_variant_patterns=[],
    diag_variables_raw=[],
    variable_groups=NamedItemList(),
    libraries=NamedItemList(),
    dyn_defined_spec=None,
    sub_components=NamedItemList(),
)
somersault_assiduous_ecu = EcuVariant(diag_layer_raw=somersault_assiduous_ecu_raw)

##################
# Container with all ECUs
##################

# create a "diagnosis layer container" object
somersault_dlc = DiagLayerContainer(
    odx_id=OdxLinkId("DLC.somersault", doc_frags),
    oid=None,
    short_name=dlc_short_name,
    long_name="Collect all saults in the summer",
    description=Description.from_string(
        "<p>This contains ECUs which do somersaults &amp; cetera</p>"),
    admin_data=somersault_admin_data,
    company_datas=NamedItemList([
        somersault_company_datas["suncus"],
        somersault_company_datas["acme"],
    ]),
    base_variants=NamedItemList([somersault_base_variant]),
    ecu_variants=NamedItemList([somersault_lazy_ecu, somersault_assiduous_ecu]),
    ecu_shared_datas=NamedItemList(),
    protocols=NamedItemList([somersault_protocol]),
    functional_groups=NamedItemList(),
    sdgs=[],
)

# read the communication parameters
comparam_subsets = []
odx_cs_dir = pathlib.Path(__file__).parent / "data"
for odx_cs_filename in (
        "ISO_11898_2_DWCAN.odx-cs",
        "ISO_11898_3_DWFTCAN.odx-cs",
        "ISO_15765_2.odx-cs",
        "ISO_15765_3_CPSS.odx-cs",
        "SAE_J2411_SWCAN_CPSS.odx-cs",
):
    odx_cs_root = ElementTree.parse(odx_cs_dir / odx_cs_filename).getroot()
    subset = odx_cs_root.find("COMPARAM-SUBSET")
    if subset is not None:
        comparam_subsets.append(ComparamSubset.from_et(subset, []))

comparam_specs = []
for odx_c_filename in ("UDSOnCAN_CPS.odx-c",):
    odx_c_root = ElementTree.parse(odx_cs_dir / odx_c_filename).getroot()
    subset = odx_c_root.find("COMPARAM-SPEC")
    if subset is not None:
        comparam_specs.append(ComparamSpec.from_et(subset, []))

# create a database object
database = Database()
database.short_name = "somersault_database"
database._diag_layer_containers = NamedItemList([somersault_dlc])
database._comparam_subsets = NamedItemList(comparam_subsets)
database._comparam_specs = NamedItemList(comparam_specs)
database.add_auxiliary_file("jobs.py",
                            BytesIO(b"""
def compulsory_program():
  print("Hello, World")
"""))

# Create ID mapping and resolve references
database.refresh()
