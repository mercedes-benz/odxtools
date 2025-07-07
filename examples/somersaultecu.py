#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import pathlib
from enum import IntEnum
from io import BytesIO
from itertools import chain
from typing import Any
from xml.etree import ElementTree

from packaging.version import Version

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
from odxtools.compumethods.compucategory import CompuCategory
from odxtools.compumethods.compuconst import CompuConst
from odxtools.compumethods.compuinternaltophys import CompuInternalToPhys
from odxtools.compumethods.compumethod import CompuMethod
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
from odxtools.odxdoccontext import OdxDocContext
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkId, OdxLinkRef
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
from odxtools.preconditionstateref import PreConditionStateRef
from odxtools.progcode import ProgCode
from odxtools.relateddoc import RelatedDoc
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.singleecujob import SingleEcuJob
from odxtools.standardlengthtype import StandardLengthType
from odxtools.state import State
from odxtools.statechart import StateChart
from odxtools.statetransition import StateTransition
from odxtools.statetransitionref import StateTransitionRef
from odxtools.structure import Structure
from odxtools.table import Table
from odxtools.tablerow import TableRow
from odxtools.teammember import TeamMember
from odxtools.unit import Unit
from odxtools.unitgroup import UnitGroup
from odxtools.unitgroupcategory import UnitGroupCategory
from odxtools.unitspec import UnitSpec
from odxtools.xdoc import XDoc

ODX_VERSION = Version("2.2.0")


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
doc_frags = (OdxDocFragment(dlc_short_name, DocType.CONTAINER),)

# document fragments for communication parameters
cp_dwcan_doc_frags = (OdxDocFragment("ISO_11898_2_DWCAN", DocType.COMPARAM_SUBSET),)
cp_iso15765_2_doc_frags = (OdxDocFragment("ISO_15765_2", DocType.COMPARAM_SUBSET),)
cp_iso15765_3_doc_frags = (OdxDocFragment("ISO_15765_3", DocType.COMPARAM_SUBSET),)

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
            description=Description.from_string("<p>Dog is man's best friend</p>"),
            roles=["gymnast", "tracker"],
            department="sniffers",
            address="Some road",
            zipcode="12345",
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
            description=Description.from_string("<p>Trustworthy worker</p>"),
            roles=["gymnast"],
            department="haulers",
            address="Some road",
            zipcode="12345",
            city="New Dogsville",
            phone="+0 1234/5678-91",
            fax="+0 1234/5678-0",
            email="info@suncus.com",
        ),
    "slothy":
        TeamMember(
            odx_id=OdxLinkId("TM.Slothy", doc_frags),
            short_name="Slothy",
        ),
}

somersault_company_datas = {
    "suncus":
        CompanyData(
            odx_id=OdxLinkId("CD.Suncus", doc_frags),
            short_name="Suncus",
            long_name="Circus of the sun",
            description=Description.from_string("<p>Prestigious group of performers</p>"),
            roles=["circus", "gym"],
            team_members=NamedItemList([
                somersault_team_members["doggy"],
                somersault_team_members["horsey"],
            ]),
            company_specific_info=CompanySpecificInfo(related_docs=[
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
            ]),
        ),
    "acme":
        CompanyData(
            odx_id=OdxLinkId("CD.ACME", doc_frags),
            short_name="ACME_Corporation",
            team_members=NamedItemList([
                somersault_team_members["slothy"],
            ]),
        ),
}

somersault_admin_data = AdminData(
    language="en-US",
    company_doc_infos=[
        CompanyDocInfo(
            company_data_ref=OdxLinkRef("CD.Suncus", doc_frags),
            team_member_ref=OdxLinkRef("TM.Doggy", doc_frags),
            doc_label="A really meaningful label",
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
                ),
            ],
        ),
        DocRevision(
            team_member_ref=OdxLinkRef("TM.Slothy", doc_frags),
            revision_label="1.0.3.2.1.5.6",
            date="1900-01-01T00:00:00+00:00",
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
        ),
    "session":
        FunctionalClass(
            odx_id=OdxLinkId("somersault.FNC.session", doc_frags),
            short_name="session",
            long_name="Session",
        ),
}

# additional audiences
somersault_additional_audiences = {
    "attentive_admirer":
        AdditionalAudience(
            odx_id=OdxLinkId("somersault.AA.attentive_admirer", doc_frags),
            short_name="attentive_admirer",
            long_name="Attentive Admirer",
        ),
    "anyone":
        AdditionalAudience(
            odx_id=OdxLinkId("somersault.AA.anyone", doc_frags),
            short_name="anyone",
            long_name="Anyone",
        ),
}

# diag coded types
somersault_diagcodedtypes = {
    "flag": StandardLengthType(
        base_data_type=DataType.A_UINT32,
        bit_length=1,
    ),
    "int8": StandardLengthType(
        base_data_type=DataType.A_INT32,
        bit_length=8,
    ),
    "uint8": StandardLengthType(
        base_data_type=DataType.A_UINT32,
        bit_length=8,
    ),
    "uint16": StandardLengthType(
        base_data_type=DataType.A_UINT32,
        bit_length=16,
    ),
    "float32": StandardLengthType(
        base_data_type=DataType.A_FLOAT32,
        bit_length=32,
    ),
}

somersault_physical_dimensions = {
    "time":
        PhysicalDimension(
            odx_id=OdxLinkId("somersault.PD.time", doc_frags),
            short_name="time",
            long_name="Time",
            time_exp=1,
        ),
    "temperature":
        PhysicalDimension(
            odx_id=OdxLinkId("somersault.PD.temperature", doc_frags),
            short_name="temperature",
            long_name="Temperature",
            temperature_exp=1,
        )
}

somersault_units = {
    "second":
        Unit(
            odx_id=OdxLinkId("somersault.unit.second", doc_frags),
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
            short_name="minute",
            display_name="min",
            long_name="Minute",
            factor_si_to_unit=60,
            offset_si_to_unit=0,
            physical_dimension_ref=OdxLinkRef.from_id(
                somersault_physical_dimensions["time"].odx_id),
        ),
    "celsius":
        Unit(
            odx_id=OdxLinkId("somersault.unit.celsius", doc_frags),
            short_name="celsius",
            display_name="°C",
            long_name="Degrees Celcius",
            factor_si_to_unit=1,
            offset_si_to_unit=-273.15,
            physical_dimension_ref=OdxLinkRef.from_id(
                somersault_physical_dimensions["temperature"].odx_id),
        ),
}

somersault_unit_groups = {
    "european_duration":
        UnitGroup(
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
somersault_compumethods: dict[str, CompuMethod] = {
    "int_passthrough":
        IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            internal_type=DataType.A_INT32,
            physical_type=DataType.A_INT32),
    "uint_passthrough":
        IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UINT32),
    "float_passthrough":
        IdenticalCompuMethod(
            category=CompuCategory.IDENTICAL,
            internal_type=DataType.A_FLOAT32,
            physical_type=DataType.A_FLOAT32),
    "boolean":
        TexttableCompuMethod(
            category=CompuCategory.TEXTTABLE,
            compu_internal_to_phys=CompuInternalToPhys(compu_scales=[
                CompuScale(
                    compu_const=CompuConst(vt="false", data_type=DataType.A_UTF8STRING),
                    lower_limit=Limit(value_raw="0", value_type=DataType.A_UINT32),
                    upper_limit=Limit(value_raw="0", value_type=DataType.A_UINT32),
                    domain_type=DataType.A_UINT32,
                    range_type=DataType.A_UNICODE2STRING),
                CompuScale(
                    compu_const=CompuConst(vt="true", data_type=DataType.A_UTF8STRING),
                    lower_limit=Limit(value_raw="1", value_type=DataType.A_UINT32),
                    upper_limit=Limit(value_raw="1", value_type=DataType.A_UINT32),
                    domain_type=DataType.A_UINT32,
                    range_type=DataType.A_UNICODE2STRING),
            ]),
            internal_type=DataType.A_UINT32,
            physical_type=DataType.A_UNICODE2STRING,
        ),
}

# data object properties
somersault_dops = {
    "num_flips":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.num_flips", doc_frags),
            short_name="num_flips",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "soberness_check":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.soberness_check", doc_frags),
            short_name="soberness_check",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "dizzyness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.dizzyness_level", doc_frags),
            short_name="dizzyness_level",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "happiness_level":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.happiness_level", doc_frags),
            short_name="happiness_level",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "duration":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.duration", doc_frags),
            short_name="duration",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["second"].odx_id),
        ),
    "temperature":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.temperature", doc_frags),
            short_name="temperature",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
            unit_ref=OdxLinkRef.from_id(somersault_units["celsius"].odx_id),
        ),
    "error_code":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.error_code", doc_frags),
            short_name="error_code",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "boolean":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.boolean", doc_frags),
            short_name="boolean",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UNICODE2STRING),
            compu_method=somersault_compumethods["boolean"],
        ),
    "uint8":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.uint8", doc_frags),
            short_name="uint8",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "uint16":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.uint16", doc_frags),
            short_name="uint16",
            diag_coded_type=somersault_diagcodedtypes["uint16"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "float":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.float", doc_frags),
            short_name="float",
            diag_coded_type=somersault_diagcodedtypes["float32"],
            physical_type=PhysicalType(base_data_type=DataType.A_FLOAT32),
            compu_method=somersault_compumethods["float_passthrough"],
        ),
    "schroedinger_base":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.schroedinger_base", doc_frags),
            short_name="schroedinger_dop",
            diag_coded_type=somersault_diagcodedtypes["int8"],
            physical_type=PhysicalType(base_data_type=DataType.A_INT32),
            compu_method=somersault_compumethods["int_passthrough"],
        ),
    "schroedinger_lazy":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.schroedinger_lazy", doc_frags),
            short_name="schroedinger_dop",
            diag_coded_type=somersault_diagcodedtypes["uint8"],
            physical_type=PhysicalType(base_data_type=DataType.A_UINT32),
            compu_method=somersault_compumethods["uint_passthrough"],
        ),
    "schroedinger_assiduous":
        DataObjectProperty(
            odx_id=OdxLinkId("somersault.DOP.schroedinger_assiduous", doc_frags),
            short_name="schroedinger_dop",
            diag_coded_type=somersault_diagcodedtypes["float32"],
            physical_type=PhysicalType(base_data_type=DataType.A_FLOAT32),
            compu_method=somersault_compumethods["float_passthrough"],
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
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(
                        uds.positive_response_id(
                            SID.DiagnosticSessionControl.value)),  # type: ignore[attr-defined]
                ),
                ValueParameter(
                    short_name="can_do_backward_flips",
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                ),
            ]),
        ),
    "tester_ok":
        Response(
            odx_id=OdxLinkId("somersault.PR.tester_present", doc_frags),
            short_name="tester_present",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.TesterPresent.value)),  # type: ignore[attr-defined]
                ),
                ValueParameter(
                    short_name="status",
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                    physical_default_value_raw="0",
                    byte_position=1,
                ),
            ]),
        ),
    "forward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_forward", doc_frags),
            short_name="grudging_forward",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.ForwardFlip.value)),  # type: ignore[attr-defined]
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    short_name="num_flips_done",
                    request_byte_position=2,
                    byte_position=1,
                    byte_length=1,
                ),
                ValueParameter(
                    short_name="sault_time",
                    physical_default_value_raw="255",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.duration", doc_frags),
                ),
            ]),
        ),
    "forward_flips_happily_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.happy_forward", doc_frags),
            short_name="happy_forward",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.ForwardFlip.value)),  # type: ignore[attr-defined]
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    short_name="num_flips_done",
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                ),
                ValueParameter(
                    short_name="yeha_level",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                ),
            ]),
        ),
    "backward_flips_grudgingly_done":
        Response(
            odx_id=OdxLinkId("somersault.PR.grudging_backward", doc_frags),
            short_name="grudging_backward",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.BackwardFlip.value)),  # type: ignore[attr-defined]
                ),
                ValueParameter(
                    short_name="num_flips_done",
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                ),
                ValueParameter(
                    short_name="grumpiness_level",
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                ),
            ]),
        ),
    # Note that there is no such thing as a "backwards flip done happily"!
    "status_report":
        Response(
            odx_id=OdxLinkId("somersault.PR.status_report", doc_frags),
            short_name="status_report",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.ReadDataByIdentifier.value)),  # type: ignore[attr-defined]
                ),
                ValueParameter(
                    short_name="dizzyness_level",
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.dizzyness_level", doc_frags),
                ),
                ValueParameter(
                    short_name="happiness_level",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.happiness_level", doc_frags),
                ),
                TableKeyParameter(
                    odx_id=OdxLinkId("somersault.PR.report_status.last_pos_response_key",
                                     doc_frags),
                    short_name="last_pos_response_key",
                    table_ref=last_flip_details_table_ref,
                    byte_position=3,
                ),
                TableStructParameter(
                    short_name="last_pos_response",
                    table_key_ref=OdxLinkRef("somersault.PR.report_status.last_pos_response_key",
                                             doc_frags),
                ),
            ]),
        ),
    "set_operation_params":
        Response(
            odx_id=OdxLinkId("somersault.PR.set_operation_params", doc_frags),
            short_name="set_operation_params",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.positive_response_id(
                        SID.ForwardFlipCondition.value)),  # type: ignore[attr-defined]
                ),
            ]),
        ),
}

somersault_structures = {
    "forward_flips_grudgingly_done":
        Structure(
            short_name="forward_flips_grudgingly_done_recall",
            odx_id=OdxLinkId("somersault.struct.recall.forward_flips_grudgingly_done", doc_frags),
            parameters=somersault_positive_responses["forward_flips_grudgingly_done"].parameters),
    "forward_flips_happily_done":
        Structure(
            short_name="forward_flips_happily_done_recall",
            odx_id=OdxLinkId("somersault.struct.recall.forward_flips_happily_done", doc_frags),
            parameters=somersault_positive_responses["forward_flips_happily_done"].parameters),
    "backward_flips_grudgingly_done":
        Structure(
            short_name="backward_flips_grudgingly_done_recall",
            odx_id=OdxLinkId("somersault.struct.recall.backward_flips_grudgingly_done", doc_frags),
            parameters=somersault_positive_responses["backward_flips_grudgingly_done"].parameters),
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
            short_name="general_negative_response",
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.NegativeResponseId),
                ),
                MatchingRequestParameter(
                    short_name="rq_sid",
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                ),
                ValueParameter(
                    short_name="response_code",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.error_code", doc_frags),
                ),
            ]),
        ),
    # the tester present request needs separate negative and positive
    # responses because it must be fully specified a-priory to be able
    # to extract it for the COMPARAMS.
    "tester_nok":
        Response(
            odx_id=OdxLinkId("somersault.NR.tester_nok", doc_frags),
            short_name="tester_nok",
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.NegativeResponseId),
                ),
                CodedConstParameter(
                    short_name="rq_sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(uds.SID.TesterPresent.value),  # type: ignore[attr-defined]
                ),
            ]),
        ),
    "flips_not_done":
        Response(
            odx_id=OdxLinkId("somersault.NR.flips_not_done", doc_frags),
            short_name="flips_not_done",
            response_type=ResponseType.NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.NegativeResponseId),
                ),
                MatchingRequestParameter(
                    short_name="rq_sid",
                    request_byte_position=0,
                    byte_position=1,
                    byte_length=1,
                ),
                NrcConstParameter(
                    short_name="reason",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=2,
                    coded_values_raw=[str(0), str(1), str(2)],
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
        ),
}

somersault_global_negative_responses = {
    "general":
        Response(
            odx_id=OdxLinkId("GNR.too_hot", doc_frags),
            short_name="too_hot",
            response_type=ResponseType.GLOBAL_NEGATIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(uds.NegativeResponseId),
                ),
                CodedConstParameter(
                    short_name="too_hot_dummy",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(0xfe),
                ),
                CodedConstParameter(
                    short_name="too_hot_id",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=2,
                    coded_value_raw=str(0xa7),
                ),
                ValueParameter(
                    short_name="temperature",
                    byte_position=3,
                    dop_ref=OdxLinkRef("somersault.DOP.temperature", doc_frags),
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
            short_name="last_flip_details",
            long_name="Flip Details",
            description=Description.from_string(
                "<p>The details the last successfully executed request</p>"),
            semantic="DETAILS",
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
                    description=Description.from_string("<p>We have not done any flips yet!</p>"),
                    semantic="DETAILS-KEY",
                    dop_ref=OdxLinkRef.from_id(somersault_dops["soberness_check"].odx_id),
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_grudging",
                                     doc_frags),
                    short_name="forward_grudging",
                    long_name="Forward Flips Grudgingly Done",
                    key_raw="3",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["forward_flips_grudgingly_done"].odx_id),
                    description=Description.from_string(
                        "<p>The the last forward flip was grudgingly done</p>"),
                    semantic="DETAILS-KEY",
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.forward_happy", doc_frags),
                    short_name="forward_happily",
                    long_name="Forward Flips Happily Done",
                    key_raw="5",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["forward_flips_happily_done"].odx_id),
                ),
                TableRow(
                    table_ref=last_flip_details_table_ref,
                    odx_id=OdxLinkId("somersault.table.last_flip_details.backward", doc_frags),
                    short_name="backward_grudging",
                    long_name="Backward Flips",
                    key_raw="10",
                    structure_ref=OdxLinkRef.from_id(
                        somersault_structures["backward_flips_grudgingly_done"].odx_id),
                ),
            ],
        )
}

# requests
somersault_requests = {
    "start_session":
        Request(
            odx_id=OdxLinkId("somersault.RQ.start_session", doc_frags),
            short_name="start_session",
            long_name="Start the diagnostic session & do some mischief",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(
                        SID.DiagnosticSessionControl.value),  # type: ignore[attr-defined]
                ),
                CodedConstParameter(
                    short_name="id",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(0x0),
                ),
                ValueParameter(
                    short_name="bribe",
                    physical_default_value_raw="0",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.uint8", doc_frags),
                ),
            ]),
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
                    coded_value_raw=str(
                        SID.DiagnosticSessionControl  # type: ignore[attr-defined,arg-type]
                        .value),
                ),
                CodedConstParameter(
                    short_name="id",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(0x1),
                ),
            ],
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
                    coded_value_raw=str(
                        SID.TesterPresent.value),  # type: ignore[attr-defined,arg-type]
                ),
                CodedConstParameter(
                    short_name="id",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(0x0),
                ),
            ],
        ),
    "set_operation_params":
        Request(
            odx_id=OdxLinkId("somersault.RQ.set_operation_params", doc_frags),
            short_name="set_operation_params",
            long_name="Specify the mode of operation for the ECU; e.g. if rings "
            "of fire ought to be used for maximum effect",
            parameters=[
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(
                        SID.ForwardFlipCondition  # type: ignore[attr-defined,arg-type]
                        .value),
                ),
                ValueParameter(
                    short_name="use_fire_ring",
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.boolean", doc_frags),
                ),
            ],
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
                    coded_value_raw=str(
                        SID.ForwardFlip.value),  # type: ignore[attr-defined,arg-type]
                ),
                ValueParameter(
                    short_name="forward_soberness_check",
                    dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                    byte_position=1,
                    # value must be 0x12 for the request to be accepted
                ),
                ValueParameter(
                    short_name="num_flips",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                ),
            ],
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
                    coded_value_raw=str(
                        SID.BackwardFlip.value),  # type: ignore[attr-defined,arg-type]
                ),
                ValueParameter(
                    short_name="backward_soberness_check",
                    dop_ref=OdxLinkRef("somersault.DOP.soberness_check", doc_frags),
                    byte_position=1,
                    # value must be 0x21 for the request to be accepted
                ),
                ValueParameter(
                    short_name="num_flips",
                    byte_position=2,
                    dop_ref=OdxLinkRef("somersault.DOP.num_flips", doc_frags),
                ),
            ],
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
                    coded_value_raw=str(
                        SID.ReadDataByIdentifier  # type: ignore[attr-defined,arg-type]
                        .value),
                ),
                CodedConstParameter(
                    short_name="id",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=1,
                    coded_value_raw=str(0x0),
                ),
            ],
        ),
    "schroedinger":
        Request(
            odx_id=OdxLinkId("somersault.RQ.schroedinger", doc_frags),
            short_name="schroedinger_request",
            parameters=NamedItemList([
                ValueParameter(
                    short_name="schroedinger_param",
                    long_name="Parameter where the DOP changes dending on how you "
                    "look at the SNREF to it",
                    byte_position=0,
                    dop_snref="schroedinger_dop",
                ),
            ]),
        ),
}

# services
somersault_services = {
    "start_session":
        DiagService(
            odx_id=OdxLinkId("somersault.service.session_start", doc_frags),
            short_name="session_start",
            pre_condition_state_refs=[
                PreConditionStateRef(
                    ref_id="charts.annoyed.states.in_bed",
                    ref_docs=doc_frags,
                ),
                # note that the standard does not allow to specify
                # relations other than equivalence for the specified
                # value (larger-than would be more appropriate here...)
                PreConditionStateRef(
                    ref_id="charts.angry.states.in_bed",
                    ref_docs=doc_frags,
                    value="1",
                    in_param_if_snref="bribe",
                ),
            ],
            state_transition_refs=[
                StateTransitionRef(
                    ref_id="charts.annoyed.transitions.get_up",
                    ref_docs=doc_frags,
                    value="false",
                    in_param_if_snref="can_do_backward_flips",
                ),
                StateTransitionRef(
                    ref_id="charts.annoyed.transitions.get_up_to_park",
                    ref_docs=doc_frags,
                    value="true",
                    in_param_if_snref="can_do_backward_flips",
                ),
                StateTransitionRef(
                    ref_id="charts.angry.transitions.get_up",
                    ref_docs=doc_frags,
                ),
            ],
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
        ),
    "stop_session":
        DiagService(
            odx_id=OdxLinkId("somersault.service.session_stop", doc_frags),
            short_name="session_stop",
            state_transition_refs=[
                StateTransitionRef(
                    ref_id="charts.angry.transitions.go_to_bed",
                    ref_docs=doc_frags,
                ),
                StateTransitionRef(
                    ref_id="charts.annoyed.transitions.go_to_bed",
                    ref_docs=doc_frags,
                ),
            ],
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
        ),
    "tester_present":
        DiagService(
            odx_id=OdxLinkId("somersault.service.tester_present", doc_frags),
            short_name="tester_present",
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id),
                    OdxLinkRef.from_id(somersault_additional_audiences["anyone"].odx_id),
                ],
                is_development_raw=False,
            ),
            semantic="TESTERPRESENT",
            request_ref=OdxLinkRef.from_id(somersault_requests["tester_present"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["tester_ok"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["tester_nok"].odx_id),
            ],
        ),
    "set_operation_params":
        DiagService(
            odx_id=OdxLinkId("somersault.service.set_operation_params", doc_frags),
            short_name="set_operation_params",
            semantic="FUNCTION",
            request_ref=OdxLinkRef.from_id(somersault_requests["set_operation_params"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["set_operation_params"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
        ),
    "forward_flips":
        DiagService(
            odx_id=OdxLinkId("somersault.service.do_forward_flips", doc_frags),
            short_name="do_forward_flips",
            description=Description.from_string("<p>Do a forward flip.</p>"),
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                is_development_raw=False,
            ),
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
        ),
    "backward_flips":
        DiagService(
            odx_id=OdxLinkId("somersault.service.do_backward_flips", doc_frags),
            short_name="do_backward_flips",
            audience=Audience(
                enabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                is_development_raw=False,
            ),
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
        ),
    "report_status":
        DiagService(
            odx_id=OdxLinkId("somersault.service.report_status", doc_frags),
            short_name="report_status",
            audience=Audience(
                disabled_audience_refs=[
                    OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
                ],
                is_aftersales_raw=False,
                is_aftermarket_raw=False,
            ),
            semantic="CURRENTDATA",
            request_ref=OdxLinkRef.from_id(somersault_requests["report_status"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(somersault_positive_responses["status_report"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_negative_responses["general"].odx_id),
            ],
        ),
    "schroedinger":
        DiagService(
            odx_id=OdxLinkId("somersault.service.schroedinger", doc_frags),
            short_name="schroedinger",
            request_ref=OdxLinkRef.from_id(somersault_requests["schroedinger"].odx_id),
            semantic="ROUTINE",
        ),
}

somersault_single_ecu_jobs = {
    "compulsory_program":
        SingleEcuJob(
            odx_id=OdxLinkId("somersault.service.compulsory_program", doc_frags),
            short_name="compulsory_program",
            long_name="Compulsory Program",
            description=Description.from_string("<p>Do several fancy moves.</p>"),
            prog_codes=[
                ProgCode(
                    code_file="jobs.py",
                    syntax="PYTHON3",
                    entrypoint="compulsory_program",
                    revision="1.23.4",
                ),
            ],
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
    ),
    # timeout for responses [us]
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_RC21CompletionTimeout", cp_iso15765_3_doc_frags),
        value="1000000",
        protocol_snref="somersault_protocol",
    ),
    ###
    # "tester present" message handling
    ###
    # expected "tester present" message
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentMessage", cp_iso15765_3_doc_frags),
        value=f"{tester_present_value.hex()}",
        protocol_snref="somersault_protocol",
    ),
    # a response is mandatory
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="somersault_protocol",
    ),
    # positive response to "tester present"
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpPosResp", cp_iso15765_3_doc_frags),
        value=f"{tester_pr_value.hex()}",
        protocol_snref="somersault_protocol",
    ),
    # negative response to "tester present"
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentExpNegResp", cp_iso15765_3_doc_frags),
        value=f"{tester_nr_value.hex()}",
        protocol_snref="somersault_protocol",
    ),
    # when a tester present message must be send
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentSendType", cp_iso15765_3_doc_frags),
        value="On idle",
        protocol_snref="somersault_protocol",
    ),
    # "tester present" messages are send directly to the CAN IDs
    # (i.e., they are not embedded in the ISO-TP telegram?)
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentAddrMode", cp_iso15765_3_doc_frags),
        value="Physical",
        protocol_snref="somersault_protocol",
    ),
    # is a response from the ECU to "tester present" messages expected
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_3.CP_TesterPresentReqRsp", cp_iso15765_3_doc_frags),
        value="Response expected",
        protocol_snref="somersault_protocol",
    ),
    ###
    # ISO-TP parameters:
    ###
    # maximum number of frames between flow control ACKs
    ComparamInstance(
        spec_ref=OdxLinkRef("ISO_15765_2.CP_BlockSize", cp_iso15765_2_doc_frags),
        value="4",
        protocol_snref="somersault_protocol",
    ),
]

somersault_base_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=NamedItemList(
        [x for x in somersault_dops.values() if x.short_name != "schroedinger_dop"] +
        [somersault_dops["schroedinger_base"]]),
    unit_spec=UnitSpec(
        unit_groups=NamedItemList(somersault_unit_groups.values()),
        units=NamedItemList(somersault_units.values()),
        physical_dimensions=NamedItemList(somersault_physical_dimensions.values()),
    ),
    tables=NamedItemList(somersault_tables.values()),
    structures=NamedItemList(somersault_structures.values()),
)

somersault_lazy_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=NamedItemList([somersault_dops["schroedinger_lazy"]]))

somersault_assiduous_diag_data_dictionary_spec = DiagDataDictionarySpec(
    data_object_props=NamedItemList([somersault_dops["schroedinger_assiduous"]]))

# diagnostics layer for the protocol
somersault_protocol_raw = ProtocolRaw(
    variant_type=DiagLayerType.PROTOCOL,
    odx_id=OdxLinkId("somersault.protocol", doc_frags),
    short_name="somersault_protocol",
    long_name="Somersault protocol info",
    description=Description.from_string(
        "<p>Protocol information of the somersault ECUs &amp; cetera</p>"),
    comparam_spec_ref=OdxLinkRef("CPS_ISO_15765_3_on_ISO_15765_2", (OdxDocFragment(
        "ISO_15765_3_on_ISO_15765_2", DocType.COMPARAM_SPEC),)),
    comparam_refs=somersault_comparam_refs,
)
somersault_protocol = Protocol(diag_layer_raw=somersault_protocol_raw)

# diagnostics layer for the base variant
somersault_base_variant_raw = BaseVariantRaw(
    variant_type=DiagLayerType.BASE_VARIANT,
    odx_id=OdxLinkId("somersault.base_variant", doc_frags),
    short_name="somersault_base_variant",
    long_name="Somersault base variant",
    description=Description.from_string("<p>Base variant of the somersault ECU &amp; cetera</p>"),
    functional_classes=NamedItemList(somersault_functional_classes.values()),
    diag_data_dictionary_spec=somersault_base_diag_data_dictionary_spec,
    diag_comms_raw=[*somersault_services.values(), *somersault_single_ecu_jobs.values()],
    requests=NamedItemList(somersault_requests.values()),
    positive_responses=NamedItemList(somersault_positive_responses.values()),
    negative_responses=NamedItemList(somersault_negative_responses.values()),
    global_negative_responses=NamedItemList(somersault_global_negative_responses.values()),
    additional_audiences=NamedItemList(somersault_additional_audiences.values()),
    parent_refs=[ParentRef(layer_ref=OdxLinkRef.from_id(somersault_protocol.odx_id))])
somersault_base_variant = BaseVariant(diag_layer_raw=somersault_base_variant_raw)

##################
# Lazy variant of Somersault ECU: this one is lazy and cuts corners
##################

somersault_lazy_ecu_raw = EcuVariantRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_lazy", doc_frags),
    short_name="somersault_lazy",
    long_name="Somersault lazy ECU",
    description=Description.from_string(
        "<p>Sloppy variant of the somersault ECU (lazy &lt; assiduous)</p>"),
    diag_data_dictionary_spec=somersault_lazy_diag_data_dictionary_spec,
    state_charts=NamedItemList([
        StateChart(
            semantic="annoyed",
            odx_id=OdxLinkId("charts.annoyed.chart", doc_frags),
            short_name="annoyed_chart",
            description=Description.from_string(
                "<p>State chart for a day where the ECU is grumpy</p>"),
            states=NamedItemList([
                State(
                    odx_id=OdxLinkId("charts.annoyed.states.in_bed", doc_frags),
                    short_name="in_bed",
                ),
                State(
                    odx_id=OdxLinkId("charts.annoyed.states.on_street", doc_frags),
                    short_name="on_street",
                ),
                State(
                    odx_id=OdxLinkId("charts.annoyed.states.in_park", doc_frags),
                    short_name="in_park",
                ),
                State(
                    odx_id=OdxLinkId("charts.annoyed.states.at_lunch", doc_frags),
                    short_name="at_lunch",
                ),
            ]),
            start_state_snref="in_bed",
            state_transitions=[
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.get_up", doc_frags),
                    short_name="get_up",
                    source_snref="in_bed",
                    target_snref="on_street",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.get_up_to_park", doc_frags),
                    short_name="get_up_to_park",
                    source_snref="in_bed",
                    target_snref="in_park",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.go_to_bed", doc_frags),
                    short_name="go_to_bed",
                    source_snref="on_street",
                    target_snref="in_bed",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.move", doc_frags),
                    short_name="move",
                    source_snref="on_street",
                    target_snref="in_park",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.stumble", doc_frags),
                    short_name="stumble",
                    source_snref="on_street",
                    target_snref="at_lunch",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.annoyed.transitions.caffeinated", doc_frags),
                    short_name="caffeinated",
                    source_snref="at_lunch",
                    target_snref="in_park",
                ),
            ]),
        StateChart(
            semantic="angry",
            odx_id=OdxLinkId("charts.angry.chart", doc_frags),
            short_name="angry_chart",
            description=Description.from_string(
                "<p>State chart for a day where the ECU has a hissy fit</p>"),
            states=NamedItemList([
                State(
                    odx_id=OdxLinkId("charts.angry.states.in_bed", doc_frags),
                    short_name="in_bed",
                ),
                State(
                    odx_id=OdxLinkId("charts.angry.states.on_street", doc_frags),
                    short_name="on_street",
                ),
                State(
                    odx_id=OdxLinkId("charts.angry.states.in_park", doc_frags),
                    short_name="in_park",
                ),
                State(
                    odx_id=OdxLinkId("charts.angry.states.at_lunch", doc_frags),
                    short_name="at_lunch",
                ),
                State(
                    odx_id=OdxLinkId("charts.angry.states.in_hospital", doc_frags),
                    short_name="in_hospital",
                ),
            ]),
            start_state_snref="in_bed",
            state_transitions=[
                StateTransition(
                    odx_id=OdxLinkId("charts.angry.transitions.get_up", doc_frags),
                    short_name="get_up",
                    source_snref="in_bed",
                    target_snref="on_street",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.angry.transitions.go_to_bed", doc_frags),
                    short_name="go_to_bed",
                    source_snref="on_street",
                    target_snref="in_bed",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.angry.transitions.move", doc_frags),
                    short_name="move",
                    source_snref="on_street",
                    target_snref="in_park",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.angry.transitions.stumble", doc_frags),
                    short_name="stumble",
                    source_snref="on_street",
                    target_snref="at_lunch",
                ),
                StateTransition(
                    odx_id=OdxLinkId("charts.angry.transitions.caffeinated", doc_frags),
                    short_name="caffeinated",
                    source_snref="at_lunch",
                    target_snref="in_park",
                ),
            ],
        ),
    ]),
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_base_variant.odx_id),
            # this variant does not do backflips and does not like
            # being told under which conditions it operates.
            not_inherited_diag_comms=[
                somersault_requests["backward_flips"].short_name,
                somersault_requests["set_operation_params"].short_name,
            ],
        )
    ],
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
            short_name="do_headstand",
            long_name="Do a headstand & whatever else is required to entertain the customer",
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(0x3),
                ),
                ValueParameter(
                    short_name="duration",
                    byte_position=1,
                    dop_ref=OdxLinkRef("somersault.DOP.duration", doc_frags),
                ),
            ]),
        ),
}

# positive responses
somersault_assiduous_positive_responses = {
    "headstand_done":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.PR.headstand_done", doc_frags),
            short_name="headstand_done",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(0x1),
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    short_name="duration",
                    request_byte_position=1,
                    byte_position=1,
                    byte_length=1,
                ),
            ]),
        ),
}

# negative responses
somersault_assiduous_negative_responses = {
    "fell_over":
        Response(
            odx_id=OdxLinkId("somersault_assiduous.NR.fell_over", doc_frags),
            short_name="fell_over",
            response_type=ResponseType.POSITIVE,
            parameters=NamedItemList([
                CodedConstParameter(
                    short_name="sid",
                    diag_coded_type=somersault_diagcodedtypes["uint8"],
                    byte_position=0,
                    coded_value_raw=str(0x20),
                ),
                # TODO (?): non-byte aligned MatchingRequestParameters
                MatchingRequestParameter(
                    short_name="duration",
                    request_byte_position=1,  # somersault_assiduous_requests["headstand"]["duration"].byte_position
                    byte_position=1,
                    byte_length=1,
                ),
            ]),
        ),
}

# services
somersault_assiduous_services = {
    "headstand":
        DiagService(
            odx_id=OdxLinkId("somersault_assiduous.service.headstand", doc_frags),
            short_name="headstand",
            request_ref=OdxLinkRef.from_id(somersault_assiduous_requests["headstand"].odx_id),
            pos_response_refs=[
                OdxLinkRef.from_id(
                    somersault_assiduous_positive_responses["headstand_done"].odx_id),
            ],
            neg_response_refs=[
                OdxLinkRef.from_id(somersault_assiduous_negative_responses["fell_over"].odx_id),
            ],
            audience=Audience(enabled_audience_refs=[
                OdxLinkRef.from_id(somersault_additional_audiences["attentive_admirer"].odx_id)
            ]),
        ),
}

somersault_assiduous_ecu_raw = EcuVariantRaw(
    variant_type=DiagLayerType.ECU_VARIANT,
    odx_id=OdxLinkId("somersault_assiduous", doc_frags),
    short_name="somersault_assiduous",
    long_name="Somersault assiduous ECU",
    description=Description.from_string(
        "<p>Hard-working variant of the somersault ECU (lazy &lt; assiduous)</p>"),
    diag_data_dictionary_spec=somersault_assiduous_diag_data_dictionary_spec,
    diag_comms_raw=list(somersault_assiduous_services.values()),
    requests=NamedItemList(somersault_assiduous_requests.values()),
    positive_responses=NamedItemList(somersault_assiduous_positive_responses.values()),
    negative_responses=NamedItemList(somersault_assiduous_negative_responses.values()),
    parent_refs=[
        ParentRef(
            layer_ref=OdxLinkRef.from_id(somersault_base_variant.odx_id),
            # this variant does everything which the base variant does
            # and more
            not_inherited_dops=["schroedinger"],
        )
    ],
    comparam_refs=somersault_comparam_refs,
)
somersault_assiduous_ecu = EcuVariant(diag_layer_raw=somersault_assiduous_ecu_raw)

##################
# Container with all ECUs
##################

# create a "diagnosis layer container" object
somersault_dlc = DiagLayerContainer(
    odx_id=OdxLinkId("DLC.somersault", doc_frags),
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
    protocols=NamedItemList([somersault_protocol]),
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
        category_sn = odxrequire(subset.findtext("SHORT-NAME"))
        context = OdxDocContext(ODX_VERSION,
                                (OdxDocFragment(category_sn, DocType.COMPARAM_SUBSET),))
        comparam_subsets.append(ComparamSubset.from_et(subset, context))

comparam_specs = []
for odx_c_filename in ("UDSOnCAN_CPS.odx-c",):
    odx_c_root = ElementTree.parse(odx_cs_dir / odx_c_filename).getroot()
    subset = odx_c_root.find("COMPARAM-SPEC")
    if subset is not None:
        category_sn = odxrequire(subset.findtext("SHORT-NAME"))
        context = OdxDocContext(ODX_VERSION, (OdxDocFragment(category_sn, DocType.COMPARAM_SPEC),))
        comparam_specs.append(ComparamSpec.from_et(subset, context))

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
