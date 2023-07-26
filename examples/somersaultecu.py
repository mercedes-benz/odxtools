#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import pathlib
from enum import IntEnum
from itertools import chain
from typing import Any
from xml.etree import ElementTree

import odxtools.uds as uds
from odxtools import PhysicalConstantParameter
from odxtools.admindata import AdminData, CompanyDocInfo, DocRevision, Modification
from odxtools.audience import AdditionalAudience, Audience
from odxtools.communicationparameter import CommunicationParameterRef
from odxtools.companydata import CompanyData, CompanySpecificInfo, RelatedDoc, TeamMember, XDoc
from odxtools.comparam_subset import ComparamSubset
from odxtools.compumethods import CompuScale, IdenticalCompuMethod, Limit, TexttableCompuMethod
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer
from odxtools.diaglayercontainer import DiagLayerContainer
from odxtools.diaglayerraw import DiagLayerRaw
from odxtools.diaglayertype import DiagLayerType
from odxtools.envdata import EnvironmentData
from odxtools.envdatadesc import EnvironmentDataDescription
from odxtools.functionalclass import FunctionalClass
from odxtools.globals import logger
from odxtools.multiplexer import (Multiplexer, MultiplexerCase, MultiplexerDefaultCase,
                                  MultiplexerSwitchKey)
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters import (CodedConstParameter, MatchingRequestParameter, NrcConstParameter,
                                 TableKeyParameter, TableStructParameter, ValueParameter)
from odxtools.parentref import ParentRef
from odxtools.physicaltype import PhysicalType
from odxtools.service import DiagService
from odxtools.singleecujob import ProgCode, SingleEcuJob
from odxtools.structures import Request, Response
from odxtools.table import Table, TableRow
from odxtools.units import PhysicalDimension, Unit, UnitGroup, UnitSpec
from odxtools.utils import short_name_as_id


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
SID: Any = IntEnum("SID", tmp)  # type: ignore

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
            short_name="Doggy",
            long_name="Doggy the dog",
            description="<p>Dog is man's best friend</p>",
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
            short_name="Horsey",
            long_name="Horsey the horse",
            description="<p>Trustworthy worker</p>",
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
            short_name="Suncus",
            long_name="Circus of the sun",
            description="<p>Prestigious group of performers</p>",
            roles=["circus", "gym"],
            team_members=NamedItemList(
                short_name_as_id,
                [
                    somersault_team_members["doggy"],
                    somersault_team_members["horsey"],
                ],
            ),
            company_specific_info=CompanySpecificInfo(
                related_docs=[
                    RelatedDoc(
                        description="<p>We are the best!</p>",
                        xdoc=XDoc(
                            short_name="best",
                            long_name="suncus is the best",
                            description="<p>great propaganda...</p>",
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
            short_name="ACME_Corporation",
            long_name=None,
            description=None,
            team_members=NamedItemList(
                short_name_as_id,
                [
                    somersault_team_members["slothy"],
                ],
            ),
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
            short_name="flip",
            long_name="Flip",
            description=None,
        ),
    "session":
        FunctionalClass(
            odx_id=OdxLinkId("somersault.FNC.session", doc_frags),
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
            short_name="attentive_admirer",
            long_name="Attentive Admirer",
            description=None,
        ),
    "anyone":
        AdditionalAudience(
            odx_id=OdxLinkId("somersault.AA.anyone", doc_frags),
            short_name="anyone",
            long_name="Anyone",
            description=None,
        ),
}

# diag coded types
somersault_diagcodedtypes = {
    "flag":
        StandardLengthType(
            base_data_type="A_UINT32",
            bit_length=1,
            bit_mask=None,
            base_type_encoding=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        ),
    "uint8":
        StandardLengthType(
            base_data_type="A_UINT32",
            bit_length=8,
            bit_mask=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
            base_type_encoding=None,
        ),
    "uint16":
        StandardLengthType(
            base_data_type="A_UINT32",
            bit_length=16,
            bit_mask=None,
            base_type_encoding=None,
            is_condensed_raw=None,
            is_highlow_byte_order_raw=None,
        ),
    "float32":
        StandardLengthType(
            base_data_type="A_FLOAT32",
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
            short_name="time",
            long_name="Time",
            time_exp=1,
            length_exp=0,
            mass_exp=0,
            current_exp=0,
            temperature_exp=0,
            molar_amount_exp=0,
            luminous_intensity_exp=0,
            oid=None,
            description=None,
        ),
    "temperature":
        PhysicalDimension(
            odx_id=OdxLinkId("somersault.PD.temperature", doc_frags),
            short_name="temperature",
            long_name="Temperature",
            time_exp=0,
            length_exp=0,
            mass_exp=0,
            current_exp=0,
            temperature_exp=1,
            molar_amount_exp=0,
            luminous_intensity_exp=0,
            oid=None,
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
            description="<p>SI unit for the time</p>",
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
            category="COUNTRY",
            unit_refs=[
                OdxLinkRef.from_id(somersault_units["second"].odx_id),
                OdxLinkRef.from_id(somersault_units["minute"].odx_id),
            ],
            long_name="Duration",
            description="<p>Units for measuring a duration</p>",
        ),
}

# computation methods
somersault_compumethods = {
    "uint_passthrough":
        IdenticalCompuMethod(internal_type="A_UINT32", physical_type="A_UINT32"),
    "float_passthrough":
        IdenticalCompuMethod(internal_type="A_FLOAT32", physical_type="A_FLOAT32"),
    "boolean":
        TexttableCompuMethod(
            internal_type="A_UINT32",
            internal_to_phys=[
                CompuScale(compu_const="false", lower_limit=Limit(0), upper_limit=Limit(0)),
                CompuScale(compu_const="true", lower_limit=Limit(1), upper_limit=Limit(1)),
            ],
        ),
}

# data object properties
somersault_dops = {
    "num_flips":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.num_flips", doc_frags),
            short_name="num_flips",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "soberness_check":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.soberness_check", doc_frags),
            short_name="soberness_check",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "dizzyness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.dizzyness_level", doc_frags),
            short_name="dizzyness_level",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "happiness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.happiness_level", doc_frags),
            short_name="happiness_level",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "duration":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.duration", doc_frags),
            short_name="duration",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["second"].odx_id),
            is_visible_raw=None,
            sdgs=[],
        ),
    "temperature":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.temperature", doc_frags),
            short_name="temperature",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["celsius"].odx_id),
            is_visible_raw=None,
            sdgs=[],
        ),
    "error_code":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.error_code", doc_frags),
            short_name="error_code",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "boolean":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.boolean", doc_frags),
            short_name="boolean",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(
                DataType.A_UNICODE2STRING, display_radix=None, precision=None),
            compu_method=somersault_compumethods["boolean"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "uint8":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.uint8", doc_frags),
            short_name="uint8",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(DataType.A_UINT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
    "float":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.float", doc_frags),
            short_name="float",
            long_name=None,
            description=None,
            diag_coded_type=somersault_diagcodedtypes["float32"],
            physical_type=PhysicalType(DataType.A_FLOAT32, display_radix=None, precision=None),
            compu_method=somersault_compumethods["float_passthrough"],
            unit_ref=None,
            is_visible_raw=None,
            sdgs=[],
        ),
}

last_flip_details_table_id = OdxLinkId("somersault.table.last_flip_details", doc_frags)
last_flip_details_table_ref = OdxLinkRef.from_id(last_flip_details_table_id)

# positive responses
somersault_positive_responses = {
    "session":
        Response(
            odx_id=OdxLinkId("somersault.PR.session_start", doc_frags),
            short_name="session",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(
                            SID.DiagnosticSessionControl.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    ValueParameter(
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
                ],
            ),
            byte_size=None,
        ),
    "tester_ok":
        Response(
            odx_id=OdxLinkId("somersault.PR.tester_present", doc_frags),
            short_name="tester_present",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint16"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(
                            SID.TesterPresent.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    CodedConstParameter(
                        short_name="status",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=1,
                        coded_value=0x00,
                        bit_position=None,
                        sdgs=[],
                    ),
                ],
            ),
            byte_size=None,
        ),
    "forward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_forward", doc_frags),
            short_name="grudging_forward",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(SID.ForwardFlip.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    # TODO (?): non-byte aligned MatchingRequestParameters
                    MatchingRequestParameter(
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
                ],
            ),
            byte_size=None,
        ),
    "forward_flips_happily_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.happy_forward", doc_frags),
            short_name="happy_forward",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(SID.ForwardFlip.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    # TODO (?): non-byte aligned MatchingRequestParameters
                    MatchingRequestParameter(
                        short_name="num_flips_done",
                        long_name=None,
                        semantic=None,
                        description=None,
                        request_byte_position=3,
                        byte_position=1,
                        byte_length=1,
                        bit_position=None,
                        sdgs=[],
                    ),
                    ValueParameter(
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
                ],
            ),
            byte_size=None,
        ),
    "backward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_backward", doc_frags),
            short_name="grudging_backward",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(
                            SID.BackwardFlip.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    ValueParameter(
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
                ],
            ),
            byte_size=None,
        ),
    # Note that there is no such thing as a "backwards flip done happily"!
    "status_report":
        Response(
            odx_id=OdxLinkId("somersault.PR.status_report", doc_frags),
            short_name="status_report",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(
                            SID.ReadDataByIdentifier.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                    ValueParameter(
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
                        short_name="last_pos_response",
                        long_name=None,
                        semantic=None,
                        description=None,
                        table_key_ref=OdxLinkRef(
                            "somersault.PR.report_status.last_pos_response_key", doc_frags),
                        table_key_snref=None,
                        byte_position=None,
                        bit_position=None,
                        sdgs=[],
                    ),
                ],
            ),
            byte_size=None,
        ),
    "set_operation_params":
        Response(
            odx_id=OdxLinkId("somersault.PR.set_operation_params", doc_frags),
            short_name="set_operation_params",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
                        short_name="sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=0,
                        coded_value=uds.positive_response_id(
                            SID.ForwardFlipCondition.value),  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                ],
            ),
            byte_size=None,
        ),
}

# negative responses
somersault_negative_responses = {
    "general":
        Response(
            odx_id=OdxLinkId("somersault.NR.general_negative_response", doc_frags),
            short_name="general_negative_response",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="NEG-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                ],
            ),
            byte_size=None,
        ),
    # the tester present request needs separate negative and positive
    # responses because it must be fully specified a-priory to be able
    # to extract it for the COMPARAMS.
    "tester_nok":
        Response(
            odx_id=OdxLinkId("somersault.NR.tester_nok", doc_frags),
            short_name="tester_nok",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="NEG-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                        short_name="rq_sid",
                        long_name=None,
                        semantic=None,
                        description=None,
                        diag_coded_type=somersault_diagcodedtypes["uint8"],
                        byte_position=1,
                        coded_value=uds.SID.TesterPresent.value,  # type: ignore
                        bit_position=None,
                        sdgs=[],
                    ),
                ],
            ),
            byte_size=None,
        ),
    "flips_not_done":
        Response(
            odx_id=OdxLinkId("somersault.NR.flips_not_done", doc_frags),
            short_name="flips_not_done",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="NEG-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                ],
            ),
            byte_size=None,
        ),
}

somersault_global_negative_responses = {
    "general":
        Response(
            odx_id=OdxLinkId("GNR.too_hot", doc_frags),
            short_name="too_hot",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="GLOBAL-NEG-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                ],
            ),
            byte_size=None,
        )
}

# tables
flip_quality_table_id = OdxLinkId("somersault.table.flip_quality", doc_frags)
flip_quality_table_ref = OdxLinkRef.from_id(flip_quality_table_id)
somersault_tables = {
    "last_flip_details":
        Table(
            odx_id=last_flip_details_table_id,
            short_name="last_flip_details",
            long_name="Flip Details",
            description="<p>The details the last successfully executed request</p>",
            semantic="DETAILS",
            admin_data=None,
            key_label="key",
            struct_label="response",
            key_dop_ref=OdxLinkRef.from_id(somersault_dops["uint8"].odx_id),
            table_rows_raw=[
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.none", doc_frags),
                    short_name="none",
                    long_name="No Flips Done Yet",
                    key_raw="0",
                    structure_ref=None,
                    structure_snref=None,
                    description="<p>We have not done any flips yet!</p>",
                    semantic="DETAILS-KEY",
                    dop_ref=OdxLinkRef.from_id(somersault_dops["soberness_check"].odx_id),
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_grudging",
                                     doc_frags),
                    short_name="forward_grudging",
                    long_name="Forward Flips Grudgingly Done",
                    key_raw="3",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_positive_responses["forward_flips_grudgingly_done"].odx_id),
                    structure_snref=None,
                    description="<p>The the last forward flip was grudgingly done</p>",
                    semantic="DETAILS-KEY",
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_happy", doc_frags),
                    short_name="forward_happily",
                    long_name="Forward Flips Happily Done",
                    description=None,
                    semantic=None,
                    key_raw="5",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_positive_responses["forward_flips_happily_done"].odx_id),
                    structure_snref=None,
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.backward", doc_frags),
                    short_name="backward_grudging",
                    long_name="Backward Flips",
                    description=None,
                    semantic=None,
                    key_raw="10",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_positive_responses["backward_flips_grudgingly_done"].odx_id),
                    structure_snref=None,
                    dop_ref=None,
                    dop_snref=None,
                    sdgs=[],
                ),
            ],
            sdgs=[],
        )
}

# muxs
somersault_muxs = {
    "flip_preference":
        Multiplexer(
            odx_id=OdxLinkId("somersault.multiplexer.flip_preference", doc_frags),
            short_name="flip_preference",
            long_name="Flip Preference",
            description=None,
            is_visible_raw=None,
            sdgs=[],
            byte_position=0,
            switch_key=MultiplexerSwitchKey(
                byte_position=0,
                bit_position=0,
                dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
            default_case=MultiplexerDefaultCase(
                short_name="default_case",
                long_name="Default Case",
                structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
            cases=[
                MultiplexerCase(
                    short_name="forward_flip",
                    long_name="Forward Flip",
                    lower_limit="1",
                    upper_limit="3",
                    structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
                ),
                MultiplexerCase(
                    short_name="backward_flip",
                    long_name="Backward Flip",
                    lower_limit="1",
                    upper_limit="3",
                    structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
                ),
            ],
        )
}

# env-data
somersault_env_datas = {
    "flip_env_data":
        EnvironmentData(
            odx_id=OdxLinkId("somersault.env_data.flip_env_data", doc_frags),
            short_name="flip_env_data",
            long_name="Flip Env Data",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            byte_size=None,
            dtc_values=[],
            parameters=[
                ValueParameter(
                    short_name="flip_speed",
                    long_name="Flip Speed",
                    description=None,
                    physical_default_value_raw=None,
                    byte_position=0,
                    semantic="DATA",
                    dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
                PhysicalConstantParameter(
                    short_name="flip_direction",
                    long_name="Flip Direction",
                    description=None,
                    byte_position=1,
                    semantic="DATA",
                    physical_constant_value="1",
                    dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
                    dop_snref=None,
                    bit_position=None,
                    sdgs=[],
                ),
            ],
        )
}

# env-data-desc
somersault_env_data_descs = {
    "flip_env_data_desc":
        EnvironmentDataDescription(
            odx_id=OdxLinkId("somersault.env_data_desc.flip_env_data_desc", doc_frags),
            short_name="flip_env_data_desc",
            long_name="Flip Env Data Desc",
            description=None,
            param_snref="flip_speed",
            param_snpathref=None,
            is_visible_raw=None,
            env_datas=[],
            env_data_refs=[OdxLinkRef("somersault.env_data.flip_env_data", doc_frags)],
            sdgs=[],
        )
}

# requests
somersault_requests = {
    "start_session":
        Request(
            odx_id=OdxLinkId("somersault.RQ.start_session", doc_frags),
            short_name="start_session",
            long_name="Start the diagnostic session & do some mischief",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.DiagnosticSessionControl.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
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
            byte_size=None,
        ),
    "stop_session":
        Request(
            odx_id=OdxLinkId("somersault.RQ.stop_session", doc_frags),
            short_name="stop_session",
            long_name="Terminate the current diagnostic session",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.DiagnosticSessionControl.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
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
            byte_size=None,
        ),
    "tester_present":
        Request(
            odx_id=OdxLinkId("somersault.RQ.tester_present", doc_frags),
            short_name="tester_present",
            long_name="Prevent the current diagnostic session from timing out",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.TesterPresent.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
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
            byte_size=None,
        ),
    "set_operation_params":
        Request(
            odx_id=OdxLinkId("somersault.RQ.set_operation_params", doc_frags),
            short_name="set_operation_params",
            long_name="Specify the mode of operation for the ECU; e.g. if rings "
            "of fire ought to be used for maximum effect",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ForwardFlipCondition.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
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
            byte_size=None,
        ),
    "forward_flips":
        Request(
            odx_id=OdxLinkId("somersault.RQ.do_forward_flips", doc_frags),
            short_name="do_forward_flips",
            long_name="Do forward somersaults & some other mischief",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ForwardFlip.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
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
            byte_size=None,
        ),
    "backward_flips":
        Request(
            odx_id=OdxLinkId("somersault.RQ.do_backward_flips", doc_frags),
            short_name="do_backward_flips",
            long_name="Do a backward somersault & some other mischief",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.BackwardFlip.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                ValueParameter(
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
            byte_size=None,
        ),
    "report_status":
        Request(
            odx_id=OdxLinkId("somersault.RQ.report_status", doc_frags),
            short_name="report_status",
            long_name="Report back the current level of dizzy- & happiness.",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    long_name=None,
                    semantic=None,
                    description=None,
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value=SID.ReadDataByIdentifier.value,  # type: ignore
                    bit_position=None,
                    sdgs=[],
                ),
                CodedConstParameter(
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
            byte_size=None,
        ),
}

# services
somersault_services = {
    "start_session":
        DiagService(
            odx_id=OdxLinkId("somersault.service.session_start", doc_frags),
            short_name="session_start",
            long_name=None,
            description=None,
            admin_data=None,
            audience=None,
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request=OdxLinkRef.from_id(somersault_requests["start_session"].odx_id),
            semantic="SESSION",
            positive_responses=[
                OdxLinkRef.from_id(somersault_positive_responses["session"].odx_id),
            ],
            negative_responses=[
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
            short_name="session_stop",
            long_name=None,
            description=None,
            admin_data=None,
            audience=None,
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="SESSION",
            request=OdxLinkRef.from_id(somersault_requests["stop_session"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(somersault_positive_responses["session"].odx_id),
            ],
            negative_responses=[
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
            short_name="tester_present",
            long_name=None,
            description=None,
            admin_data=None,
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
            request=OdxLinkRef.from_id(somersault_requests["tester_present"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(somersault_positive_responses["tester_ok"].odx_id),
            ],
            negative_responses=[
                OdxLinkRef.from_id(somersault_negative_responses["tester_nok"].odx_id),
            ],
            sdgs=[],
        ),
    "set_operation_params":
        DiagService(
            odx_id=OdxLinkId("somersault.service.set_operation_params", doc_frags),
            short_name="set_operation_params",
            long_name=None,
            description=None,
            admin_data=None,
            audience=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            semantic="FUNCTION",
            request=OdxLinkRef.from_id(somersault_requests["set_operation_params"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(somersault_positive_responses["set_operation_params"].odx_id),
            ],
            negative_responses=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            sdgs=[],
        ),
    "forward_flips":
        DiagService(
            odx_id=OdxLinkId("somersault.service.do_forward_flips", doc_frags),
            short_name="do_forward_flips",
            long_name=None,
            description="<p>Do a forward flip.</p>",
            admin_data=None,
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
            request=OdxLinkRef.from_id(somersault_requests["forward_flips"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(
                    somersault_positive_responses["forward_flips_grudgingly_done"].odx_id),
                # TODO: implement handling of multiple responses
                # OdxLinkRef.from_id(somersault_positive_responses["forward_flips_happily_done"].odx_id),
            ],
            negative_responses=[
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
            short_name="do_backward_flips",
            long_name=None,
            description=None,
            admin_data=None,
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
            request=OdxLinkRef.from_id(somersault_requests["backward_flips"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(
                    somersault_positive_responses["backward_flips_grudgingly_done"].odx_id),
            ],
            negative_responses=[
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
            short_name="report_status",
            long_name=None,
            description=None,
            admin_data=None,
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
            request=OdxLinkRef.from_id(somersault_requests["report_status"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(somersault_positive_responses["status_report"].odx_id),
            ],
            negative_responses=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
            sdgs=[],
        ),
}

somersault_single_ecu_jobs = {
    "compulsory_program":
        SingleEcuJob(
            oid=None,
            audience=None,
            odx_id=OdxLinkId("somersault.service.compulsory_program", doc_frags),
            short_name="compulsory_program",
            long_name="Compulsory Program",
            description="<p>Do several fancy moves.</p>",
            admin_data=None,
            semantic=None,
            functional_class_refs=[],
            diagnostic_class=None,
            prog_codes=[
                ProgCode(
                    code_file="jobs.jar",
                    encryption=None,
                    syntax="JAR",
                    entrypoint="com.supervisor.jobs.CompulsoryProgram",
                    revision="1.23.4",
                    library_refs=[],
                ),
            ],
            input_params=[],
            output_params=[],
            neg_output_params=[],
            is_mandatory_raw=None,
            is_executable_raw=None,
            is_final_raw=None,
            sdgs=[],
        )
}


# communication parameters
def extract_constant_bytes(params):
    const_params = [x.coded_value for x in params if isinstance(x, CodedConstParameter)]
    return bytes(const_params).hex()


tester_present_value = extract_constant_bytes(somersault_requests["tester_present"].parameters)
tester_pr_value = extract_constant_bytes(somersault_positive_responses["tester_ok"].parameters)
tester_nr_value = extract_constant_bytes(somersault_negative_responses["tester_nok"].parameters)
somersault_communication_parameters = [
    ###
    # basic parameters
    ###
    # bus speed
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_11898_2_DWCAN.CP_Baudrate", cp_dwcan_doc_frags),
        value="500000",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # parameters of the CAN diagnostics frames
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_2.CP_UniqueRespIdTable", cp_iso15765_2_doc_frags),
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
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # timeout for responses [us]
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_RC21CompletionTimeout", cp_iso15765_3_doc_frags),
        value="1000000",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    ###
    # "tester present" message handling
    ###
    # expected "tester present" message
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentMessage", cp_iso15765_3_doc_frags),
        value=f"{tester_present_value}",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # a response is mandatory
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # positive response to "tester present"
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpPosResp", cp_iso15765_3_doc_frags),
        value=f"{tester_pr_value}",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # negative response to "tester present"
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpNegResp", cp_iso15765_3_doc_frags),
        value=f"{tester_nr_value}",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # when a tester present message must be send
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentSendType", cp_iso15765_3_doc_frags),
        value="On idle",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # "tester present" messages are send directly to the CAN IDs
    # (i.e., they are not embedded in the ISO-TP telegram?)
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentAddrMode", cp_iso15765_3_doc_frags),
        value="Physical",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    # is a response from the ECU to "tester present" messages expected
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
    ###
    # ISO-TP parameters:
    ###
    # maximum number of frames between flow control ACKs
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_2.CP_BlockSize", cp_iso15765_2_doc_frags),
        value="4",
        protocol_snref="MyProtocol",
        prot_stack_snref=None,
        is_functional=False,
        description=None,
    ),
]

somersault_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=NamedItemList(short_name_as_id, somersault_dops.values()),
    unit_spec=UnitSpec(
        unit_groups=list(somersault_unit_groups.values()),
        units=list(somersault_units.values()),
        physical_dimensions=list(somersault_physical_dimensions.values()),
        sdgs=[],
    ),
    tables=NamedItemList(short_name_as_id, somersault_tables.values()),
    muxs=NamedItemList(short_name_as_id, somersault_muxs.values()),
    env_datas=NamedItemList(short_name_as_id, somersault_env_datas.values()),
    env_data_descs=NamedItemList(short_name_as_id, somersault_env_data_descs.values()),
    dtc_dops=NamedItemList(short_name_as_id),
    structures=NamedItemList(short_name_as_id),
    end_of_pdu_fields=NamedItemList(short_name_as_id),
    sdgs=[],
)

# diagnostics layer
somersault_diaglayer_raw = DiagLayerRaw(
    variant_type=DiagLayerType.BASE_VARIANT,
    odx_id=OdxLinkId("somersault", doc_frags),
    short_name="somersault",
    long_name="Somersault base variant",
    description="<p>Base variant of the somersault ECU &amp; cetera</p>",
    admin_data=None,
    company_datas=NamedItemList(short_name_as_id),
    functional_classes=NamedItemList(short_name_as_id, somersault_functional_classes.values()),
    diag_data_dictionary_spec=somersault_diag_data_dictionary_spec,
    diag_comms=[*somersault_services.values(), *somersault_single_ecu_jobs.values()],
    requests=NamedItemList(short_name_as_id, somersault_requests.values()),
    positive_responses=NamedItemList(short_name_as_id, somersault_positive_responses.values()),
    negative_responses=NamedItemList(short_name_as_id, somersault_negative_responses.values()),
    global_negative_responses=NamedItemList(short_name_as_id,
                                            somersault_global_negative_responses.values()),
    import_refs=[],
    state_charts=NamedItemList(short_name_as_id),
    additional_audiences=NamedItemList(short_name_as_id, somersault_additional_audiences.values()),
    sdgs=[],
    parent_refs=[],
    communication_parameters=somersault_communication_parameters,
    ecu_variant_patterns=[],
)
somersault_diaglayer = DiagLayer(diag_layer_raw=somersault_diaglayer_raw)

##################
# Lazy variant of Somersault ECU: this one is lazy and cuts corners
##################

somersault_lazy_diaglayer_raw = DiagLayerRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_lazy", doc_frags),
    short_name="somersault_lazy",
    long_name="Somersault lazy ECU",
    description="<p>Sloppy variant of the somersault ECU (lazy &lt; assiduous)</p>",
    admin_data=None,
    company_datas=NamedItemList(short_name_as_id),
    functional_classes=NamedItemList(short_name_as_id),
    diag_data_dictionary_spec=None,
    diag_comms=[],
    requests=NamedItemList(short_name_as_id),
    positive_responses=NamedItemList(short_name_as_id),
    negative_responses=NamedItemList(short_name_as_id),
    global_negative_responses=NamedItemList(short_name_as_id),
    import_refs=[],
    state_charts=NamedItemList(short_name_as_id),
    additional_audiences=NamedItemList(short_name_as_id),
    sdgs=[],
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_diaglayer.odx_id),
            # this variant does not do backflips
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
    communication_parameters=somersault_communication_parameters,
    ecu_variant_patterns=[],
)
somersault_lazy_diaglayer = DiagLayer(diag_layer_raw=somersault_lazy_diaglayer_raw)

##################
# Assiduous production variant of Somersault ECU: This one works
# harder than it needs to
##################

# the assiduous ECU also does headstands...
somersault_assiduous_requests = {
    "headstand":
        Request(
            odx_id=OdxLinkId("somersault_assiduous.RQ.do_headstand", doc_frags),
            short_name="do_headstand",
            long_name="Do a headstand & whatever else is required to entertain the customer",
            description=None,
            sdgs=[],
            is_visible_raw=None,
            parameters=[
                CodedConstParameter(
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
            ],
            byte_size=None,
        ),
}

# positive responses
somersault_assiduous_positive_responses = {
    "headstand_done":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.PR.headstand_done", doc_frags),
            short_name="headstand_done",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                ],
            ),
            byte_size=None,
        ),
}

# negative responses
somersault_assiduous_negative_responses = {
    "fell_over":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.NR.fell_over", doc_frags),
            short_name="fell_over",
            long_name=None,
            description=None,
            sdgs=[],
            is_visible_raw=None,
            response_type="POS-RESPONSE",
            parameters=NamedItemList(
                short_name_as_id,
                [
                    CodedConstParameter(
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
                ],
            ),
            byte_size=None,
        ),
}

# services
somersault_assiduous_services = {
    "headstand":
        DiagService(
            odx_id=OdxLinkId("somersault_assiduous.service.headstand", doc_frags),
            short_name="headstand",
            long_name=None,
            description=None,
            admin_data=None,
            semantic=None,
            functional_class_refs=[],
            pre_condition_state_refs=[],
            state_transition_refs=[],
            request=OdxLinkRef.from_id(somersault_assiduous_requests["headstand"].odx_id),
            positive_responses=[
                OdxLinkRef.from_id(
                    somersault_assiduous_positive_responses["headstand_done"].odx_id),
            ],
            negative_responses=[
                OdxLinkRef.from_id(somersault_assiduous_negative_responses["fell_over"].odx_id),
            ],
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

somersault_assiduous_diaglayer_raw = DiagLayerRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_assiduous", doc_frags),
    short_name="somersault_assiduous",
    long_name="Somersault assiduous ECU",
    description="<p>Hard-working variant of the somersault ECU (lazy &lt; assiduous)</p>",
    admin_data=None,
    company_datas=NamedItemList(short_name_as_id),
    functional_classes=NamedItemList(short_name_as_id),
    diag_data_dictionary_spec=DiagDataDictionarySpec(
        dtc_dops=NamedItemList(short_name_as_id),
        data_object_props=NamedItemList(short_name_as_id),
        structures=NamedItemList(short_name_as_id),
        end_of_pdu_fields=NamedItemList(short_name_as_id),
        tables=NamedItemList(short_name_as_id),
        env_data_descs=NamedItemList(short_name_as_id),
        env_datas=NamedItemList(short_name_as_id),
        muxs=NamedItemList(short_name_as_id),
        unit_spec=None,
        sdgs=[],
    ),
    diag_comms=list(somersault_assiduous_services.values()),
    requests=NamedItemList(short_name_as_id, somersault_assiduous_requests.values()),
    positive_responses=NamedItemList(short_name_as_id,
                                     somersault_assiduous_positive_responses.values()),
    negative_responses=NamedItemList(short_name_as_id,
                                     somersault_assiduous_negative_responses.values()),
    global_negative_responses=NamedItemList(short_name_as_id),
    import_refs=[],
    state_charts=NamedItemList(short_name_as_id),
    additional_audiences=NamedItemList(short_name_as_id),
    sdgs=[],
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_diaglayer.odx_id),
            # this variant does everything which the base variant does
            not_inherited_diag_comms=[],
            not_inherited_dops=[],
            not_inherited_variables=[],
            not_inherited_tables=[],
            not_inherited_global_neg_responses=[],
        )
    ],
    communication_parameters=somersault_communication_parameters,
    ecu_variant_patterns=[],
)
somersault_assiduous_diaglayer = DiagLayer(diag_layer_raw=somersault_assiduous_diaglayer_raw)

##################
# Container with all ECUs
##################

# create a "diagnosis layer container" object
somersault_dlc = DiagLayerContainer(
    odx_id=OdxLinkId("DLC.somersault", doc_frags),
    short_name=dlc_short_name,
    long_name="Collect all saults in the summer",
    description="<p>This contains ECUs which do somersaults &amp; cetera</p>",
    admin_data=somersault_admin_data,
    company_datas=NamedItemList(
        short_name_as_id,
        [
            somersault_company_datas["suncus"],
            somersault_company_datas["acme"],
        ],
    ),
    base_variants=[somersault_diaglayer],
    ecu_variants=[somersault_lazy_diaglayer, somersault_assiduous_diaglayer],
    ecu_shared_datas=[],
    protocols=[],
    functional_groups=[],
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
):
    odx_cs_root = ElementTree.parse(odx_cs_dir / odx_cs_filename).getroot()
    subset = odx_cs_root.find("COMPARAM-SUBSET")
    if subset is not None:
        comparam_subsets.append(ComparamSubset.from_et(subset))

# create a database object
database = Database()
database._diag_layer_containers = NamedItemList(short_name_as_id, [somersault_dlc])
database._comparam_subsets = NamedItemList(short_name_as_id, comparam_subsets)

# Create ID mapping and resolve references
database.refresh()

# delete all variables except "database"
for name in dir():
    if name not in (
            "database",
            "SID",
    ):
        del globals()[name]
del globals()["name"]
