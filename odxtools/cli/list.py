# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

import argparse
import re
import markdownify

from ..database import Database
from ..service import DiagService
from . import _parser_utils


def format_desc(desc, ident=0):
    # Collapse whitespaces
    desc = re.sub(r'\s+', ' ', desc)
    # Covert XHTML to Markdown
    desc = markdownify.markdownify(desc)
    # Collapse blank lines
    desc = re.sub(r'(\n\s*)+\n+', '\n', desc).strip()

    if '\n' in desc:
        desc = '\n' + ident * ' ' + \
            ('\n' + ident * ' ').join(desc.split('\n'))
    return desc


def print_diagnostic_service(service: DiagService, print_params=False):

    print(f" {service.short_name} <ID: {service.id}>")

    if service.description:
        desc = format_desc(service.description, ident=3)
        print(f"  Service description: " + desc)

    if print_params:
        print(f"  Message format of a request:")
        service.request.print_message_format(indent=3)

        print(
            f"  Number of positive responses: {len(service.positive_responses)}")
        if len(service.positive_responses) == 1:
            print(f"  Message format of a positive response:")
            service.positive_responses[0].print_message_format(
                indent=3)

        print(
            f"  Number of negative responses: {len(service.negative_responses)}")
        if len(service.negative_responses) == 1:
            print(f"  Message format of a negative response:")
            service.negative_responses[0].print_message_format(
                indent=3)

    if len(service.positive_responses) > 1 or len(service.negative_responses) > 1:
        # Does this ever happen?
        raise NotImplementedError(
            f"The diagnostic service {service.id} offers more than one response!")


def print_summary(odxdb: Database,
                  print_services=False,
                  print_dops=False,
                  print_params=False,
                  print_com_params=False,
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
        service_sns = sorted(service.short_name for service in dl.services)
        data_object_properties = dl.data_object_properties
        com_params = dl.communication_parameters

        if dl.get_receive_id() is not None:
            recv_id = hex(dl.get_receive_id())
        else:
            recv_id = "None"
        if dl.get_send_id() is not None:
            send_id = hex(dl.get_send_id())
        else:
            send_id = "None"
        print(
            f"{dl.variant_type} '{dl.short_name}' (Receive ID: {recv_id}, Send ID: {send_id})"
        )
        print(
            f" num services: {len(service_sns)}, num DOPs: {len(data_object_properties)}, num communication parameters: {len(com_params)}."
        )
        
        if dl.description:
            desc = format_desc(dl.description, ident=2)
            print(f" Description: " + desc)

        if print_services and len(service_sns) > 0:
            services = [dl.services[service_sn] for service_sn in service_sns]
            services = list(filter(service_filter, services))
            if len(services) > 0:
                print(
                    f"The services of the {dl.variant_type} '{dl.short_name}' are: ")
                for service in services:
                    if service_filter(service):
                        print_diagnostic_service(
                            service, print_params=print_params)

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
                  print_com_params=args.all)
