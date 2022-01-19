#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import odxtools
import argparse

argparser = argparse.ArgumentParser(
    description="\n".join([
        "Read in a PDX file and write back the resulting database object.",
        "",
        "This is primarily intended to be a demonstration of how to write",
        "PDX files using odxtools, but it can also be used to strip",
        "'unnecessary' auxiliary data from the input PDX file.",
    ]),
    formatter_class=argparse.RawTextHelpFormatter)

argparser.add_argument("input_pdx_file", metavar="INPUT_PDX_FILE",
                       help="Path to the input .pdx file")
argparser.add_argument("output_pdx_file", metavar="OUTPUT_PDX_FILE",
                       help="Path to the where the resulting .pdx file is written")
argparser.add_argument(
    'aux_files',
    metavar='AUX_FILES',
    nargs='*',
    default=[],
    help='The names of the auxiliary files to be included in the resulting .pdx file')

args = argparser.parse_args()

in_file_name = args.input_pdx_file
out_file_name = args.output_pdx_file
aux_file_names = args.aux_files

# a content specifier is a tuple of (name_in_zipfile,
# content_data). Here we simply read all all content from files on
# the filesystem...
auxiliary_content = \
    [ (x, open(x, "rb").read()) for x in aux_file_names ]

print(f"Loading input file '{in_file_name}'...", end='', flush=True)
db = odxtools.load_pdx_file(in_file_name)
print(" done")

print(f"Writing output file '{out_file_name}'...", end='', flush=True)
odxtools.write_pdx_file(out_file_name, db, auxiliary_content)
print(" done")

