#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
#
# This script demonstrates how an existing ODX database can be
# modified programatically. Note that this is pretty hacky...
import argparse
from copy import deepcopy

import odxtools
import odxtools.uds as uds
from examples import somersaultecu
from odxtools.diaglayer import DiagLayer
from odxtools.diagservice import DiagService
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxLinkId, OdxLinkRef
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.request import Request
from odxtools.response import Response, ResponseType

argparser = argparse.ArgumentParser(
    description="\n".join([
        "Creates a simple sample PDX file for a modified 'somersault' ECU from scratch.", "",
        "The modified PDX file is primarily intended to be used a demo for the ",
        "'compare' command line tool."
    ]),
    formatter_class=argparse.RawTextHelpFormatter,
)

argparser.add_argument(
    "output_pdx_file",
    metavar="OUTPUT_PDX_FILE",
    help="Path to the where the resulting .pdx file is written",
)

args = argparser.parse_args()

FLIC_FLAC_SID = 0xBE

db = somersaultecu.database

dlc = db.diag_layer_containers[0]

# modify the positive response of the tester_present service for all ECUs
somersault_dlr = dlc.base_variants.somersault.diag_layer_raw

tester_present_service = [
    x for x in somersault_dlr.diag_comms if getattr(x, "short_name", None) == "tester_present"
][0]
assert isinstance(tester_present_service, DiagService)
tester_present_pr = tester_present_service.positive_responses[0]
param = tester_present_pr.parameters.status
assert isinstance(param, CodedConstParameter)
param.diag_coded_type = somersaultecu.somersault_diagcodedtypes["uint16"]
param.coded_value = 0x1234

# add a new "somersault_young" variant which can do flic-flacs and
# does not take any instructions
somersault_young = deepcopy(dlc.ecu_variants.somersault_lazy)
somersault_young_dlr = dlc.ecu_variants.somersault_lazy.diag_layer_raw
somersault_young_dlr.short_name = "somersault_young"
somersault_young_dlr.odx_id = OdxLinkId("ECU.somersault_young",
                                        somersault_young_dlr.odx_id.doc_fragments)
somersault_young_dlr.description = \
"""<p>A young version of the somersault ECU

It is as grumpy as the lazy variant, but it is more agile, so it can do flic-flacs.

On the flipside it is unwilling to take any instructions, so no operational parameters
can be set.
</p>"""

# remove the "sault_time" parameter from the positive response of the
# "do_forward_flips" service.
do_forward_flips_service = somersault_young.services.do_forward_flips
pr = do_forward_flips_service.positive_responses[0]
new_params = [x for x in pr.parameters if x.short_name != "sault_time"]
pr.parameters = NamedItemList(new_params)
somersault_young_dlr.diag_comms.append(do_forward_flips_service)
doc_frags = do_forward_flips_service.odx_id.doc_fragments

# add "flic-flac" service
flic_flac_request = Request(
    odx_id=OdxLinkId("somersault.RQ.flic_flac", doc_frags),
    short_name="RQ_flic_flac",
    long_name=None,
    description=None,
    admin_data=None,
    sdgs=[],
    parameters=NamedItemList([
        CodedConstParameter(
            short_name="sid",
            long_name=None,
            semantic=None,
            description=None,
            diag_coded_type=somersaultecu.somersault_diagcodedtypes["uint8"],
            byte_position=0,
            coded_value=FLIC_FLAC_SID,
            bit_position=None,
            sdgs=[],
        )
    ]),
    byte_size=None,
)
somersault_young_dlr.requests.append(flic_flac_request)

flic_flac_positive_response = Response(
    odx_id=OdxLinkId("somersault.PR.flic_flac", doc_frags),
    short_name="PR_flic_flac",
    long_name=None,
    description=None,
    admin_data=None,
    sdgs=[],
    response_type=ResponseType.POSITIVE,
    parameters=NamedItemList([
        CodedConstParameter(
            short_name="sid",
            long_name=None,
            semantic=None,
            description=None,
            diag_coded_type=somersaultecu.somersault_diagcodedtypes["uint8"],
            byte_position=0,
            coded_value=uds.positive_response_id(FLIC_FLAC_SID),
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
    ]),
    byte_size=None,
)
somersault_young_dlr.positive_responses.append(flic_flac_positive_response)

flic_flac_service = DiagService(
    odx_id=OdxLinkId("somersault.service.flic_flac", doc_frags),
    short_name="flic_flac",
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
    request_ref=OdxLinkRef.from_id(flic_flac_request.odx_id),
    pos_response_refs=[
        OdxLinkRef.from_id(flic_flac_positive_response.odx_id),
    ],
    neg_response_refs=[
        OdxLinkRef.from_id(somersaultecu.somersault_negative_responses["general"].odx_id),
    ],
    sdgs=[],
)

# create a new list of diagnostic communications that does not include
# the "set_operation_params" service
ss_young_diag_comms = [
    x for x in somersault_young_dlr.diag_comms
    if getattr(x, "short_name", None) != "somersault_young_dlr"
]

# append the flic-flac service
ss_young_diag_comms.append(flic_flac_service)

# change the list of the ECU's diag comms
somersault_young_dlr.diag_comms = ss_young_diag_comms

dlc.ecu_variants.append(DiagLayer(diag_layer_raw=somersault_young_dlr))

# make the database consistent. Note: For just writing the object to
# disk, this is not necessary (but it is useful if the object is going
# to be used for something else later...)
db.refresh()

# write the result
odxtools.write_pdx_file(args.output_pdx_file, db)
