# SPDX-License-Identifier: MIT
"""Check whether Parameters of the same codec object occupy the same bits in a PDU."""
from collections.abc import Iterable, Iterator

from ..compositecodec import CompositeCodec
from ..database import Database
from ..parameters.parameter import Parameter
from .finding import Finding, Severity
from .rule import is_composite_codec


def _bit_span(param: Parameter) -> tuple[int, int] | None:
    """The bits ``param`` occupies, or ``None`` if that is not statically known.

    A parameter without a byte position follows whatever precedes it, and one
    without a static length is sized by its value, so neither can be placed
    without decoding an actual message. A parameter of zero bits occupies
    nothing and therefore cannot share bits with anything.
    """
    if param.byte_position is None:
        return None

    bit_length = param.get_static_bit_length()
    if not bit_length:
        return None

    start = param.byte_position * 8 + (param.bit_position or 0)
    return start, start + bit_length


def _place(codec: CompositeCodec) -> tuple[list[tuple[tuple[int, int], Parameter]], int]:
    """The parameters of ``codec`` which can be placed, and how many cannot."""
    placed: list[tuple[tuple[int, int], Parameter]] = []
    skipped = 0
    for param in codec.parameters:
        if param is None:
            # this can happen in non-strict mode
            skipped += 1
            continue
        span = _bit_span(param)
        if span is None:
            skipped += 1
        else:
            placed.append((span, param))
    return placed, skipped


def _overlaps(placed: list[tuple[tuple[int, int],
                                 Parameter]]) -> Iterator[tuple[Parameter, Parameter]]:
    for i, ((a_start, a_end), a) in enumerate(placed):
        for (b_start, b_end), b in placed[i + 1:]:
            if (a_start < b_end and b_start < a_end) or (b_start < a_end and a_start < b_end):
                yield a, b


class OverlappingParameters:
    """Two parameters of one codec object which cover the same bits.

    The specification does not forbid this: a value parameter routinely shares
    its bits with a CODED-CONST or NRC-CONST which discriminates on the same
    bytes, and real databases map one byte to several decodings on purpose.
    The findings are therefore informational, never errors.

    Only parameters whose position and length are both known from the database
    are compared; a codec whose layout depends on the data it carries is
    passed over, and saying so is reported at ``DEBUG`` so that a database
    with no findings can be told apart from one that could not be inspected.
    """

    name = "overlapping-parameters"

    #: This rule does not enforce a requirement of the standard, which permits
    #: overlapping parameters (see e.g. NRC-CONST, ASAM MCD-2 D (ODX) 2.2,
    #: section 7.3.5.4). It reports them for the reader's information.
    spec = ("informational; the standard permits overlaps "
            "(cf. NRC-CONST, ASAM MCD-2 D (ODX) 2.2, section 7.3.5.4, p. 79)")

    def check(self, database: Database) -> Iterable[Finding]:
        for codec in database.odxlinks.objects():
            if not is_composite_codec(codec):
                continue
            placed, skipped = _place(codec)

            if skipped:
                yield Finding(
                    rule=self.name,
                    severity=Severity.DEBUG,
                    object=codec,
                    message=(f"{skipped} of {skipped + len(placed)} parameters have no "
                             f"statically known position and length and were not compared"),
                )

            for a, b in _overlaps(placed):
                a_span = _bit_span(a)
                b_span = _bit_span(b)
                assert a_span is not None and b_span is not None
                yield Finding(
                    rule=self.name,
                    severity=Severity.INFO,
                    object=codec,
                    message=(f"parameters '{a.short_name}' (bits {a_span[0]}..{a_span[1] - 1}) "
                             f"and '{b.short_name}' (bits {b_span[0]}..{b_span[1] - 1}) "
                             f"share bits"),
                )
