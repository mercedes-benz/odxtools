#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from enum import IntEnum
from itertools import chain

from odxtools import PhysicalConstantParameter

from odxtools.envdata import EnvData
from odxtools.mux import Mux, SwitchKey, DefaultCase, Case

from odxtools.table import Table, TableRow

from odxtools.nameditemlist import NamedItemList

from odxtools.database import Database

from odxtools.companydata import XDoc, RelatedDoc, CompanySpecificInfo, TeamMember, CompanyData
from odxtools.admindata import CompanyDocInfo, Modification, DocRevision, AdminData

from odxtools.diaglayer import DiagLayer
from odxtools.diaglayer import DiagLayerContainer

from odxtools.service import DiagService
from odxtools.singleecujob import SingleEcuJob, ProgCode

from odxtools.structures import Request
from odxtools.structures import Response

from odxtools.compumethods import CompuScale, IdenticalCompuMethod, Limit
from odxtools.compumethods import TexttableCompuMethod

from odxtools.dataobjectproperty import DataObjectProperty

from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec

from odxtools.diagcodedtypes import StandardLengthType
from odxtools.physicaltype import PhysicalType

from odxtools.units import UnitSpec
from odxtools.units import PhysicalDimension
from odxtools.units import Unit
from odxtools.units import UnitGroup

from odxtools.parameters import CodedConstParameter
from odxtools.parameters import ValueParameter
from odxtools.parameters import MatchingRequestParameter
from odxtools.parameters import NrcConstParameter

from odxtools.communicationparameter import CommunicationParameterRef

from odxtools.audience import AdditionalAudience, Audience
from odxtools.functionalclass import FunctionalClass

import odxtools.uds as uds


class SID(IntEnum):
    """The Somersault-ECU specific service IDs.

    These are ECU specific service IDs allocated by the UDS standard.

    """
    ForwardFlip = 0xBA
    BackwardFlip = 0xBB
    Headstand = 0xBC
    ForwardFlipCondition = 0xBD

# extend the Somersault SIDs by the UDS ones
SID = IntEnum('SID', [(i.name, i.value) for i in chain(uds.SID, SID)])


###########
# /generic UDS stuff
###########

##################
# Base variant of Somersault ECU
##################

# company datas
somersault_team_members = {
    "doggy":
    TeamMember(id="TM.Doggy",
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
    TeamMember(id="TM.Horsey",
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
    TeamMember(id="TM.Slothy",
               short_name="Slothy")
}

somersault_company_datas = {
    "suncus":
    CompanyData(id="CD.Suncus",
                short_name="Suncus",
                long_name="Circus of the sun",
                description="<p>Prestigious group of performers</p>",
                roles=["circus", "gym"],
                team_members=NamedItemList(lambda x: x.short_name,
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
    CompanyData(id="CD.ACME",
                short_name="ACME_Corporation",
                team_members=NamedItemList(lambda x: x.short_name,
                                           [
                                               somersault_team_members["slothy"],
                                           ]),
                ),

}

somersault_admin_data = \
    AdminData(language="en-US",
              company_doc_infos=\
              [
                  CompanyDocInfo(company_data_ref="CD.Suncus",
                                 team_member_ref="TM.Doggy",
                                 doc_label="A really meaningful label"),
              ],
              doc_revisions=\
              [
                  DocRevision(team_member_ref="TM.Doggy",
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
                  DocRevision(team_member_ref="TM.Horsey",
                              revision_label="1.1",
                              state="released",
                              date="2020-08-19T12:12:12+08:00",
                              tool="odxtools 0.1",
                              modifications=[
                                  Modification(change="rename somersault ECU to somersault_assiduous to enable slothy to add somersault_lazy"),
                              ]),

                  DocRevision(team_member_ref="TM.Slothy",
                              revision_label="1.0.3.2.1.5.6",
                              date="1900-01-01T00:00:00+00:00"),
              ])

# functional classes
somersault_functional_classes = {
    "flip":
    FunctionalClass(
        id="somersault.FNC.flip",
        short_name="flip",
        long_name="Flip"),

    "session":
    FunctionalClass(
        id="somersault.FNC.session",
        short_name="session",
        long_name="Session"),
}

# additional audiences
somersault_additional_audiences = {
    "attentive_admirer":
    AdditionalAudience(
        id="somersault.AA.attentive_admirer",
        short_name="attentive_admirer",
        long_name="Attentive Admirer"),

    "anyone":
    AdditionalAudience(
        id="somersault.AA.anyone",
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
        id="somersault.PD.second",
        short_name="second",
        long_name="Second",
        time_exp=1
    )
}

somersault_units = {
    "second":
        Unit(
            id="somersault.unit.second",
            short_name="second",
            display_name="s",
            long_name="Second",
            description="<p>SI unit for the time</p>",
            factor_si_to_unit=1,
            offset_si_to_unit=0,
            physical_dimension_ref=somersault_physical_dimensions["second"].id
        ),
    "minute":
        Unit(
            id="somersault.unit.minute",
            short_name="minute",
            display_name="min",
            long_name="Minute",
            factor_si_to_unit=60,
            offset_si_to_unit=0,
            physical_dimension_ref=somersault_physical_dimensions["second"].id
        ),
}

somersault_unit_groups = {
    "european_duration":
        UnitGroup(
            short_name="european_duration",
            category="COUNTRY",
            unit_refs=[somersault_units["second"].id, somersault_units["minute"].id],
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
        id="somersault.DOP.num_flips",
        short_name="num_flips",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "soberness_check":
    DataObjectProperty(
        id="somersault.DOP.soberness_check",
        short_name="soberness_check",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "dizzyness_level":
    DataObjectProperty(
        id="somersault.DOP.dizzyness_level",
        short_name="dizzyness_level",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "happiness_level":
    DataObjectProperty(
        id="somersault.DOP.happiness_level",
        short_name="happiness_level",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "duration":
    DataObjectProperty(
        id="somersault.DOP.duration",
        short_name="duration",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"],
        unit_ref=somersault_units["second"].id),

    "error_code":
    DataObjectProperty(
        id="somersault.DOP.error_code",
        short_name="error_code",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UINT32"),
        compu_method=somersault_compumethods["uint_passthrough"]),

    "boolean":
    DataObjectProperty(
        id="somersault.DOP.boolean",
        short_name="boolean",
        diag_coded_type=somersault_diagcodedtypes["uint8"],
        physical_type=PhysicalType("A_UNICODE2STRING"),
        compu_method=somersault_compumethods["boolean"]),
}

# tables
somersault_tables = {
    "flip_quality": Table(
        id="somersault.table.flip_quality",
        short_name="flip_quality",
        long_name="Flip Quality",
        key_dop_ref=somersault_dops["num_flips"].id,
        table_rows=[
            TableRow(
                id="somersault.table.flip_quality.average",
                short_name="average",
                long_name="Average",
                key=3,
                structure_ref=somersault_dops["num_flips"].id,
            ),
            TableRow(
                id="somersault.table.flip_quality.good",
                short_name="good",
                long_name="Good",
                key=5,
                structure_ref=somersault_dops["num_flips"].id,
            ),
            TableRow(
                id="somersault.table.flip_quality.best",
                short_name="best",
                long_name="Best",
                key=10,
                structure_ref=somersault_dops["num_flips"].id,
            ),
        ]
    )

}

# muxs
somersault_muxs = {
    "flip_preference": Mux(
        id="somersault.mux.flip_preference",
        short_name="flip_preference",
        long_name="Flip Preference",
        byte_position=0,
        switch_key=SwitchKey(
            byte_position=0,
            bit_position=0,
            dop_ref=somersault_dops["num_flips"].id,
        ),
        default_case=DefaultCase(
            short_name="default_case",
            long_name="Default Case",
            structure_ref=somersault_dops["num_flips"].id,
        ),
        cases=[
            Case(
                short_name="forward_flip",
                long_name="Forward Flip",
                lower_limit="1",
                upper_limit="3",
                structure_ref=somersault_dops["num_flips"].id,
            ),
            Case(
                short_name="backward_flip",
                long_name="Backward Flip",
                lower_limit="1",
                upper_limit="3",
                structure_ref=somersault_dops["num_flips"].id,
            )
        ]
    )
}

# env-data
somersault_env_datas = {
    "flip_env_data": EnvData(
        id="somersault.env_data.flip_env_data",
        short_name="flip_env_data",
        long_name="Flip Env Data",
        parameters=[
            ValueParameter(
                short_name="flip_speed",
                long_name="Flip Speed",
                byte_position=0,
                semantic="DATA",
                dop_ref=somersault_dops["num_flips"].id,
            ),
            PhysicalConstantParameter(
                short_name="flip_direction",
                long_name="Flip Direction",
                byte_position=1,
                semantic="DATA",
                physical_constant_value=1,
                dop_ref=somersault_dops["num_flips"].id,
            ),
        ]
    )
}

# requests
somersault_requests = {
    "start_session":
    Request(
        id="somersault.RQ.start_session",
        short_name="start_session",
        long_name="Start the diagnostic session & do some mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.DiagnosticSessionControl.value,
            ),
            CodedConstParameter(
                short_name="id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x0,
            ),
        ]
    ),

    "stop_session":
    Request(
        id="somersault.RQ.stop_session",
        short_name="stop_session",
        long_name="Terminate the current diagnostic session",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.DiagnosticSessionControl.value,
            ),
            CodedConstParameter(
                short_name="id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x1,
            ),
        ]
    ),

    "tester_present":
    Request(
        id="somersault.RQ.tester_present",
        short_name="tester_present",
        long_name="Prevent the current diagnostic session from timing out",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.TesterPresent.value
            ),
            CodedConstParameter(
                short_name="id",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=1,
                coded_value=0x0
            ),
        ]
    ),

    "set_operation_params":
    Request(
        id="somersault.RQ.set_operation_params",
        short_name="set_operation_params",
        long_name=\
        "Specify the mode of operation for the ECU; e.g. if rings "
        "of fire ought to be used for maximum effect",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ForwardFlipCondition.value,
            ),
            ValueParameter(
                short_name="use_fire_ring",
                byte_position=1,
                dop_ref="somersault.DOP.boolean",
            ),

        ]
    ),

    "forward_flips":
    Request(
        id="somersault.RQ.do_forward_flips",
        short_name="do_forward_flips",
        long_name="Do forward somersaults & some other mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ForwardFlip.value
            ),
            ValueParameter(
                short_name="forward_soberness_check",
                dop_ref="somersault.DOP.soberness_check",
                byte_position=1,
                #value must be 0x12 for the request to be accepted
            ),
            ValueParameter(
                short_name="num_flips",
                byte_position=2,
                dop_ref="somersault.DOP.num_flips"),
        ]
    ),

    "backward_flips":
    Request(
        id="somersault.RQ.do_backward_flips",
        short_name="do_backward_flips",
        long_name="Do a backward somersault & some other mischief",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.BackwardFlip.value
            ),
            ValueParameter(
                short_name="backward_soberness_check",
                dop_ref="somersault.DOP.soberness_check",
                byte_position=1,
                #value must be 0x21 for the request to be accepted
            ),
            ValueParameter(
                short_name="num_flips",
                byte_position=2,
                dop_ref="somersault.DOP.num_flips",
            ),
        ]
    ),

    "report_status":
    Request(
        id="somersault.RQ.report_status",
        short_name="report_status",
        long_name="Report back the current level of dizzy- & happiness.",
        parameters=[
            CodedConstParameter(
                short_name="sid",
                diag_coded_type=somersault_diagcodedtypes["uint8"],
                byte_position=0,
                coded_value=SID.ReadDataByIdentifier.value,
            ),
            CodedConstParameter(
                short_name="id",
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
    Response(id="somersault.PR.session_start",
             short_name="session",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.DiagnosticSessionControl.value),
                 ),
                 ValueParameter(
                     short_name="can_do_backward_flips",
                     byte_position=1,
                     dop_ref="somersault.DOP.boolean",
                 ),
             ]),

    "tester_ok":
    Response(id="somersault.PR.tester_present",
             short_name="tester_present",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint16"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.TesterPresent.value),
                 ),
                 CodedConstParameter(
                     short_name="status",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=1,
                     coded_value=0x00,
                 ),
             ]),

    "forward_flips_grudgingly_done":
    Response(id="somersault.PR.grudging_forward",
             short_name="grudging_forward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlip.value),
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=2,
                                          byte_position=1,
                                          byte_length=1),
             ]),

    "forward_flips_happily_done":
    Response(id="somersault.PR.happy_forward",
             short_name="happy_forward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlip.value),
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=3,
                                          byte_position=1,
                                          byte_length=1),
                 ValueParameter(
                     short_name="yeha_level",
                     byte_position=2,
                     dop_ref="somersault.DOP.num_flips"),
             ]),

    "backward_flips_grudgingly_done":
    Response(id="somersault.PR.grudging_backward",
             short_name="grudging_backward",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.BackwardFlip.value),
                 ),
                 # TODO (?): non-byte aligned MatchingRequestParameters
                 MatchingRequestParameter(short_name="num_flips_done",
                                          request_byte_position=3,
                                          byte_position=1,
                                          byte_length=1),
             ]),

    # Note that there is no such thing as a "backwards flip done happily"!

    "status_report":
    Response(id="somersault.PR.status_report",
             short_name="status_report",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ReadDataByIdentifier.value),
                 ),
                 ValueParameter(
                     short_name="dizzyness_level",
                     byte_position=1,
                     dop_ref="somersault.DOP.dizzyness_level"),
                 ValueParameter(
                     short_name="happiness_level",
                     byte_position=2,
                     dop_ref="somersault.DOP.happiness_level"),
             ]),

    "set_operation_params":
    Response(id="somersault.PR.set_operation_params",
             short_name="set_operation_params",
             response_type="POS-RESPONSE",
             parameters=[
                 CodedConstParameter(
                     short_name="sid",
                     diag_coded_type=somersault_diagcodedtypes["uint8"],
                     byte_position=0,
                     coded_value=uds.positive_response_id(SID.ForwardFlipCondition.value),
                 ),
             ]),
}

# negative responses
somersault_negative_responses = {
    "general":
    Response(id="somersault.NR.general_negative_response",
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
                     dop_ref="somersault.DOP.error_code"),
             ]),

    # the tester present request needs separate negative and positive
    # responses because it must be fully specified a-priory to be able
    # to extract it for the COMPARAMS.
    "tester_nok":
    Response(id="somersault.NR.tester_nok",
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
                     coded_value=uds.SID.TesterPresent.value,
                 ),
             ]),

    "flips_not_done":
    Response(id="somersault.NR.flips_not_done",
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
                     dop_ref="somersault.DOP.num_flips",
                     byte_position=3,
                 ),
             ]),
}

# services
somersault_services = {
    "start_session":
    DiagService(id="somersault.service.session_start",
                short_name="session_start",
                request=somersault_requests["start_session"].id,
                semantic="SESSION",
                positive_responses=[
                    somersault_positive_responses["session"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["general"].id,
                ],
                functional_class_refs=[
                    somersault_functional_classes["session"].id
                ]
                ),

    "stop_session":
    DiagService(id="somersault.service.session_stop",
                short_name="session_stop",
                semantic="SESSION",
                request=somersault_requests["stop_session"].id,
                positive_responses=[
                    somersault_positive_responses["session"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["general"].id,
                ],
                functional_class_refs=[
                    somersault_functional_classes["session"].id
                ]
                ),

    "tester_present":
    DiagService(id="somersault.service.tester_present",
                short_name="tester_present",
                semantic="TESTERPRESENT",
                request=somersault_requests["tester_present"].id,
                positive_responses=[
                    somersault_positive_responses["tester_ok"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["tester_nok"].id,
                ],
                audience=Audience(
                    enabled_audience_refs=[
                        somersault_additional_audiences["attentive_admirer"].id,
                        somersault_additional_audiences["anyone"].id,
                    ],
                    is_development=False)
                ),

    "set_operation_params":
    DiagService(id="somersault.service.set_operation_params",
                short_name="set_operation_params",
                semantic="FUNCTION",
                request=somersault_requests["set_operation_params"].id,
                positive_responses=[
                    somersault_positive_responses["set_operation_params"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["general"].id,
                ],
                ),

    "forward_flips":
    DiagService(id="somersault.service.do_forward_flips",
                short_name="do_forward_flips",
                description="<p>Do a forward flip.</p>",
                semantic="FUNCTION",
                request=somersault_requests["forward_flips"].id,
                positive_responses=[
                    somersault_positive_responses["forward_flips_grudgingly_done"].id,
                    # TODO: implement handling of multiple responses
                    #somersault_positive_responses["forward_flips_happily_done"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["flips_not_done"].id,
                    # TODO (?): implement handling of multiple possible responses
                    #somersault_negative_responses["stumbled"].id,
                    #somersault_negative_responses["too_dizzy"].id,
                    #somersault_negative_responses["not_sober"].id,
                ],
                functional_class_refs=[
                    somersault_functional_classes["flip"].id
                ],
                audience=Audience(
                    enabled_audience_refs=[somersault_additional_audiences["attentive_admirer"].id],
                    is_development=False)
                ),

    "backward_flips":
    DiagService(id="somersault.service.do_backward_flips",
                short_name="do_backward_flips",
                semantic="FUNCTION",
                request=somersault_requests["backward_flips"].id,
                positive_responses=[
                    somersault_positive_responses["backward_flips_grudgingly_done"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["flips_not_done"].id,
                ],
                functional_class_refs=[
                    somersault_functional_classes["flip"].id
                ],
                audience=Audience(
                    enabled_audience_refs=[somersault_additional_audiences["attentive_admirer"].id],
                    is_development=False)
                ),

    "report_status":
    DiagService(id="somersault.service.report_status",
                short_name="report_status",
                semantic="CURRENTDATA",
                request=somersault_requests["report_status"].id,
                positive_responses=[
                    somersault_positive_responses["status_report"].id,
                ],
                negative_responses=[
                    somersault_negative_responses["general"].id,
                ],
                audience=Audience(
                    disabled_audience_refs=[somersault_additional_audiences["attentive_admirer"].id],
                    is_aftersales=False,
                    is_aftermarket=False)
                ),

}

somersault_single_ecu_jobs = {
    "compulsory_program":
    SingleEcuJob(id="somersault.service.compulsory_program",
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
    return bytes(map(lambda x: x.coded_value,
                     filter(lambda y: isinstance(y, CodedConstParameter),
                            params))).hex()
tester_present_value = extract_constant_bytes(somersault_requests["tester_present"].parameters)
tester_pr_value = extract_constant_bytes(somersault_positive_responses["tester_ok"].parameters)
tester_nr_value = extract_constant_bytes(somersault_negative_responses["tester_nok"].parameters)
somersault_communication_parameters = [
    ###
    # basic parameters
    ###

    # bus speed
    CommunicationParameterRef(
        id_ref="ISO_11898_2_DWCAN.CP_Baudrate",
        value="500000"),

    # parameters of the CAN diagnostics frames
    CommunicationParameterRef(
        id_ref='ISO_15765_2.CP_UniqueRespIdTable',
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
        id_ref="ISO_15765_3.CP_RC21CompletionTimeout",
        value="1000000"),

    ###
    # "tester present" message handling
    ###

    # expected "tester present" message
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentMessage',
        value=f'{tester_present_value}'),

    # a response is mandatory
    CommunicationParameterRef(
        id_ref='ISO_15765_3.ISO_15765_3.CP_TesterPresentReqRsp',
        value='Response expected'),

    # positive response to "tester present"
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentExpPosResp',
        value=f'{tester_pr_value}'),

    # negative response to "tester present"
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentExpNegResp',
        value=f'{tester_nr_value}'),

    # when a tester present message must be send
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentSendType',
        value='On idle'),

    # "tester present" messages are send directly to the CAN IDs
    # (i.e., they are not embedded in the ISO-TP telegram?)
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentAddrMode',
        value='Physical'),

    # is a response from the ECU to "tester present" messages expected
    CommunicationParameterRef(
        id_ref='ISO_15765_3.CP_TesterPresentReqRsp',
        value='Response expected'),

    ###
    # ISO-TP parameters:
    ###

    # maximum number of frames between flow control ACKs
    CommunicationParameterRef(
        id_ref='ISO_15765_2.CP_BlockSize',
        value='4'
    ),
]

somersault_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=list(somersault_dops.values()),
    unit_spec=UnitSpec(
        unit_groups=list(somersault_unit_groups.values()),
        units=list(somersault_units.values()),
        physical_dimensions=list(somersault_physical_dimensions.values()),
    ),
    tables=list(somersault_tables.values()),
    muxs=list(somersault_muxs.values()),
    env_datas=list(somersault_env_datas.values()),
)

# diagnostics layer
somersault_diaglayer = DiagLayer(
    variant_type="BASE-VARIANT",
    id="somersault",
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
    variant_type="ECU-VARIANT",
    id="somersault_lazy",
    short_name="somersault_lazy",
    long_name="Somersault lazy ECU",
    description="<p>Sloppy variant of the somersault ECU (lazy &lt; assiduous)</p>",
    parent_refs=[
        DiagLayer.ParentRef( # <- TODO: this is a bit sketchy IMO
            reference=somersault_diaglayer.id,
            ref_type="BASE-VARIANT-REF",
            # this variant does not do backflips
            not_inherited_diag_comms=[
                somersault_requests["backward_flips"].short_name,
                somersault_requests["set_operation_params"].short_name
            ],
        )],
    communication_parameters=somersault_communication_parameters,
    enable_candela_workarounds=False,
    )

##################
# Assiduous production variant of Somersault ECU: This one works
# harder than it needs to
##################

# TODO: inheritance (without too much code duplication)
somersault_assiduous_diaglayer = DiagLayer(
    variant_type="ECU-VARIANT",
    id="somersault_assiduous",
    short_name="somersault_assiduous",
    long_name="Somersault assiduous ECU",
    description="<p>Hard-working variant of the somersault ECU (lazy &lt; assiduous)</p>",
    diag_data_dictionary_spec=DiagDataDictionarySpec(),
    parent_refs=[
        DiagLayer.ParentRef( # <- TODO: this is a bit sketchy IMO
            reference=somersault_diaglayer.id,
            ref_type="BASE-VARIANT-REF",
            # this variant does everything which the base variant does
        )],
    communication_parameters=somersault_communication_parameters,
    enable_candela_workarounds=False,
    )

# the assiduous ECU also does headstands...
somersault_assiduous_requests = {
    "headstand":
    Request(
        id="somersault_assiduous.RQ.do_headstand",
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
                dop_ref="somersault.DOP.duration"),
        ]
    ),
}

# positive responses
somersault_assiduous_positive_responses = {
    "headstand_done":
    Response(id="somersault_assiduous.PR.headstand_done",
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
    Response(id="somersault_assiduous.NR.fell_over",
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
    DiagService(id="somersault_assiduous.service.headstand",
                short_name="headstand",
                request=somersault_assiduous_requests["headstand"].id,
                positive_responses=[
                    somersault_assiduous_positive_responses["headstand_done"].id,
                ],
                negative_responses=[
                    somersault_assiduous_negative_responses["fell_over"].id,
                ],
                audience=Audience(enabled_audience_refs=[somersault_additional_audiences["attentive_admirer"].id])
                ),
}

# fill the diagnostics layer object
somersault_assiduous_diaglayer.requests = list(somersault_assiduous_requests.values())
somersault_assiduous_diaglayer._local_services = list(somersault_assiduous_services.values())
somersault_assiduous_diaglayer.positive_responses = list(somersault_assiduous_positive_responses.values())
somersault_assiduous_diaglayer.negative_responses = list(somersault_assiduous_negative_responses.values())

##################
# Container with all ECUs
##################

# create a "diagnosis layer container" object
somersault_dlc = DiagLayerContainer(
    id="DLC.somersault",
    short_name="somersault",
    long_name="Collect all saults in the summer",
    description="<p>This contains ECUs which do somersaults &amp; cetera</p>",
    admin_data=somersault_admin_data,
    company_datas=NamedItemList(lambda x: x.short_name,
                                [
                                    somersault_company_datas["suncus"],
                                    somersault_company_datas["acme"],
                                ]),
    base_variants=[somersault_diaglayer],
    ecu_variants=[somersault_lazy_diaglayer, somersault_assiduous_diaglayer]
)

# create a database object
database = Database()
database.diag_layer_containers = NamedItemList(lambda x: x.short_name,
                                               [somersault_dlc])

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
