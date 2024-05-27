#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import argparse
from typing import Any, Protocol, runtime_checkable

from ..database import Database
from ..loadfile import load_file as _load_file


@runtime_checkable
class SubparsersList(Protocol):
    """This protocol reproduces the parts of `argparse._SubparsersAction` which are needed by odxtools

    Unfortunately this is necessary because
    `argparse._SubparsersAction` is a private class of the `argparse`
    module that is used by some of its public API and thus cannot be
    used outside of the `argparse` module.
    """

    def add_parser(self, name: str, **kwargs: Any) -> "argparse.ArgumentParser":
        ...


def add_pdx_argument(parser: argparse.ArgumentParser, is_optional: bool = False) -> None:
    parser.add_argument(
        "pdx_file",
        help="Location of the .pdx file",
        nargs="?" if is_optional else 1,
        metavar="PDX_FILE")


def load_file(args: argparse.Namespace) -> Database:
    pdx_file_name = args.pdx_file if isinstance(args.pdx_file, str) else args.pdx_file[0]
    return _load_file(pdx_file_name)
