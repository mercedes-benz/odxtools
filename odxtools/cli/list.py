# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import argparse
from typing import cast, List, Union

from ._print_utils import print_diagnostic_service, format_desc
from . import _parser_utils

from ..database import Database
from ..diaglayer import DiagLayer
from ..service import DiagService
from ..singleecujob import SingleEcuJob

# name of the tool
_odxtools_tool_name_ = "list"

def print_summary(odxdb: Database,
                  print_services=False,
                  print_dops=False,
                  print_params=False,
                  print_com_params=False,
                  print_pre_condition_states=False,
                  print_state_transitions=False,
                  print_audiences=False,
                  allow_unknown_bit_lengths=False,
                  variants=None,
                  service_filter=lambda x: True):

    diag_layer_names = variants if variants else [
        dl.short_name for dl in odxdb.diag_layers
    ]

    for dl_sn in diag_layer_names:
        dl = odxdb.diag_layers[dl_sn]
        if not dl:
            print(f"The variant '{dl_sn}' could not be found!")
            continue

        assert isinstance(dl, DiagLayer)
        all_services: List[Union[DiagService, SingleEcuJob]] \
            = sorted(dl.services,
                     key=lambda x: x.short_name)

        data_object_properties = dl.data_object_properties
        com_params = dl.communication_parameters

        if (rx_id := dl.get_receive_id()) is not None:
            recv_id = hex(rx_id)
        else:
            recv_id = "None"

        if (tx_id := dl.get_send_id()) is not None:
            send_id = hex(tx_id)
        else:
            send_id = "None"

        print(
            f"{dl.variant_type} '{dl.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
        )
        print(
            f" num services: {len(all_services)}, num DOPs: {len(data_object_properties)}, num communication parameters: {len(com_params)}."
        )

        if dl.description:
            desc = format_desc(dl.description, ident=2)
            print(f" Description: " + desc)

        if print_services and len(all_services) > 0:
            services = [s for s in all_services if service_filter(s)]
            if len(services) > 0:
                print(
                    f"The services of the {dl.variant_type} '{dl.short_name}' are: ")
                for service in services:
                    if isinstance(service, DiagService):
                        print_diagnostic_service(
                            service,
                            print_params=print_params,
                            print_pre_condition_states=print_pre_condition_states,
                            print_state_transitions=print_state_transitions,
                            print_audiences=print_audiences,
                            allow_unknown_bit_lengths=allow_unknown_bit_lengths
                        )
                    elif isinstance(service, SingleEcuJob):
                        print(f" Single ECU job: {service.odx_id}")
                    else:
                        print(f" Unidentifiable service: {service}")

        if print_dops and len(data_object_properties) > 0:
            print(f"The DOPs of the {dl.variant_type} '{dl.short_name}' are: ")
            for dop in sorted(data_object_properties, key=lambda x: (type(x).__name__, x.short_name)):
                print("  " + str(dop).replace("\n", "\n  "))

        if print_com_params and len(com_params) > 0:
            print(
                f"The communication parameters of the {dl.variant_type} '{dl.short_name}' are: ")
            for com_param in com_params:
                print(f"  {com_param.id_ref}: {com_param.value}")


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        "list",
        description="\n".join([
            "List the content of automotive diagnostic files (*.pdx)",
            "",
            "Examples:",
            "  For displaying only the names of the diagnostic layers use:",
            "    odxtools list ./path/to/database.pdx",
            "  For displaying all content use:",
            "    odxtools list ./path/to/database.pdx --all",
            "  For more information use:",
            "    odxtools list -h"
        ]),
        help="Print a summary of automotive diagnostic files.",
        formatter_class=argparse.RawTextHelpFormatter)
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument("-v", "--variants", nargs='+', metavar="VARIANT",
                        required=False, help="Specifies which variants should be included.", default="all")

    # The service option is None if option is not passed at all (-> do not print services). It is an empty list if --services is passed
    parser.add_argument("-s", "--services", nargs='*', default=None, metavar="SERVICE",
                        required=False, help="Print a list of diagnostic services specified in the pdx. \n"
                        + "If no service names are specified, all services are printed.")
    # Pretty print message format and list parameters
    parser.add_argument("-p", "--params", default=False, action='store_const', const=True,
                        required=False, help="Print a list of all parameters relevant for the selected items.\n")
    parser.add_argument("-d", "--dops", default=False, action='store_const', const=True,
                        required=False, help="Print a list of all data object properties relevant for the selected items")

    # Shortcut to just dump everything
    parser.add_argument("-a", "--all", default=False, action='store_const', const=True,
                        required=False, help="Print a list of all diagnostic services and DOPs specified in the pdx")


def run(args):
    odxdb = _parser_utils.load_file(args)

    variants = args.variants if args.variants else None
    print_summary(odxdb, print_services=args.all or args.params or args.services is not None,
                  service_filter=(lambda s: s.short_name in args.services
                                  if args.services and len(args.services) > 0 else lambda s: True),
                  print_dops=args.all or args.dops, variants=None if variants == "all" else variants,
                  print_params=args.all or args.params,
                  print_com_params=args.all,
                  print_pre_condition_states=args.all,
                  print_state_transitions=args.all,
                  print_audiences=args.all,
                  allow_unknown_bit_lengths=args.all)
