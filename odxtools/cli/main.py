# SPDX-License-Identifier: MIT
import argparse
import importlib
from typing import Any, List

import odxtools
import odxtools.exceptions

from ..version import __version__ as odxtools_version
from .dummy_sub_parser import DummyTool

# import the tool modules which can be loaded. if a tool
# can't be loaded, add a dummy one
tool_modules: List[Any] = []
for tool_name in ["list", "browse", "snoop", "find", "decode", "compare"]:
    try:
        tool_modules.append(importlib.import_module(f".{tool_name}", package="odxtools.cli"))
    except Exception as e:
        tool_modules.append(DummyTool(tool_name, e))


def start_cli() -> None:
    argparser = argparse.ArgumentParser(
        description="\n".join([
            "Utilities to interact with automotive diagnostic descriptions based on the ODX standard.",
            "",
            "Examples:",
            "  For printing all services use:",
            "   odxtools list ./path/to/database.pdx --services",
            "  For browsing the data base and encoding messages use:",
            "   odxtools browse ./path/to/database.pdx",
        ]),
        prog="odxtools",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    argparser.add_argument(
        "--no-strict",
        action="store_true",
        default=False,
        required=False,
        help="Load the dataset in non-strict mode (which is more robust but might lead to undefined behavior)",
    )

    argparser.add_argument(
        "--version", required=False, action="store_true", help="Print the odxtools version")

    subparsers = argparser.add_subparsers(help="Select a subcommand", dest="subparser_name")

    for tool in tool_modules:
        tool.add_subparser(subparsers)

    args = argparser.parse_args()  # deals with the help message handling

    if args.version:
        print(f"odxtools {odxtools_version}")
        exit()
    if args.subparser_name is None:
        argparser.print_usage()
        exit()

    for tool in tool_modules:
        if tool._odxtools_tool_name_ == args.subparser_name:
            orig_strict = odxtools.exceptions.strict_mode
            odxtools.exceptions.strict_mode = not args.no_strict
            try:
                tool.run(args)
            finally:
                odxtools.exceptions.strict_mode = orig_strict
            return
