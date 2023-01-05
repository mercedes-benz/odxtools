#! /usr/bin/python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2023 MBition GmbH

import argparse

import odxtools
from examples import somersaultecu

argparser = argparse.ArgumentParser(
    description="\n".join([
        "Creates a simple sample PDX file for a 'somersault' ECU from scratch.",
        "",
        "This is primarily intended to be a demonstration of how to define",
        "automotive diagnostic services in python and making them interact",
        "with existing tooling.",
    ]),
    formatter_class=argparse.RawTextHelpFormatter)

argparser.add_argument("output_pdx_file", metavar="OUTPUT_PDX_FILE",
                       help="Path to the where the resulting .pdx file is written")

args = argparser.parse_args()

odxtools.write_pdx_file(args.output_pdx_file, somersaultecu.database)
