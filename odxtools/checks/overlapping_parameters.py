# SPDX-License-Identifier: MIT
"""Check that Parameters of the same codec object do not occupy the same bits in a PDU."""
from collections.abc import Iterable, Iterator
from itertools import chain

from ..compositecodec import CompositeCodec
from ..database import Database
from ..diagservice import DiagService
from ..parameters.parameter import Parameter
from .finding import Finding, Severity


def _bit_span(param: Parameter) -> tuple[int, int] | None:
    """The bits ``param`` occupies, or ``None`` if that is not statically known.

    A parameter without a byte position follows whatever precedes it, and one
    without a static length is sized by its value, so neither can be placed
    without decoding an actual message.
    """
    if param.byte_position is None:
        return None

    bit_length = param.get_static_bit_length()
    if bit_length is None:
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


def _overlaps(placed: list[tuple[tuple[int, int], Parameter]]
              ) -> Iterator[tuple[Parameter, Parameter]]:
    for i, ((a_start, a_end), a) in enumerate(placed):
        for (b_start, b_end), b in placed[i + 1:]:
            if a_start < b_end and b_start < a_end:
                yield a, b


class OverlappingParameters:
    """Two parameters of one structure which cover the same bits.

    Only parameters whose position and length are both known from the database
    are considered, so a structure whose layout depends on the data it carries
    is passed over rather than guessed at. Passing one over is reported at
    ``DEBUG``, so that a database which reports nothing can be told apart from
    one which could not be inspected.
    """

    name = "overlapping-parameters"

    def check(self, database: Database) -> Iterable[Finding]:
        for codec, location in _codecs(database):
            placed, skipped = _place(codec)

            if skipped:
                yield Finding(
                    rule=self.name,
                    severity=Severity.DEBUG,
                    location=location,
                    message=(f"{skipped} of {skipped + len(placed)} parameters have no "
                             f"statically known position and length and were not compared"),
                )

            for a, b in _overlaps(placed):
                a_span = _bit_span(a)
                b_span = _bit_span(b)
                assert a_span is not None and b_span is not None
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    location=location,
                    message=(f"parameters '{a.short_name}' (bits {a_span[0]}..{a_span[1] - 1}) "
                             f"and '{b.short_name}' (bits {b_span[0]}..{b_span[1] - 1}) "
                             f"overlap"),
                )


def _codecs(database: Database) -> Iterator[tuple[CompositeCodec, tuple[str, ...]]]:
    """Find every parameter-carrying object reachable from ``database``.

    Requests, responses and structures all carry parameters without sharing a
    base class, so they are identified through the CompositeCodec protocol.
    """
    seen: set[int] = set()

    for diag_layer in database.diag_layers:
        layer_name = diag_layer.short_name

        for diag_comm in diag_layer.diag_comms:
            if not isinstance(diag_comm, DiagService):
                continue
            for codec_obj in chain([diag_comm.request], diag_comm.positive_responses,
                                   diag_comm.negative_responses):
                if not isinstance(codec_obj, CompositeCodec) or id(codec_obj) in seen:
                    continue
                seen.add(id(codec_obj))
                yield codec_obj, (layer_name, diag_comm.short_name, codec_obj.short_name)

        ddd_spec = diag_layer.diag_data_dictionary_spec
        for structure in chain(ddd_spec.structures, ddd_spec.env_datas):
            if id(structure) in seen:
                continue
            seen.add(id(structure))
            yield structure, (layer_name, structure.short_name)
