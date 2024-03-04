# SPDX-License-Identifier: MIT
import argparse
import sys
import traceback
from io import StringIO

from ._parser_utils import SubparsersList


class DummyTool:
    """A tool which acts as a placeholder for a "real" tool that
    could not be loaded for whatever reason.

    The intention is to be able to use tools that are available
    without them being disturbed by the ones which aren't. Tools which
    are not available should subparser appear in the list of available
    tools, but as soon as the functionality is attempted to be used it
    should bail out.
    """

    def __init__(self, tool_name: str, error: Exception):
        self._odxtools_tool_name_ = tool_name
        self._error = error

    def add_subparser(self, subparser_list: SubparsersList) -> None:
        desc = StringIO()

        print(f"Tool '{self._odxtools_tool_name_}' is unavailable: {self._error}", file=desc)
        print(file=desc)
        print(f"Traceback:", file=desc)
        traceback.print_tb(self._error.__traceback__, file=desc)

        subparser_list.add_parser(
            self._odxtools_tool_name_,
            description=desc.getvalue(),
            help="Tool unavailable",
            formatter_class=argparse.RawTextHelpFormatter,
        )

    def run(self, args: argparse.Namespace) -> None:
        print(
            f"Error: Tool '{self._odxtools_tool_name_}' is unavailable: {self._error}",
            file=sys.stderr,
        )
        exit(1)
