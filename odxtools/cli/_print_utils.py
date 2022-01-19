# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import re
import markdownify

from odxtools import DiagService


def format_desc(desc, ident=0):
    # Collapse whitespaces
    desc = re.sub(r'\s+', ' ', desc)
    # Covert XHTML to Markdown
    desc = markdownify.markdownify(desc)
    # Collapse blank lines
    desc = re.sub(r'(\n\s*)+\n+', '\n', desc).strip()

    if '\n' in desc:
        desc = '\n' + ident * ' ' + \
               ('\n' + ident * ' ').join(desc.split('\n'))
    return desc


def print_diagnostic_service(service: DiagService, print_params=False):

    print(f" {service.short_name} <ID: {service.id}>")

    if service.description:
        desc = format_desc(service.description, ident=3)
        print(f"  Service description: " + desc)

    if print_params:
        print(f"  Message format of a request:")
        service.request.print_message_format(indent=3)

        print(
            f"  Number of positive responses: {len(service.positive_responses)}")
        if len(service.positive_responses) == 1:
            print(f"  Message format of a positive response:")
            service.positive_responses[0].print_message_format(
                indent=3)

        print(
            f"  Number of negative responses: {len(service.negative_responses)}")
        if len(service.negative_responses) == 1:
            print(f"  Message format of a negative response:")
            service.negative_responses[0].print_message_format(
                indent=3)

    if len(service.positive_responses) > 1 or len(service.negative_responses) > 1:
        # Does this ever happen?
        raise NotImplementedError(
            f"The diagnostic service {service.id} offers more than one response!")
