#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from ..load_file import load_file as _load_file


def add_pdx_argument(parser):
    parser.add_argument(
        "pdx_file", metavar="PDX_FILE", help="path to the .pdx file")
    #parser.add_argument("pdx_files", metavar="PDX_FILES", nargs="+", help="PDX descriptions of all ECUs which shall be analyzed")


def load_file(args):
    db_file_name = args.pdx_file
    odxdb = None
    if db_file_name is not None:
        odxdb = _load_file(db_file_name)
    return odxdb
