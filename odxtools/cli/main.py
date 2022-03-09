# SPDX-License-Identifier: MIT
# Copyright (c) 2021-2022 MBition GmbH

import argparse

from . import list
from . import browse
from . import snoop
from . import find

from ..version import __version__ as odxtools_version

def start_cli():
    argparser = argparse.ArgumentParser(
        description="\n".join([
            "Utilities to interact with automotive diagnostic descriptions based on the ODX standard.",
            "",
            "Examples:",
            "  For printing all services use:",
            "   odxtools list ./path/to/database.pdx --services",
            "  For browsing the data base and encoding messages use:",
            "   odxtools browse ./path/to/database.pdx"
        ]),
        prog="odxtools",
        formatter_class=argparse.RawTextHelpFormatter)

    argparser.add_argument("--version", required=False,
                           action='store_true',
                           help="Print the odxtools version")

    subparsers = argparser.add_subparsers(
        help='Select a subcommand',
        dest="subparser_name"
    )

    list.add_subparser(subparsers)
    browse.add_subparser(subparsers)
    snoop.add_subparser(subparsers)
    find.add_subparser(subparsers)

    args = argparser.parse_args()  # deals with the help message handling

    if args.version:
        print(f"odxtools {odxtools_version}")
        exit()
    if args.subparser_name is None:
        argparser.print_usage()
        exit()

    if args.subparser_name == "list":
        list.run(args)
    elif args.subparser_name == "browse":
        browse.run(args)
    elif args.subparser_name == "snoop":
        snoop.run(args)
    elif args.subparser_name == "find":
        find.run(args)
