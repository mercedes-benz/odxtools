# SPDX-License-Identifier: MIT
import argparse
from typing import Dict, List, Optional

from ..database import Database
from ..diagservice import DiagService
from ..odxtypes import ParameterValue
from ..singleecujob import SingleEcuJob
from . import _parser_utils
from ._print_utils import print_diagnostic_service

# name of the tool
_odxtools_tool_name_ = "find"


def get_display_value(v: ParameterValue) -> str:
    if isinstance(v, bytes):
        return v.hex(" ")
    elif isinstance(v, int):
        return f"{v} (0x{v:x})"
    else:
        return str(v)


def print_summary(odxdb: Database,
                  service_names: List[str],
                  ecu_variants: Optional[List[str]] = None,
                  allow_unknown_bit_lengths: bool = False,
                  print_params: bool = False) -> None:
    ecu_names = ecu_variants if ecu_variants else [ecu.short_name for ecu in odxdb.ecus]
    service_db: Dict[str, DiagService] = {}
    service_ecus: Dict[str, List[str]] = {}
    for ecu_name in ecu_names:
        ecu = odxdb.ecus[ecu_name]
        if not ecu:
            print(f"The ecu variant '{ecu_name}' could not be found!")
            continue

        if service_names:
            for service_name_search in service_names:
                for service in ecu.services:
                    if service_name_search.lower() in service.short_name.lower():
                        ecu_names = service_ecus.get(service.short_name, [])
                        ecu_names.append(ecu_name)
                        service_ecus[service.short_name] = ecu_names
                        service_db[service.short_name] = service

    for service_name, ecu_names in service_ecus.items():
        service = service_db[service_name]
        display_names = ", ".join(ecu_names)
        filler = str.ljust("", len(display_names), "=")
        print(f"\n{filler}")
        print(f"{', '.join(ecu_names)}")
        print(f"{filler}\n\n")
        if isinstance(service, DiagService):
            print_diagnostic_service(
                service,
                print_params=print_params,
                allow_unknown_bit_lengths=allow_unknown_bit_lengths,
                print_pre_condition_states=True,
                print_state_transitions=True,
                print_audiences=True,
            )
        elif isinstance(service, SingleEcuJob):
            print(f"SingleEcuJob: {service.odx_id}")
        else:
            print(f"Unknown service: {service}")


def add_subparser(subparsers: "argparse._SubParsersAction") -> None:
    parser = subparsers.add_parser(
        "find",
        description="\n".join([
            "Find & print services by name",
            "",
            "Examples:",
            "  For displaying the services associated with the partial name 'Reset' without details:",
            '    odxtools find ./path/to/database.pdx -s "Reset" --no-details',
            "  For more information use:",
            "    odxtools find -h",
        ]),
        help="Find & print services by hex-data, or name. Can also decode the request.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "-v",
        "--variants",
        nargs=1,
        metavar="VARIANT",
        required=False,
        help="Specifies which ecu variants should be included.",
        default="all",
    )

    parser.add_argument(
        "-s",
        "--service-names",
        nargs="*",
        default=None,
        metavar="SERVICES",
        required=True,
        help="Print a list of diagnostic services partially matching given service names",
    )

    parser.add_argument(
        "-nd",
        "--no-details",
        action="store_true",
        required=False,
        help="Don't show all service details",
    )

    parser.add_argument(
        "-ro",
        "--relaxed-output",
        action="store_true",
        required=False,
        help="Relax output formatting rules (allow unknown bitlengths for ascii representation)",
    )


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)
    variants = args.variants

    print_summary(
        odxdb,
        ecu_variants=None if variants == "all" else variants,
        service_names=args.service_names,
        print_params=not args.no_details,
        allow_unknown_bit_lengths=args.relaxed_output,
    )
