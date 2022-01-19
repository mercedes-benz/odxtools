# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import argparse

from . import list
from . import browse
from . import snoop
from . import find


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

    subparsers = argparser.add_subparsers(
        help='Select a sub command',
        dest="subparser_name"
    )

    list.add_subparser(subparsers)
    browse.add_subparser(subparsers)
    snoop.add_subparser(subparsers)
    find.add_subparser(subparsers)

    args = argparser.parse_args()  # deals with the help message handling

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
