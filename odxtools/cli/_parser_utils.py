#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from ..load_file import load_file as _load_file


def add_pdx_argument(parser):
    parser.add_argument(
        "pdx_file", metavar="PDX_FILE", help="path to the .pdx file")
    #parser.add_argument("pdx_files", metavar="PDX_FILES", nargs="+", help="PDX descriptions of all ECUs which shall be analyzed")

    # do not enable the CANdela workarounds. Note that we disable then
    # by default because CANdela is by far the most common tool to
    # work with ODX.
    # Note that the short option "-c" is reserved for the "--channel" of the snoop command.
    parser.add_argument("--conformant", default=False, action='store_const', const=True,
                        required=False, help="The input file fully confirms to the standard, i.e., disable work-arounds for bugs of the CANdela tool")


def load_file(args):
    db_file_name = args.pdx_file
    odxdb = None
    if db_file_name is not None:
        odxdb = _load_file(db_file_name,
                            enable_candela_workarounds=not args.conformant)
    return odxdb
