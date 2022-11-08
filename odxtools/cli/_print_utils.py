# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import re
import markdownify

from odxtools import DiagService
from odxtools.structures import Request, Response

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


def print_diagnostic_service(service: DiagService, print_params=False, print_pre_condition_states=False,
                             print_state_transitions=False, print_audiences=False, allow_unknown_bit_lengths=False):
    print(f" {service.short_name} <ID: {service.odx_id}>")

    if service.description:
        desc = format_desc(service.description, ident=3)
        print(f"  Service description: " + desc)

    if print_pre_condition_states and len(service.pre_condition_states) > 0:
        pre_condition_states_short_names = [pre_condition_state.short_name for pre_condition_state in service.pre_condition_states]
        print(f"  Pre-Condition-States: {', '.join(pre_condition_states_short_names)}")

    if print_state_transitions and len(service.state_transitions) > 0:
        state_transitions = [f"{state_transition.source_short_name} -> {state_transition.target_short_name}" for state_transition in service.state_transitions]
        print(f"  State-Transitions: {', '.join(state_transitions)}")

    if print_audiences and service.audience:
        enabled_audiences_short_names = [enabled_audience.short_name for enabled_audience in service.audience.enabled_audiences]
        print(f"  Enabled-Audiences: {', '.join(enabled_audiences_short_names)}")

    if print_params:
        assert service.request is not None
        assert service.positive_responses is not None
        assert service.negative_responses is not None

        print(f"  Message format of a request:")
        service.request.print_message_format(
            indent=3,
            allow_unknown_lengths=allow_unknown_bit_lengths)

        print(
            f"  Number of positive responses: {len(service.positive_responses)}")
        if len(service.positive_responses) == 1:
            resp = service.positive_responses[0]

            print(f"  Message format of a positive response:")
            resp.print_message_format(indent=3,
                                      allow_unknown_lengths=allow_unknown_bit_lengths)

        print(
            f"  Number of negative responses: {len(service.negative_responses)}")
        if len(service.negative_responses) == 1:
            resp = service.negative_responses[0]

            print(f"  Message format of a negative response:")
            resp.print_message_format(indent=3,
                                      allow_unknown_lengths=allow_unknown_bit_lengths)

    if ((service.positive_responses and len(service.positive_responses) > 1)
            or (service.negative_responses and len(service.negative_responses) > 1)):
        # Does this ever happen?
        raise NotImplementedError(
            f"The diagnostic service {service.odx_id} offers more than one response!")
