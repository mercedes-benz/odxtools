#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
import argparse

from ..database import Database
from ..load_file import load_file as _load_file


def add_pdx_argument(parser: argparse.ArgumentParser, is_optional: bool = False) -> None:
    parser.add_argument(
        "pdx_file",
        help="Location of the .pdx file",
        nargs="?" if is_optional else 1,
        metavar="PDX_FILE")


def load_file(args: argparse.Namespace) -> Database:
    pdx_file_name = args.pdx_file if isinstance(args.pdx_file, str) else args.pdx_file[0]
    return _load_file(pdx_file_name)
