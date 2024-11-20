# SPDX-License-Identifier: MIT
import argparse
from typing import Callable, List, Optional

import rich

from ..comparaminstance import ComparamInstance
from ..database import Database
from ..dataobjectproperty import DataObjectProperty
from ..diagcomm import DiagComm
from ..diaglayers.basevariant import BaseVariant
from ..diaglayers.diaglayer import DiagLayer
from ..diaglayers.ecuvariant import EcuVariant
from ..diaglayers.hierarchyelement import HierarchyElement
from ..diagservice import DiagService
from ..singleecujob import SingleEcuJob
from . import _parser_utils
from ._parser_utils import SubparsersList
from ._print_utils import format_desc, print_diagnostic_service, print_dl_metrics

# name of the tool
_odxtools_tool_name_ = "list"


def print_summary(odxdb: Database,
                  print_global_negative_responses: bool = False,
                  print_services: bool = False,
                  print_dops: bool = False,
                  print_params: bool = False,
                  print_comparams: bool = False,
                  print_pre_condition_states: bool = False,
                  print_state_transitions: bool = False,
                  print_audiences: bool = False,
                  allow_unknown_bit_lengths: bool = False,
                  variants: Optional[List[str]] = None,
                  service_filter: Callable[[DiagComm], bool] = lambda x: True) -> None:

    diag_layer_names = [dl.short_name for dl in odxdb.diag_layers]
    diag_layers: List[DiagLayer] = []

    if variants is None:
        variants = diag_layer_names

    for name in variants:
        if name in diag_layer_names:
            diag_layers.append([x for x in odxdb.diag_layers if x.short_name == name][0])

        else:
            rich.print(f"The variant '{name}' could not be found!")
            return

    if diag_layers:
        rich.print("\n")
        rich.print(f"Overview of diagnostic layers: ")
        print_dl_metrics(diag_layers)

    for dl in diag_layers:
        rich.print("\n")
        rich.print(f"Diagnostic layer: '{dl.short_name}'")
        rich.print(f" Variant Type: {dl.variant_type.value}")

        all_services: List[DiagComm] = sorted(dl.services, key=lambda x: x.short_name)

        if isinstance(dl, (BaseVariant, EcuVariant)):
            for proto in dl.protocols:
                if (can_rx_id := dl.get_can_receive_id(proto.short_name)) is not None:
                    rich.print(
                        f"  CAN receive ID for protocol '{proto.short_name}': 0x{can_rx_id:x}")

                if (can_tx_id := dl.get_can_send_id(proto.short_name)) is not None:
                    rich.print(f"  CAN send ID for protocol '{proto.short_name}': 0x{can_tx_id:x}")

        if dl.description:
            desc = format_desc(dl.description, indent=2)
            rich.print(f" Description: " + desc)

        if print_global_negative_responses and dl.global_negative_responses:
            rich.print("\n")
            rich.print(f"The global negative responses of '{dl.short_name}' are: ")
            for gnr in dl.global_negative_responses:
                rich.print(f" {gnr.short_name}")

        if print_services and len(all_services) > 0:
            services = [s for s in all_services if service_filter(s)]
            if len(services) > 0:
                rich.print("\n")
                rich.print(f"The services of '{dl.short_name}' are: ")
                for service in services:
                    if isinstance(service, DiagService):
                        print_diagnostic_service(
                            service,
                            print_params=print_params,
                            print_pre_condition_states=print_pre_condition_states,
                            print_state_transitions=print_state_transitions,
                            print_audiences=print_audiences,
                            allow_unknown_bit_lengths=allow_unknown_bit_lengths)
                    elif isinstance(service, SingleEcuJob):
                        rich.print(f" Single ECU job: {service.odx_id}")
                    else:
                        rich.print(f" Unidentifiable service: {service}")
        ddd_spec = dl.diag_data_dictionary_spec
        data_object_properties: List[
            DataObjectProperty] = [] if ddd_spec is None else ddd_spec.data_object_props
        if print_dops and len(data_object_properties) > 0:
            rich.print("\n")
            rich.print(f"The DOPs of the {dl.variant_type.value} '{dl.short_name}' are: ")
            for dop in sorted(
                    data_object_properties, key=lambda x: (type(x).__name__, x.short_name)):
                rich.print("  " + str(dop.short_name).replace("\n", "\n  "))

        comparam_refs: List[ComparamInstance] = []
        if isinstance(dl, HierarchyElement):
            comparam_refs = dl.comparam_refs

        if print_comparams and len(comparam_refs) > 0:
            rich.print("\n")
            rich.print(
                f"The communication parameters of the {dl.variant_type.value} '{dl.short_name}' are: "
            )
            for com_param in comparam_refs:
                rich.print(f"  {com_param.short_name}: {com_param.value}")


def add_subparser(subparsers: SubparsersList) -> None:
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

    parser.add_argument(
        "--dump-database",
        action="store_true",
        required=False,
        help="Ignore all other parameters and print a comprehensive dump the full database "
        "instead of providing a pretty-printed summary",
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)

    if args.dump_database:
        print(repr(odxdb))
        return

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
        allow_unknown_bit_lengths=args.all)
