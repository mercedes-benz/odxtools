#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
#
# This script demonstrates how an existing ODX database can be
# modified programatically. Note that this is pretty hacky...
import argparse
from copy import deepcopy
from typing import List, TypeVar

import odxtools
import odxtools.uds as uds
from examples import somersaultecu
from odxtools.description import Description
from odxtools.diaglayers.diaglayer import DiagLayer
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diagservice import DiagService
from odxtools.nameditemlist import NamedItemList
from odxtools.odxlink import OdxLinkId, OdxLinkRef
from odxtools.parameters.codedconstparameter import CodedConstParameter
from odxtools.parameters.valueparameter import ValueParameter
from odxtools.request import Request
from odxtools.response import Response, ResponseType

T = TypeVar("T")


def find_named_object(item_list: List[T], name: str) -> T:
    for x in item_list:
        if getattr(x, "short_name", None) == name:
            return x

    raise KeyError(str(name))


FLIC_FLAC_SID = 0xBE

db = somersaultecu.database

dlc = db.diag_layer_containers[0]

# modify the positive response of the tester_present service for all ECUs
somersault_dlr = dlc.base_variants.somersault.diag_layer_raw

# rename the "session_start" and "session_stop" services to
# "start_session" and "stop_session"
start_service = find_named_object(somersault_dlr.diag_comms_raw, "session_start")
assert isinstance(start_service, DiagService)
start_service.short_name = "start_session"

stop_service = find_named_object(somersault_dlr.diag_comms_raw, "session_stop")
assert isinstance(stop_service, DiagService)
stop_service.short_name = "stop_session"

tester_present_service = find_named_object(somersault_dlr.diag_comms_raw, "tester_present")
assert isinstance(tester_present_service, DiagService)
tester_present_pr = tester_present_service.positive_responses[0]
param = tester_present_pr.parameters.status
assert isinstance(param, ValueParameter)
param.dop_ref = OdxLinkRef.from_id(somersaultecu.somersault_dops["uint16"].odx_id)

# change the DOP used by the "can_do_backward_flips" parameter of the
# positive response to the "session" service from "bool" to "uint8"
cdbf_param = start_service.positive_responses[0].parameters.can_do_backward_flips
doc_frags = start_service.odx_id.doc_fragments
assert isinstance(cdbf_param, ValueParameter)
cdbf_param.dop_ref = OdxLinkRef("somersault.DOP.uint8", doc_frags)

# change the byte and bit positions of the "num_flips_done" parameter
# of the "grudging_backward" response for all variants variant
gb_response = find_named_object(somersault_dlr.positive_responses, "grudging_backward")
param = gb_response.parameters.num_flips_done
param.byte_position = 2
param.bit_position = 4

# add a new "somersault_young" variant which can do flic-flacs and
# does not take any instructions
somersault_lazy = dlc.ecu_variants.somersault_lazy
somersault_young_dlr = deepcopy(somersault_lazy.ecu_variant_raw)
somersault_young_dlr.short_name = "somersault_young"
somersault_young_dlr.odx_id = OdxLinkId("ECU.somersault_young",
                                        somersault_young_dlr.odx_id.doc_fragments)
somersault_young_dlr.description = \
Description.from_string("""<p>A young version of the somersault ECU

It is as grumpy as the lazy variant, but it is more agile, so it can do flic-flacs.

On the flipside, it is unwilling to take any instructions, so no
operational parameters can be set. Finally, it is unwilling to compete
(i.e. it does not time its somersaults).</p>""")
somersault_young = DiagLayer(diag_layer_raw=somersault_young_dlr)

# remove the "sault_time" parameter from the positive response of the
# "do_forward_flips" service.
do_forward_flips_service = deepcopy(somersault_lazy.services.do_forward_flips)
somersault_young_dlr.diag_comms_raw.append(do_forward_flips_service)
pr = do_forward_flips_service.positive_responses[0]
new_params = [x for x in pr.parameters if getattr(x, "short_name", None) != "sault_time"]
pr.parameters = NamedItemList(new_params)

# add a new "flic-flac" service
flic_flac_request = Request(
    odx_id=OdxLinkId("somersault.RQ.flic_flac", doc_frags),
    oid=None,
    short_name="RQ_flic_flac",
    long_name=None,
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
            diag_coded_type=somersaultecu.somersault_diagcodedtypes["uint8"],
            byte_position=0,
            coded_value=FLIC_FLAC_SID,
            bit_position=None,
            sdgs=[],
        )
    ]),
)
somersault_young_dlr.requests.append(flic_flac_request)

flic_flac_positive_response = Response(
    odx_id=OdxLinkId("somersault.PR.flic_flac", doc_frags),
    oid=None,
    short_name="PR_flic_flac",
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
            diag_coded_type=somersaultecu.somersault_diagcodedtypes["uint8"],
            byte_position=0,
            coded_value=uds.positive_response_id(FLIC_FLAC_SID),
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
)
somersault_young_dlr.positive_responses.append(flic_flac_positive_response)

flic_flac_service = DiagService(
    odx_id=OdxLinkId("somersault.service.flic_flac", doc_frags),
    oid=None,
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
# the "set_operation_params" and "compulsory_program" services
ss_young_diag_comms_raw = [
    x for x in somersault_young_dlr.diag_comms_raw
    if getattr(x, "short_name", None) not in ("set_operation_params", "compulsory_program")
]

# append the flic-flac service
ss_young_diag_comms_raw.append(flic_flac_service)

# change the list of the ECU's diag comms
somersault_young_dlr.diag_comms_raw = ss_young_diag_comms_raw

dlc.ecu_variants.append(EcuVariant(diag_layer_raw=somersault_young_dlr))

# make the database consistent. Note: For just writing to disk this is
# not necessary (but it is useful if the database is going to be used
# for something else later...)
db.refresh()

if __name__ == "__main__":
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

    # write the result
    odxtools.write_pdx_file(args.output_pdx_file, db)
