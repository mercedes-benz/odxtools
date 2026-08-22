# SPDX-License-Identifier: MIT
"""Parameters of the same object which occupy the same bits."""
from collections.abc import Iterable, Iterator

from ..compositecodec import CompositeCodec
from ..database import Database
from ..parameters.parameter import Parameter
from . import Finding, Severity


def _bit_span(param: Parameter) -> tuple[int, int] | None:
    """The bits ``param`` occupies, or ``None`` if that is not statically known.

    A parameter without a byte position follows whatever precedes it, and one
    without a static length is sized by its value, so neither can be placed
    without decoding an actual message.
    """
    if param.byte_position is None:
        return None

    try:
        bit_length = param.get_static_bit_length()
    except Exception:
        # The length of a parameter can depend on objects which a
        # non-conforming database left unresolved, and a check must not fail
        # on the very files it exists to inspect. Such a parameter cannot be
        # placed, which is the same situation as one without a static length.
        return None
    if bit_length is None:
        return None

    start = param.byte_position * 8 + (param.bit_position or 0)
    return start, start + bit_length


def _overlaps_in(codec: CompositeCodec) -> Iterator[tuple[Parameter, Parameter]]:
    placed: list[tuple[tuple[int, int], Parameter]] = []
    for param in codec.parameters:
        span = _bit_span(param)
        if span is not None:
            placed.append((span, param))

    for i, ((a_start, a_end), a) in enumerate(placed):
        for (b_start, b_end), b in placed[i + 1:]:
            if a_start < b_end and b_start < a_end:
                yield a, b


class OverlappingParameters:
    """Two parameters of one structure which cover the same bits.

    Only parameters whose position and length are both known from the database
    are considered, so a structure whose layout depends on the data it carries
    is passed over rather than guessed at.
    """

    name = "overlapping-parameters"

    def check(self, database: Database) -> Iterable[Finding]:
        for codec, location in _codecs(database):
            for a, b in _overlaps_in(codec):
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
    """Every parameter-carrying object reachable from ``database``.

    Requests, responses and structures all carry parameters without sharing a
    base class, so they are identified through the CompositeCodec protocol.
    """
    seen: set[int] = set()

    for diag_layer in database.diag_layers:
        layer_name = diag_layer.short_name

        for service in getattr(diag_layer, "services", []):
            for attribute in ("request", "positive_responses", "negative_responses"):
                value = getattr(service, attribute, None)
                candidates = value if isinstance(value, (list, tuple)) else [value]
                for candidate in candidates:
                    if not isinstance(candidate, CompositeCodec) or id(candidate) in seen:
                        continue
                    seen.add(id(candidate))
                    yield candidate, (layer_name, service.short_name, candidate.short_name)

        ddd_spec = getattr(diag_layer, "diag_data_dictionary_spec", None)
        for structure in getattr(ddd_spec, "structures", []):
            if id(structure) in seen:
                continue
            seen.add(id(structure))
            yield structure, (layer_name, structure.short_name)
