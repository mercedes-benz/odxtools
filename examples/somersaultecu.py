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
from odxtools.admindata import (AdminData, CompanyDocInfo, DocRevision,
                                Modification)
from odxtools.audience import AdditionalAudience, Audience
from odxtools.communicationparameter import CommunicationParameterRef
from odxtools.companydata import (CompanyData, CompanySpecificInfo, RelatedDoc,
                                  TeamMember, XDoc)
from odxtools.comparam_subset import ComparamSubset
from odxtools.compumethods import (CompuScale, IdenticalCompuMethod, Limit,
                                   TexttableCompuMethod)
from odxtools.database import Database
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.diagcodedtypes import StandardLengthType
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayer import DiagLayer, DiagLayerContainer
from odxtools.diaglayertype import DIAG_LAYER_TYPE
from odxtools.envdata import EnvironmentData
from odxtools.envdatadesc import EnvironmentDataDescription
from odxtools.functionalclass import FunctionalClass
from odxtools.multiplexer import (Multiplexer, MultiplexerCase,
                                  MultiplexerDefaultCase, MultiplexerSwitchKey)
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxDocFragment, OdxLinkId, OdxLinkRef
from odxtools.odxtypes import DataType
from odxtools.parameters import (CodedConstParameter, MatchingRequestParameter,
                                 NrcConstParameter, ValueParameter)
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
SID: Any = IntEnum('SID', tmp) # type: ignore

dlc_short_name = "somersault"

# document fragment for everything except the communication parameters
doc_frags = [ OdxDocFragment(dlc_short_name, "CONTAINER") ]

# document fragments for communication parameters
cp_dwcan_doc_frags = [ OdxDocFragment("ISO_11898_2_DWCAN", "COMPARAM-SUBSET") ]
cp_iso15765_2_doc_frags = [ OdxDocFragment("ISO_15765_2", "COMPARAM-SUBSET") ]
cp_iso15765_3_doc_frags = [ OdxDocFragment("ISO_15765_3", "COMPARAM-SUBSET") ]

##################
# Base variant of Somersault ECU
##################

# company datas
somersault_team_members = {
    "doggy":
    TeamMember(odx_id=OdxLinkId("TM.Doggy", doc_frags),
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
               email="info@suncus.com"),

    "horsey":
    TeamMember(odx_id=OdxLinkId("TM.Horsey", doc_frags),
               short_name="Horsey",
               long_name="Horsey the horse",
               description="<p>Trustworthy worker</p>",
               roles=["gymnast" ],
               department="haulers",
               address="Some road",
               zip="12345",
               city="New Dogsville",
               phone="+0 1234/5678-91",
               fax="+0 1234/5678-0",
               email="info@suncus.com"),

    "slothy":
    TeamMember(odx_id=OdxLinkId("TM.Slothy", doc_frags),
               short_name="Slothy")
}

somersault_company_datas = {
    "suncus":
    CompanyData(odx_id=OdxLinkId("CD.Suncus", doc_frags),
                short_name="Suncus",
                long_name="Circus of the sun",
                description="<p>Prestigious group of performers</p>",
                roles=["circus", "gym"],
                team_members=NamedItemList(short_name_as_id,
                                           [
                                               somersault_team_members["doggy"],
                                               somersault_team_members["horsey"],
                                           ]),
                company_specific_info=CompanySpecificInfo(
                    related_docs=[
                        RelatedDoc(
                            description="<p>We are the best!</p>",
                            xdoc=XDoc(short_name="best",
                                      long_name="suncus is the best",
                                      description="<p>great propaganda...</p>",
                                      number="1",
                                      state="published",
                                      date="2015-01-15T20:15:20+05:00",
                                      publisher="Suncus Publishing",
                                      url="https://suncus-is-the-best.com",
                                      position="first!")),
                    ]),
                ),

    "acme":
    CompanyData(odx_id=OdxLinkId("CD.ACME", doc_frags),
                short_name="ACME_Corporation",
                team_members=NamedItemList(short_name_as_id,
                                           [
                                               somersault_team_members["slothy"],
                                           ]),
                ),

}

somersault_admin_data = \
    AdminData(language="en-US",
              company_doc_infos=\
              [
                  CompanyDocInfo(company_data_ref=OdxLinkRef("CD.Suncus", doc_frags),
                                 team_member_ref=OdxLinkRef("TM.Doggy", doc_frags),
                                 doc_label="A really meaningful label"),
              ],
              doc_revisions=\
              [
                  DocRevision(team_member_ref=OdxLinkRef("TM.Doggy", doc_frags),
                              revision_label="1.0",
                              state="draft",
                              date="1926-07-18T11:11:11+01:00",
                              tool="odxtools 0.0.1",
                              modifications=[
                                  Modification(change="add somersault ECU",
                                               reason="we needed a new artist"),
                                  Modification(change="increase robustness to dizzyness",
                                               reason="No alcohol anymore"),
                              ]),
                  DocRevision(team_member_ref=OdxLinkRef("TM.Horsey", doc_frags),
                              revision_label="1.1",
                              state="released",
                              date="2020-08-19T12:12:12+08:00",
                              tool="odxtools 0.1",
                              modifications=[
                                  Modification(change="rename somersault ECU to somersault_assiduous to enable slothy to add somersault_lazy"),
                              ]),

                  DocRevision(team_member_ref=OdxLinkRef("TM.Slothy", doc_frags),
                              revision_label="1.0.3.2.1.5.6",
                              date="1900-01-01T00:00:00+00:00"),
              ])

# functional classes
somersault_functional_classes = {
    "flip":
    FunctionalClass(
        odx_id=OdxLinkId("somersault.FNC.flip", doc_frags),
        short_name="flip",
        long_name="Flip"),

    "session":
    FunctionalClass(
        odx_id=OdxLinkId("somersault.FNC.session", doc_frags),
        short_name="session",
        long_name="Session"),
}

# additional audiences
somersault_additional_audiences = {
    "attentive_admirer":
    AdditionalAudience(
        odx_id=OdxLinkId("somersault.AA.attentive_admirer", doc_frags),
        short_name="attentive_admirer",
        long_name="Attentive Admirer"),

    "anyone":
    AdditionalAudience(
        odx_id=OdxLinkId("somersault.AA.anyone", doc_frags),
        short_name="anyone",
        long_name="Anyone"),
}

# diag coded types
somersault_diagcodedtypes = {
    "flag":
    StandardLengthType(
        base_data_type="A_UINT32",
        bit_length=1),

    "uint8":
    StandardLengthType(
        base_data_type="A_UINT32",
        bit_length=8),

    "uint16":
    StandardLengthType(
        base_data_type="A_UINT32",
        bit_length=16),
}

somersault_physical_dimensions = {
    "second": PhysicalDimension(
        odx_id=OdxLinkId("somersault.PD.second", doc_frags),
        short_name="second",
        long_name="Second",
        time_exp=1
    )
}

somersault_units = {
    "second":
        Unit(
            odx_id=OdxLinkId("somersault.unit.second", doc_frags),
            short_name="second",
            display_name="s",
            long_name="Second",
            description="<p>SI unit for the time</p>",
            factor_si_to_unit=1,
            offset_si_to_unit=0,
            physical_dimension_ref=OdxLinkRef.from_id(somersault_physical_dimensions["second"].odx_id)
        ),
    "minute":
        Unit(
            odx_id=OdxLinkId("somersault.unit.minute", doc_frags),
            short_name="minute",
            display_name="min",
            long_name="Minute",
            factor_si_to_unit=60,
            offset_si_to_unit=0,
            physical_dimension_ref=OdxLinkRef.from_id(somersault_physical_dimensions["second"].odx_id)
        ),
}

somersault_unit_groups = {
    "european_duration":
        UnitGroup(
            short_name="european_duration",
            category="COUNTRY",
            unit_refs=[
                OdxLinkRef.from_id(somersault_units["second"].odx_id),
                OdxLinkRef.from_id(somersault_units["minute"].odx_id)],
            long_name="Duration",
            description="<p>Units for measuring a duration</p>"
        ),
}

# computation methods
somersault_compumethods = {
    "uint_passthrough":
    IdenticalCompuMethod(
        internal_type="A_UINT32",
        physical_type="A_UINT32"),

    "boolean":
    TexttableCompuMethod(
        internal_type="A_UINT32",
        internal_to_phys=[
            CompuScale(compu_const="false",
                       lower_limit=Limit(0),
                       upper_limit=Limit(0)
                       ),
            CompuScale(compu_const="true",
                       lower_limit=Limit(1),
                       upper_limit=Limit(1)
                       ),
        ])
}

# data object properties
somersault_dops = {
    "num_flips":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.num_flips", doc_frags),
        short_name="num_flips",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "soberness_check":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.soberness_check", doc_frags),
        short_name="soberness_check",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "dizzyness_level":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.dizzyness_level", doc_frags),
        short_name="dizzyness_level",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "happiness_level":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.happiness_level", doc_frags),
        short_name="happiness_level",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "duration":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.duration", doc_frags),
        short_name="duration",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"],
        unit_ref=OdxLinkRef.from_id(somersault_units["second"].odx_id)),

    "error_code":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.error_code", doc_frags),
        short_name="error_code",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UINT32),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "boolean":
    DataObjectProperty(
        odx_id=OdxLinkId("somersault.DOP.boolean", doc_frags),
        short_name="boolean",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType(DataType.A_UNICODE2STRING),
        compu_method=somersault_compumethods["boolean"]),
}

# tables
somersault_tables = {
    "flip_quality": Table(
        odx_id=OdxLinkId("somersault.table.flip_quality", doc_frags),
        short_name="flip_quality",
        long_name="Flip Quality",
        description="<p>The quality the flip (average, good or best)</p>",
        semantic="QUALITY",
        key_dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
        table_rows=[
            TableRow(
                odx_id=OdxLinkId("somersault.table.flip_quality.average", doc_frags),
                short_name="average",
                long_name="Average",
                key=3,
                structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
                description="<p>The quality of the flip is average</p>",
                semantic="QUALITY-KEY",
            ),
            TableRow(
                odx_id=OdxLinkId("somersault.table.flip_quality.good", doc_frags),
                short_name="good",
                long_name="Good",
                key=5,
                structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
            TableRow(
                odx_id=OdxLinkId("somersault.table.flip_quality.best", doc_frags),
                short_name="best",
                long_name="Best",
                key=10,
                structure_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
        ]
    )

}

# muxs
somersault_muxs = {
    "flip_preference": Multiplexer(
        odx_id=OdxLinkId("somersault.multiplexer.flip_preference", doc_frags),
        short_name="flip_preference",
        long_name="Flip Preference",
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
            )
        ]
    )
}

# env-data
somersault_env_datas = {
    "flip_env_data": EnvironmentData(
        odx_id=OdxLinkId("somersault.env_data.flip_env_data", doc_frags),
        short_name="flip_env_data",
        long_name="Flip Env Data",
        parameters=[
            ValueParameter(
                short_name="flip_speed",
                long_name="Flip Speed",
                byte_position=0,
                semantic="DATA",
                dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
            PhysicalConstantParameter(
                short_name="flip_direction",
                long_name="Flip Direction",
                byte_position=1,
                semantic="DATA",
                physical_constant_value=1,
                dop_ref=OdxLinkRef.from_id(somersault_dops["num_flips"].odx_id),
            ),
        ]
    )
}

# env-data-desc
somersault_env_data_descs = {
    "flip_env_data_desc": EnvironmentDataDescription(
        odx_id=OdxLinkId("somersault.env_data_desc.flip_env_data_desc", doc_frags),
        short_name="flip_env_data_desc",
        long_name="Flip Env Data Desc",
        param_snref="flip_speed",
        env_datas=[],
        env_data_refs=[OdxLinkRef("somersault.env_data.flip_env_data", doc_frags)],
    )
}

# requests
somersault_requests = {
    "start_session":
    Request(
        odx_id=OdxLinkId("somersault.RQ.start_session", doc_frags),
        short_name="start_session",
        long_name="Start the diagnostic session & do some mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.DiagnosticSessionControl.value, # type: ignore
            ),
            CodedConstParameter(
                short_name="odx_id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x0,
            ),
        ]
    ),

    "stop_session":
    Request(
        odx_id=OdxLinkId("somersault.RQ.stop_session", doc_frags),
        short_name="stop_session",
        long_name="Terminate the current diagnostic session",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.DiagnosticSessionControl.value, # type: ignore
            ),
            CodedConstParameter(
                short_name="odx_id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x1,
            ),
        ]
    ),

    "tester_present":
    Request(
        odx_id=OdxLinkId("somersault.RQ.tester_present", doc_frags),
        short_name="tester_present",
        long_name="Prevent the current diagnostic session from timing out",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.TesterPresent.value # type: ignore
            ),
            CodedConstParameter(
                short_name="odx_id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x0
            ),
        ]
    ),

    "set_operation_params":
    Request(
        odx_id=OdxLinkId("somersault.RQ.set_operation_params", doc_frags),
        short_name="set_operation_params",
        long_name=\
        "Specify the mode of operation for the ECU; e.g. if rings "
        "of fire ought to be used for maximum effect",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ForwardFlipCondition.value, # type: ignore
            ),
            ValueParameter(
                short_name="use_fire_ring",
                byte_position=1,
                dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
            ),

        ]
    ),

    "forward_flips":
    Request(
        odx_id=OdxLinkId("somersault.RQ.do_forward_flips", doc_frags),
        short_name="do_forward_flips",
        long_name="Do forward somersaults & some other mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ForwardFlip.value # type: ignore
            ),
            ValueParameter(
                short_name="forward_soberness_check",
                dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                byte_position=1,
                #value must be 0x12 for the request to be accepted
            ),
            ValueParameter(
                short_name="num_flips",
                byte_position=2,
                dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags)),
        ]
    ),

    "backward_flips":
    Request(
        odx_id=OdxLinkId("somersault.RQ.do_backward_flips", doc_frags),
        short_name="do_backward_flips",
        long_name="Do a backward somersault & some other mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.BackwardFlip.value # type: ignore
            ),
            ValueParameter(
                short_name="backward_soberness_check",
                dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                byte_position=1,
                #value must be 0x21 for the request to be accepted
            ),
            ValueParameter(
                short_name="num_flips",
                byte_position=2,
                dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
            ),
        ]
    ),

    "report_status":
    Request(
        odx_id=OdxLinkId("somersault.RQ.report_status", doc_frags),
        short_name="report_status",
        long_name="Report back the current level of dizzy- & happiness.",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ReadDataByIdentifier.value, # type: ignore
            ),
            CodedConstParameter(
                short_name="odx_id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x0,
            ),
        ]
    ),
}


# positive responses
somersault_positive_responses = {
    "session":
    Response(odx_id=OdxLinkId("somersault.PR.session_start", doc_frags),
             short_name="session",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.DiagnosticSessionControl.value), # type: ignore
                 ),
                 ValueParameter(
                     short_name="can_do_backward_flips",
                     byte_position=1,
                     dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                 ),
             ]),

    "tester_ok":
    Response(odx_id=OdxLinkId("somersault.PR.tester_present", doc_frags),
             short_name="tester_present",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint16"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.TesterPresent.value), # type: ignore
                 ),
                 CodedConstParameter(
                     short_name="status",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=1,
                     coded_value=0x00,
                 ),
             ]),

    "forward_flips_grudgingly_done":
    Response(odx_id=OdxLinkId("somersault.PR.grudging_forward", doc_frags),
             short_name="grudging_forward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlip.value), # type: ignore
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=2,
                                          byte_position=1,
                                          byte_length=1),
             ]),

    "forward_flips_happily_done":
    Response(odx_id=OdxLinkId("somersault.PR.happy_forward", doc_frags),
             short_name="happy_forward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlip.value), # type: ignore
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=3,
                                          byte_position=1,
                                          byte_length=1),
                 ValueParameter(
                     short_name="yeha_level",
                     byte_position=2,
                     dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags)),
             ]),

    "backward_flips_grudgingly_done":
    Response(odx_id=OdxLinkId("somersault.PR.grudging_backward", doc_frags),
             short_name="grudging_backward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.BackwardFlip.value), # type: ignore
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=3,
                                          byte_position=1,
                                          byte_length=1),
             ]),

    # Note that there is no such thing as a "backwards flip done happily"!

    "status_report":
    Response(odx_id=OdxLinkId("somersault.PR.status_report", doc_frags),
             short_name="status_report",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ReadDataByIdentifier.value), # type: ignore
                 ),
                 ValueParameter(
                     short_name="dizzyness_level",
                     byte_position=1,
                     dop_ref=OdxLinkRef("somersault.DOP.dizzyness_level", doc_frags)),
                 ValueParameter(
                     short_name="happiness_level",
                     byte_position=2,
                     dop_ref=OdxLinkRef("somersault.DOP.happiness_level", doc_frags)),
             ]),

    "set_operation_params":
    Response(odx_id=OdxLinkId("somersault.PR.set_operation_params", doc_frags),
             short_name="set_operation_params",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlipCondition.value), # type: ignore
                 ),
             ]),
}

# negative responses
somersault_negative_responses = {
    "general":
    Response(odx_id=OdxLinkId("somersault.NR.general_negative_response", doc_frags),
             short_name="general_negative_response",
             response_type="NEG-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.NegativeResponseId,
                 ),
                 MatchingRequestParameter(short_name="rq_sid",
                                          request_byte_position=0,
                                          byte_position=1,
                                          byte_length=1),
                 ValueParameter(
                     short_name="response_code",
                     byte_position=2,
                     dop_ref=OdxLinkRef("somersault.DOP.error_code", doc_frags)),
             ]),

    # the tester present request needs separate negative and positive
    # responses because it must be fully specified a-priory to be able
    # to extract it for the COMPARAMS.
    "tester_nok":
    Response(odx_id=OdxLinkId("somersault.NR.tester_nok", doc_frags),
             short_name="tester_nok",
             response_type="NEG-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.NegativeResponseId,
                 ),
                 CodedConstParameter(
                     short_name="rq_sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=1,
                     coded_value=uds.SID.TesterPresent.value, # type: ignore
                 ),
             ]),

    "flips_not_done":
    Response(odx_id=OdxLinkId("somersault.NR.flips_not_done", doc_frags),
             short_name="flips_not_done",
             response_type="NEG-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.NegativeResponseId,
                 ),
                 MatchingRequestParameter(short_name="rq_sid",
                                          request_byte_position=0,
                                          byte_position=1,
                                          byte_length=1),
                 NrcConstParameter(
                     short_name="reason",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=2,
                     coded_values=[0, 1, 2]
                     # possible values (TODO: make this an enum parameter):
                     # 0 -> not sober
                     # 1 -> too dizzy
                     # 2 -> stumbled
                 ),
                 ValueParameter(
                     short_name="flips_successfully_done",
                     dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                     byte_position=3,
                 ),
             ]),
}

# services
somersault_services = {
    "start_session":
    DiagService(odx_id=OdxLinkId("somersault.service.session_start", doc_frags),
                short_name="session_start",
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
                ]
                ),

    "stop_session":
    DiagService(odx_id=OdxLinkId("somersault.service.session_stop", doc_frags),
                short_name="session_stop",
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
                ]
                ),

    "tester_present":
    DiagService(odx_id=OdxLinkId("somersault.service.tester_present", doc_frags),
                short_name="tester_present",
                semantic="TESTERPRESENT",
                request=OdxLinkRef.from_id(somersault_requests["tester_present"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_positive_responses["tester_ok"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_negative_responses["tester_nok"].odx_id),
                ],
                audience=Audience(
                    enabled_audience_refs=[
                        OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id),
                        OdxLinkRef.from_id(somersault_additional_audiences["anyone"].odx_id),
                    ],
                    is_development_raw=False)
                ),

    "set_operation_params":
    DiagService(odx_id=OdxLinkId("somersault.service.set_operation_params", doc_frags),
                short_name="set_operation_params",
                semantic="FUNCTION",
                request=OdxLinkRef.from_id(somersault_requests["set_operation_params"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_positive_responses["set_operation_params"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
                ],
                ),

    "forward_flips":
    DiagService(odx_id=OdxLinkId("somersault.service.do_forward_flips", doc_frags),
                short_name="do_forward_flips",
                description="<p>Do a forward flip.</p>",
                semantic="FUNCTION",
                request=OdxLinkRef.from_id(somersault_requests["forward_flips"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_positive_responses["forward_flips_grudgingly_done"].odx_id),
                    # TODO: implement handling of multiple responses
                    #OdxLinkRef.from_id(somersault_positive_responses["forward_flips_happily_done"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_negative_responses["flips_not_done"].odx_id),
                    # TODO (?): implement handling of multiple possible responses
                    #OdxLinkRef.from_id(somersault_negative_responses["stumbled"].odx_id),
                    #OdxLinkRef.from_id(somersault_negative_responses["too_dizzy"].odx_id),
                    #OdxLinkRef.from_id(somersault_negative_responses["not_sober"].odx_id),
                ],
                functional_class_refs=[
                    OdxLinkRef.from_id(somersault_functional_classes["flip"].odx_id)
                ],
                audience=Audience(
                    enabled_audience_refs=[OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)],
                    is_development_raw=False)
                ),

    "backward_flips":
    DiagService(odx_id=OdxLinkId("somersault.service.do_backward_flips", doc_frags),
                short_name="do_backward_flips",
                semantic="FUNCTION",
                request=OdxLinkRef.from_id(somersault_requests["backward_flips"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_positive_responses["backward_flips_grudgingly_done"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_negative_responses["flips_not_done"].odx_id),
                ],
                functional_class_refs=[
                    OdxLinkRef.from_id(somersault_functional_classes["flip"].odx_id)
                ],
                audience=Audience(
                    enabled_audience_refs=[OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)],
                    is_development_raw=False)
                ),

    "report_status":
    DiagService(odx_id=OdxLinkId("somersault.service.report_status", doc_frags),
                short_name="report_status",
                semantic="CURRENTDATA",
                request=OdxLinkRef.from_id(somersault_requests["report_status"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_positive_responses["status_report"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
                ],
                audience=Audience(
                    disabled_audience_refs=[OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)],
                    is_aftersales_raw=False,
                    is_aftermarket_raw=False)
                ),

}

somersault_single_ecu_jobs = {
    "compulsory_program":
    SingleEcuJob(odx_id=OdxLinkId("somersault.service.compulsory_program", doc_frags),
                 short_name="compulsory_program",
                 long_name="Compulsory Program",
                 description="<p>Do several fancy moves.</p>",
                 prog_codes=[
                    ProgCode(
                        code_file="jobs.jar",
                        syntax="JAR",
                        entrypoint="com.supervisor.jobs.CompulsoryProgram",
                        revision="1.23.4"
                    ),
                 ])
}

# communication parameters
def extract_constant_bytes(params):
    const_params = [ x.coded_value for x in params if isinstance(x, CodedConstParameter) ]
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
        value="500000"),

    # parameters of the CAN diagnostics frames
    CommunicationParameterRef(
        id_ref=OdxLinkRef('ISO_15765_2.CP_UniqueRespIdTable', cp_iso15765_2_doc_frags),
        value=[
            # CP_CanPhysReqFormat
            'normal segmented 11-bit transmit with FC',
            # CP_CanPhysReqId
            '123',
            # CP_CanPhysReqExtAddr
            '0',

            # CP_CanRespUSDTFormat
            'normal segmented 11-bit receive with FC',
            # CP_CanRespUSDTId
            '456',
            # CP_CanRespUSDTExtAddr
            '0',

            # CP_CanRespUUDTFormat
            'normal unsegmented 11-bit receive',
            # CP_CanRespUUDTId
            '4294967295', # -> -1. this seems to be mandated by the standard. what a hack!
            # CP_CanRespUUDTExtAddr
            '0',

            # CP_ECULayerShortName
            'Somersault'
        ]),

    # timeout for responses [us]
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_RC21CompletionTimeout", cp_iso15765_3_doc_frags),
        value="1000000"),

    ###
    # "tester present" message handling
    ###

    # expected "tester present" message
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentMessage", cp_iso15765_3_doc_frags),
        value=f'{tester_present_value}'),

    # a response is mandatory
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value='Response expected'),

    # positive response to "tester present"
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpPosResp", cp_iso15765_3_doc_frags),
        value=f'{tester_pr_value}'),

    # negative response to "tester present"
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpNegResp", cp_iso15765_3_doc_frags),
        value=f'{tester_nr_value}'),

    # when a tester present message must be send
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentSendType", cp_iso15765_3_doc_frags),
        value='On idle'),

    # "tester present" messages are send directly to the CAN IDs
    # (i.e., they are not embedded in the ISO-TP telegram?)
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentAddrMode", cp_iso15765_3_doc_frags),
        value='Physical'),

    # is a response from the ECU to "tester present" messages expected
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value='Response expected'),

    ###
    # ISO-TP parameters:
    ###

    # maximum number of frames between flow control ACKs
    CommunicationParameterRef(
        id_ref=OdxLinkRef("ISO_15765_2.CP_BlockSize", cp_iso15765_2_doc_frags),
        value='4'
    ),
]

somersault_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=NamedItemList(short_name_as_id, somersault_dops.values()),
    unit_spec=UnitSpec(
        unit_groups=list(somersault_unit_groups.values()),
        units=list(somersault_units.values()),
        physical_dimensions=list(somersault_physical_dimensions.values()),
    ),
    tables=NamedItemList(short_name_as_id, somersault_tables.values()),
    muxs=NamedItemList(short_name_as_id, somersault_muxs.values()),
    env_datas=NamedItemList(short_name_as_id, somersault_env_datas.values()),
    env_data_descs=NamedItemList(short_name_as_id, somersault_env_data_descs.values()),
)

# diagnostics layer
somersault_diaglayer = DiagLayer(
    variant_type=DIAG_LAYER_TYPE.BASE_VARIANT,
    odx_id=OdxLinkId("somersault", doc_frags),
    short_name="somersault",
    long_name="Somersault base variant",
    description="<p>Base variant of the somersault ECU &amp; cetera</p>",
    requests=list(somersault_requests.values()),
    services=list(somersault_services.values()),
    single_ecu_jobs=list(somersault_single_ecu_jobs.values()),
    positive_responses=list(somersault_positive_responses.values()),
    negative_responses=list(somersault_negative_responses.values()),
    diag_data_dictionary_spec=somersault_diag_data_dictionary_spec,
    communication_parameters=somersault_communication_parameters,
    additional_audiences=list(somersault_additional_audiences.values()),
    functional_classes=list(somersault_functional_classes.values()))

##################
# Lazy variant of Somersault ECU: this one is lazy and cuts corners
##################

# TODO: inheritance (without too much code duplication)
somersault_lazy_diaglayer = DiagLayer(
    variant_type=DIAG_LAYER_TYPE.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_lazy", doc_frags),
    short_name="somersault_lazy",
    long_name="Somersault lazy ECU",
    description="<p>Sloppy variant of the somersault ECU (lazy &lt; assiduous)</p>",
    parent_refs=[
        DiagLayer.ParentRef( # <- TODO: this is a bit sketchy IMO
            parent=OdxLinkRef.from_id(somersault_diaglayer.odx_id),
            ref_type="BASE-VARIANT-REF",
            # this variant does not do backflips
            not_inherited_diag_comms=[
                somersault_requests["backward_flips"].short_name,
                somersault_requests["set_operation_params"].short_name
            ],
        )],
    communication_parameters=somersault_communication_parameters,
    )

##################
# Assiduous production variant of Somersault ECU: This one works
# harder than it needs to
##################

# TODO: inheritance (without too much code duplication)
somersault_assiduous_diaglayer = DiagLayer(
    variant_type=DIAG_LAYER_TYPE.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_assiduous", doc_frags),
    short_name="somersault_assiduous",
    long_name="Somersault assiduous ECU",
    description="<p>Hard-working variant of the somersault ECU (lazy &lt; assiduous)</p>",
    diag_data_dictionary_spec=DiagDataDictionarySpec(),
    parent_refs=[
        DiagLayer.ParentRef( # <- TODO: this is a bit sketchy IMO
            parent=OdxLinkRef.from_id(somersault_diaglayer.odx_id),
            ref_type="BASE-VARIANT-REF",
            # this variant does everything which the base variant does
        )],
    communication_parameters=somersault_communication_parameters,
    )

# the assiduous ECU also does headstands...
somersault_assiduous_requests = {
    "headstand":
    Request(
        odx_id=OdxLinkId("somersault_assiduous.RQ.do_headstand", doc_frags),
        short_name="do_headstand",
        long_name="Do a headstand & whatever else is required to entertain the customer",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=0x3
            ),
            ValueParameter(
                short_name="duration",
                byte_position=1,
                dop_ref=OdxLinkRef("somersault.DOP.duration", doc_frags)),
        ]
    ),
}

# positive responses
somersault_assiduous_positive_responses = {
    "headstand_done":
    Response(odx_id=OdxLinkId("somersault_assiduous.PR.headstand_done", doc_frags),
             short_name="headstand_done",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=0x1,
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="duration",
                                          request_byte_position=1,
                                          byte_position=1,
                                          byte_length=1),
             ]),
}

# negative responses
somersault_assiduous_negative_responses = {
    "fell_over":
    Response(odx_id=OdxLinkId("somersault_assiduous.NR.fell_over", doc_frags),
             short_name="fell_over",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=0x20,
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="duration",
                                          request_byte_position=1, #somersault_assiduous_requests["headstand"]["duration"].byte_position
                                          byte_position=1,
                                          byte_length=1),
             ]),
}


# services
somersault_assiduous_services = {
    "headstand":
    DiagService(odx_id=OdxLinkId("somersault_assiduous.service.headstand", doc_frags),
                short_name="headstand",
                request=OdxLinkRef.from_id(somersault_assiduous_requests["headstand"].odx_id),
                positive_responses=[
                    OdxLinkRef.from_id(somersault_assiduous_positive_responses["headstand_done"].odx_id),
                ],
                negative_responses=[
                    OdxLinkRef.from_id(somersault_assiduous_negative_responses["fell_over"].odx_id),
                ],
                audience=Audience(enabled_audience_refs=[OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)])
                ),
}

# fill the diagnostics layer object
somersault_assiduous_diaglayer.requests = list(somersault_assiduous_requests.values())
somersault_assiduous_diaglayer._local_services = NamedItemList(short_name_as_id, somersault_assiduous_services.values())
somersault_assiduous_diaglayer.positive_responses = NamedItemList(short_name_as_id, somersault_assiduous_positive_responses.values())
somersault_assiduous_diaglayer.negative_responses = NamedItemList(short_name_as_id, somersault_assiduous_negative_responses.values())

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
    company_datas=NamedItemList(short_name_as_id,
                                [
                                    somersault_company_datas["suncus"],
                                    somersault_company_datas["acme"],
                                ]),
    base_variants=[somersault_diaglayer],
    ecu_variants=[somersault_lazy_diaglayer, somersault_assiduous_diaglayer]
)

# read the communication parameters
comparam_subsets = []
odx_cs_dir = pathlib.Path(__file__).parent / "data"
for odx_cs_filename in ("ISO_11898_2_DWCAN.odx-cs",
                        "ISO_11898_3_DWFTCAN.odx-cs",
                        "ISO_15765_2.odx-cs",
                        "ISO_15765_3_CPSS.odx-cs"):
    odx_cs_root = ElementTree.parse(odx_cs_dir/odx_cs_filename).getroot()
    subset = odx_cs_root.find("COMPARAM-SUBSET")
    if subset is not None:
        comparam_subsets.append(ComparamSubset.from_et(subset))

# create a database object
database = Database()
database._diag_layer_containers = NamedItemList(short_name_as_id, [somersault_dlc])
database._comparam_subsets = NamedItemList(short_name_as_id, comparam_subsets)

# Create ID mapping and resolve references
database.finalize_init()

# delete all variables except "database"
for name in dir():
    if name not in (
            'database',
            'SID',
    ):
        del globals()[name]
del globals()["name"]
