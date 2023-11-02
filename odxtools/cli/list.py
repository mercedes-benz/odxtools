# SPDX-License-Identifier: MIT
import argparse
from typing import Callable, List, Optional

from ..database import Database
from ..diagcomm import DiagComm
from ..diaglayer import DiagLayer
from ..diagservice import DiagService
from ..singleecujob import SingleEcuJob
from . import _parser_utils
from ._print_utils import format_desc, print_diagnostic_service

# name of the tool
_odxtools_tool_name_ = "list"


def print_summary(
    odxdb: Database,
    print_global_negative_responses: bool = False,
    print_services: bool = False,
    print_dops: bool = False,
    print_params: bool = False,
    print_comparams: bool = False,
    print_pre_condition_states: bool = False,
    print_state_transitions: bool = False,
    print_audiences: bool = False,
    allow_unknown_bit_lengths: bool = False,
    variants: Optional[str] = None,
    service_filter: Callable[[DiagComm], bool] = lambda x: True,
) -> None:

    diag_layer_names = variants if variants else [dl.short_name for dl in odxdb.diag_layers]

    for dl_sn in diag_layer_names:
        dl = odxdb.diag_layers[dl_sn]
        if not dl:
            print(f"The variant '{dl_sn}' could not be found!")
            continue

        assert isinstance(dl, DiagLayer)
        all_services: List[DiagComm] = sorted(dl.services, key=lambda x: x.short_name)

        data_object_properties = dl.diag_data_dictionary_spec.data_object_props
        comparams = dl.comparams

        print(f"{dl.variant_type} '{dl.short_name}'")
        print(
            f" num services: {len(all_services)}, num DOPs: {len(data_object_properties)}, num communication parameters: {len(comparams)}."
        )

        for proto in dl.protocols:
            if (can_rx_id := dl.get_can_receive_id(proto.short_name)) is not None:
                print(f"  CAN receive ID for protocol '{proto.short_name}': 0x{can_rx_id:x}")

            if (can_tx_id := dl.get_can_send_id(proto.short_name)) is not None:
                print(f"  CAN send ID for protocol '{proto.short_name}': 0x{can_tx_id:x}")

        if dl.description:
            desc = format_desc(dl.description, ident=2)
            print(f" Description: " + desc)

        if print_global_negative_responses and dl.global_negative_responses:
            print(f"The global negative responses of '{dl.short_name}' are: ")
            for gnr in dl.global_negative_responses:
                print(f" {gnr}")

        if print_services and len(all_services) > 0:
            services = [s for s in all_services if service_filter(s)]
            if len(services) > 0:
                print(f"The services of '{dl.short_name}' are: ")
                for service in services:
                    if isinstance(service, DiagService):
                        print_diagnostic_service(
                            service,
                            print_params=print_params,
                            print_pre_condition_states=print_pre_condition_states,
                            print_state_transitions=print_state_transitions,
                            print_audiences=print_audiences,
                            allow_unknown_bit_lengths=allow_unknown_bit_lengths,
                        )
                    elif isinstance(service, SingleEcuJob):
                        print(f" Single ECU job: {service.odx_id}")
                    else:
                        print(f" Unidentifiable service: {service}")

        if print_dops and len(data_object_properties) > 0:
            print(f"The DOPs of the {dl.variant_type} '{dl.short_name}' are: ")
            for dop in sorted(
                    data_object_properties, key=lambda x: (type(x).__name__, x.short_name)):
                print("  " + str(dop).replace("\n", "\n  "))

        if print_comparams and len(comparams) > 0:
            print(
                f"The communication parameters of the {dl.variant_type.value} '{dl.short_name}' are: "
            )
            for com_param in comparams:
                print(f"  {com_param.short_name}: {com_param.value}")


def add_subparser(subparsers: "argparse._SubParsersAction") -> None:
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
            "    odxtools list -h",
        ]),
        help="Print a summary of automotive diagnostic files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "-v",
        "--variants",
        nargs="+",
        metavar="VARIANT",
        required=False,
        help="Specifies which variants should be included.",
        default="all",
    )

    parser.add_argument(
        "-g",
        "--global-negative-responses",
        default=False,
        action="store_const",
        const=True,
        required=False,
        help="Print a list of the global negative responses for the selected ECUs.",
    )

    # The service option is None if option is not passed at all (-> do not print services). It is an empty list if --services is passed
    parser.add_argument(
        "-s",
        "--services",
        nargs="*",
        default=None,
        metavar="SERVICE",
        required=False,
        help="Print a list of diagnostic services specified in the pdx. \n" +
        "If no service names are specified, all services are printed.",
    )
    # Pretty print message format and list parameters
    parser.add_argument(
        "-p",
        "--params",
        default=False,
        action="store_const",
        const=True,
        required=False,
        help="Print a list of all parameters relevant for the selected items.\n",
    )
    parser.add_argument(
        "-d",
        "--dops",
        default=False,
        action="store_const",
        const=True,
        required=False,
        help="Print a list of all data object properties relevant for the selected items",
    )

    # Shortcut to just dump everything
    parser.add_argument(
        "-a",
        "--all",
        default=False,
        action="store_const",
        const=True,
        required=False,
        help="Print a list of all diagnostic services and DOPs specified in the pdx",
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    def service_filter(s: DiagComm) -> bool:
        if args.services and len(args.services) > 0:
            return s.short_name in args.services
        return True

    variants = args.variants if args.variants else None
    print_summary(
        odxdb,
        print_global_negative_responses=args.all or args.global_negative_responses,
        print_services=args.all or args.params or args.services is not None,
        service_filter=service_filter,
        print_dops=args.all or args.dops,
        variants=None if variants == "all" else variants,
        print_params=args.all or args.params,
        print_comparams=args.all,
        print_pre_condition_states=args.all,
        print_state_transitions=args.all,
        print_audiences=args.all,
        allow_unknown_bit_lengths=args.all,
    )
