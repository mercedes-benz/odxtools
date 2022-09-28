# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import argparse
import sys

class DummyTool:
    """A tool which acts as a placeholder for a "real" tool that
    could not be loaded for whatever reason.

    The intention is to be able to use tools that are available
    without them being disturbed by the ones which aren't. Tools which
    are not available should subparser appear in the list of available
    tools, but as soon as the functionality is attempted to be used it
    should bail out.
    """

    def __init__(self,
                 tool_name,
                 error):
        self._odxtools_tool_name_ = tool_name
        self._error = error

    def add_subparser(self, subparser_list):
        parser = subparser_list.add_parser(
            self._odxtools_tool_name_,
            description=f"Tool '{self._odxtools_tool_name_}' is unavailable: {self._error}",
            help="Dummy tool",
            formatter_class=argparse.RawTextHelpFormatter)

    def run(self, args: argparse.Namespace):
        print(f"Error: Tool '{self._odxtools_tool_name_}' is unavailable: {self._error}",
              file=sys.stderr)
        exit(1)
