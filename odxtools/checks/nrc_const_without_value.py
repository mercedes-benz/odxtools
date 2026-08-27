# SPDX-License-Identifier: MIT
"""Check that every NRC-CONST parameter overlaps a VALUE parameter."""
from collections.abc import Iterable

from ..database import Database
from ..parameters.nrcconstparameter import NrcConstParameter
from ..parameters.valueparameter import ValueParameter
from .finding import Finding, Severity
from .overlapping_parameters import _bit_span
from .rule import is_composite_codec


class NrcConstWithoutValue:
    """An NRC-CONST parameter whose bits no VALUE parameter covers.

    ASAM MCD-2 D (ODX) 2.2, section 7.3.5.4: "The NRC-CONST is located at
    the same PDU position as the VALUE parameter. As a VALUE parameter is
    never used to match a RESPONSE, the parameter (and its associated
    TEXTTABLE) does not suffice to select the response."

    Decoding is not the problem: the matched value is exposed either way.
    Encoding is: an NRC-CONST refuses a directly set value, so the byte it
    matches on is meant to be written through the overlapping VALUE parameter
    (see :class:`~odxtools.parameters.nrcconstparameter.NrcConstParameter`).
    Without one, no specific value can be encoded at all and the bytes are
    left at zero — measured on ``somersault.pdx``, where encoding
    ``flips_not_done`` cannot choose a reason.
    """

    name = "nrc-const-without-value"

    spec = "ASAM MCD-2 D (ODX) 2.2, section 7.3.5.4, p. 79"

    def check(self, database: Database) -> Iterable[Finding]:
        for codec in database.odxlinks.objects():
            if not is_composite_codec(codec):
                continue
            spans = [(param, _bit_span(param)) for param in codec.parameters if param is not None]
            values = [(param, span)
                      for param, span in spans
                      if isinstance(param, ValueParameter) and span is not None]

            for param, span in spans:
                if not isinstance(param, NrcConstParameter):
                    continue
                if span is None:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.DEBUG,
                        object=codec,
                        message=(f"NRC-CONST '{param.short_name}' has no statically known "
                                 f"position and length and was not checked"),
                    )
                    continue
                start, end = span
                if not any(v_start < end and start < v_end for _, (v_start, v_end) in values):
                    yield Finding(
                        rule=self.name,
                        severity=Severity.WARNING,
                        object=codec,
                        message=(f"NRC-CONST '{param.short_name}' (bits {start}..{end - 1}) "
                                 f"is not overlapped by any VALUE parameter, so no "
                                 f"specific value can be chosen when encoding this "
                                 f"object; the bytes are left at zero"),
                    )
