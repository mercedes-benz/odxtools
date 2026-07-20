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

    # Map missing modules to install hints
    _INSTALL_HINTS: dict[str, str] = {
        "InquirerPy": 'pip install "odxtools[browse-tool]"',
        "PyYAML": 'pip install "odxtools[compare-tool]"',
        "can_isotp": 'pip install "odxtools[examples]"',
    }

    def __init__(self, tool_name: str, error: Exception):
        self._odxtools_tool_name_ = tool_name
        self._error = error

    def _format_error(self) -> str:
        """Return a user-friendly error message."""
        if isinstance(self._error, ModuleNotFoundError) and self._error.name is not None:
            hint = self._INSTALL_HINTS.get(self._error.name)
            if hint:
                return (
                    f"Error: Tool '{self._odxtools_tool_name_}' requires '{self._error.name}'.\n"
                    f"Install it with: {hint}")
            return (f"Error: Tool '{self._odxtools_tool_name_}' requires '{self._error.name}'.\n"
                    f"Install it with: pip install {self._error.name}")

        return f"Error: Tool '{self._odxtools_tool_name_}' is unavailable: {self._error}"

    def add_subparser(self, subparser_list: SubparsersList) -> None:
        desc = StringIO()
        print(self._format_error(), file=desc)
        print(file=desc)
        print(f"Traceback:", file=desc)
        traceback.print_tb(self._error.__traceback__, file=desc)

        parser = subparser_list.add_parser(
            self._odxtools_tool_name_,
            description=desc.getvalue(),
            help="Tool unavailable",
            formatter_class=argparse.RawTextHelpFormatter,
        )
        # Accept any positional arguments that the real tool would have taken,
        # so that argparse does not fail before we can display our error message.
        parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

    def run(self, args: argparse.Namespace) -> None:
        print(self._format_error(), file=sys.stderr)
        exit(1)
