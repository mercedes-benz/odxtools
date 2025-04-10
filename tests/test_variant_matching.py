# SPDX-License-Identifier: MIT
import json
from typing import Any

import pytest

from odxtools.basevariantpattern import BaseVariantPattern
from odxtools.database import Database
from odxtools.diaglayers.basevariant import BaseVariant
from odxtools.diaglayers.basevariantraw import BaseVariantRaw
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.diagservice import DiagService
from odxtools.ecuvariantpattern import EcuVariantPattern
from odxtools.exceptions import OdxError, odxrequire
from odxtools.matchingbasevariantparameter import MatchingBaseVariantParameter
from odxtools.matchingparameter import MatchingParameter
from odxtools.odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from odxtools.request import Request
from odxtools.response import Response, ResponseType
from odxtools.variantmatcher import VariantMatcher

doc_frags = (OdxDocFragment(doc_name="pytest", doc_type=DocType.CONTAINER),)

odxlinks = OdxLinkDatabase()


@pytest.fixture
def dummy_response(monkeypatch: pytest.MonkeyPatch) -> Response:
    resp = Response(
        odx_id=OdxLinkId(local_id="dummy_resp", doc_fragments=doc_frags),
        short_name="dummy_resp",
        response_type=ResponseType.POSITIVE,
    )
    odxlinks.update({resp.odx_id: resp})

    def decode(message: bytes) -> dict[str, Any]:
        msg_str = message.decode(encoding="utf-8")
        msg_dict = json.loads(msg_str)
        assert isinstance(msg_dict, dict)
        return msg_dict

    monkeypatch.setattr(resp, "decode", decode)
    return resp


@pytest.fixture()
def bv_ident_service(monkeypatch: pytest.MonkeyPatch, dummy_response: Response) -> DiagService:
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="identService", doc_fragments=doc_frags),
        short_name="identService",
        request_ref=OdxLinkRef.from_id(dummy_req.odx_id),
        pos_response_refs=[OdxLinkRef.from_id(dummy_response.odx_id)],
    )

    def encode_request() -> bytes:
        return b"\xff\xee\xdd"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture()
def ev_ident_service(monkeypatch: pytest.MonkeyPatch, dummy_response: Response) -> DiagService:
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="identService", doc_fragments=doc_frags),
        short_name="identService",
        request_ref=OdxLinkRef.from_id(dummy_req.odx_id),
        pos_response_refs=[OdxLinkRef.from_id(dummy_response.odx_id)],
    )

    def encode_request() -> bytes:
        return b"\x22\x10\x00"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def ev_supplier_service(monkeypatch: pytest.MonkeyPatch, dummy_response: Response) -> DiagService:
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="supplierService", doc_fragments=doc_frags),
        short_name="supplierService",
        request_ref=OdxLinkRef.from_id(dummy_req.odx_id),
        pos_response_refs=[OdxLinkRef.from_id(dummy_response.odx_id)],
    )

    def encode_request() -> bytes:
        return b"\x22\x20\x00"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def bv_supplier_service(monkeypatch: pytest.MonkeyPatch, dummy_response: Response) -> DiagService:
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="supplierService", doc_fragments=doc_frags),
        short_name="supplierService",
        request_ref=OdxLinkRef.from_id(dummy_req.odx_id),
        pos_response_refs=[OdxLinkRef.from_id(dummy_response.odx_id)],
    )

    def encode_request() -> bytes:
        return b"\xcc\xbb\xaa"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def bv2_supplier_service(monkeypatch: pytest.MonkeyPatch, dummy_response: Response) -> DiagService:
    bv2_req = Request(
        odx_id=OdxLinkId(local_id="bv2_req", doc_fragments=doc_frags),
        short_name="bv2_req",
    )
    odxlinks.update({bv2_req.odx_id: bv2_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="bv2.supplierService", doc_fragments=doc_frags),
        short_name="supplierService",
        request_ref=OdxLinkRef.from_id(bv2_req.odx_id),
        pos_response_refs=[OdxLinkRef.from_id(dummy_response.odx_id)],
    )

    def encode_request() -> bytes:
        return b"\xcc\xbb\xab"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def base_variant_pattern1() -> BaseVariantPattern:
    return BaseVariantPattern(matching_base_variant_parameters=[
        MatchingBaseVariantParameter(
            diag_comm_snref="identService",
            expected_value="1234",
            out_param_if_snref="id",
        ),
        MatchingBaseVariantParameter(
            diag_comm_snref="supplierService",
            use_physical_addressing_raw=False,
            expected_value="OEM",
            out_param_if_snpathref="info.type",
        ),
    ])


@pytest.fixture
def base_variant_pattern2() -> BaseVariantPattern:
    return BaseVariantPattern(matching_base_variant_parameters=[
        MatchingBaseVariantParameter(
            diag_comm_snref="identService",
            expected_value="1234",
            out_param_if_snref="id",
        ),
        MatchingBaseVariantParameter(
            diag_comm_snref="supplierService",
            use_physical_addressing_raw=True,
            expected_value="tier1",
            out_param_if_snpathref="info.type",
        ),
    ])


@pytest.fixture
def base_variant_pattern3() -> BaseVariantPattern:
    return BaseVariantPattern(matching_base_variant_parameters=[
        MatchingBaseVariantParameter(
            diag_comm_snref="supplierService",
            use_physical_addressing_raw=False,
            expected_value="tier5",
            out_param_if_snpathref="info.type",
        )
    ])


@pytest.fixture
def ecu_variant_pattern1() -> EcuVariantPattern:
    return EcuVariantPattern(matching_parameters=[
        MatchingParameter(
            diag_comm_snref="identService",
            expected_value="1000",
            out_param_if_snref="id",
        ),
        MatchingParameter(
            diag_comm_snref="supplierService",
            expected_value="supplier_A",
            out_param_if_snpathref="name.english",
        ),
    ])


@pytest.fixture
def ecu_variant_pattern2() -> EcuVariantPattern:
    return EcuVariantPattern(matching_parameters=[
        MatchingParameter(
            diag_comm_snref="identService",
            expected_value="2000",
            out_param_if_snref="id",
        ),
        MatchingParameter(
            diag_comm_snref="supplierService",
            expected_value="supplier_B",
            out_param_if_snpathref="name.english",
        ),
    ])


@pytest.fixture
def ecu_variant_pattern3() -> EcuVariantPattern:
    return EcuVariantPattern(matching_parameters=[
        MatchingParameter(
            diag_comm_snref="supplierService",
            expected_value="supplier_C",
            out_param_if_snpathref="name.english",
        )
    ])


@pytest.fixture
def base_variant_1(
    bv_ident_service: DiagService,
    bv_supplier_service: DiagService,
    base_variant_pattern1: BaseVariantPattern,
) -> BaseVariant:
    raw_layer = BaseVariantRaw(
        variant_type=DiagLayerType.BASE_VARIANT,
        odx_id=OdxLinkId(local_id="base_variant1", doc_fragments=doc_frags),
        short_name="base_variant1",
        diag_comms_raw=[bv_ident_service, bv_supplier_service],
        base_variant_pattern=base_variant_pattern1,
    )
    result = BaseVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def base_variant_2(
    bv_ident_service: DiagService,
    bv2_supplier_service: DiagService,
    base_variant_pattern2: BaseVariantPattern,
) -> BaseVariant:
    raw_layer = BaseVariantRaw(
        variant_type=DiagLayerType.BASE_VARIANT,
        odx_id=OdxLinkId(local_id="base_variant2", doc_fragments=doc_frags),
        short_name="base_variant2",
        diag_comms_raw=[bv_ident_service, bv2_supplier_service],
        base_variant_pattern=base_variant_pattern2,
    )
    result = BaseVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def base_variant_3(
    bv_ident_service: DiagService,
    bv_supplier_service: DiagService,
    base_variant_pattern1: BaseVariantPattern,
    base_variant_pattern3: BaseVariantPattern,
) -> BaseVariant:
    raw_layer = BaseVariantRaw(
        variant_type=DiagLayerType.BASE_VARIANT,
        odx_id=OdxLinkId(local_id="base_variant3", doc_fragments=doc_frags),
        short_name="base_variant3",
        diag_comms_raw=[bv_ident_service, bv_supplier_service],
        base_variant_pattern=base_variant_pattern3,
    )
    result = BaseVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def base_variants(base_variant_1: BaseVariant, base_variant_2: BaseVariant,
                  base_variant_3: BaseVariant) -> list[BaseVariant]:
    return [base_variant_1, base_variant_2, base_variant_3]


@pytest.fixture
def ecu_variant_1(
    ev_ident_service: DiagService,
    ev_supplier_service: DiagService,
    ecu_variant_pattern1: EcuVariantPattern,
) -> EcuVariant:
    raw_layer = EcuVariantRaw(
        variant_type=DiagLayerType.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant1", doc_fragments=doc_frags),
        short_name="ecu_variant1",
        diag_comms_raw=[ev_ident_service, ev_supplier_service],
        ecu_variant_patterns=[ecu_variant_pattern1],
    )
    result = EcuVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def ecu_variant_2(
    ev_ident_service: DiagService,
    ev_supplier_service: DiagService,
    ecu_variant_pattern2: EcuVariantPattern,
) -> EcuVariant:
    raw_layer = EcuVariantRaw(
        variant_type=DiagLayerType.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant2", doc_fragments=doc_frags),
        short_name="ecu_variant2",
        diag_comms_raw=[ev_ident_service, ev_supplier_service],
        ecu_variant_patterns=[ecu_variant_pattern2],
    )
    result = EcuVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def ecu_variant_3(
    ev_ident_service: DiagService,
    ev_supplier_service: DiagService,
    ecu_variant_pattern1: EcuVariantPattern,
    ecu_variant_pattern3: EcuVariantPattern,
) -> EcuVariant:
    raw_layer = EcuVariantRaw(
        variant_type=DiagLayerType.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant3", doc_fragments=doc_frags),
        short_name="ecu_variant3",
        diag_comms_raw=[ev_ident_service, ev_supplier_service],
        ecu_variant_patterns=[ecu_variant_pattern1, ecu_variant_pattern3],
    )
    result = EcuVariant(diag_layer_raw=raw_layer)
    odxlinks.update(result._build_odxlinks())
    db = Database()
    result._resolve_odxlinks(odxlinks)
    result._finalize_init(db, odxlinks)
    return result


@pytest.fixture
def ecu_variants(ecu_variant_1: EcuVariant, ecu_variant_2: EcuVariant,
                 ecu_variant_3: EcuVariant) -> list[EcuVariant]:
    return [ecu_variant_1, ecu_variant_2, ecu_variant_3]


def as_bytes(dikt: dict[str, Any]) -> bytes:
    return bytes(json.dumps(dikt), "utf-8")


@pytest.mark.parametrize("use_cache", [True, False])
# the req_resp_mapping maps request to responses for the ecu-under-test
@pytest.mark.parametrize(
    "req_resp_mapping, expected_variant",
    [
        # test if full match of matching parameters is accepted
        (
            {
                b"\xff\xee\xdd": as_bytes({"id": 1234}),
                b"\xcc\xbb\xaa": as_bytes({"info": {
                    "type": "OEM"
                }}),
            },
            "base_variant1",
        ),
        (
            {
                b"\xff\xee\xdd": as_bytes({"id": 1234}),
                b"\xcc\xbb\xab": as_bytes({"info": {
                    "type": "tier1"
                }}),
            },
            "base_variant2",
        ),
    ],
)
def test_base_variant_matching(
    base_variants: list[BaseVariant],
    use_cache: bool,
    req_resp_mapping: dict[bytes, bytes],
    expected_variant: str,
) -> None:

    matcher = VariantMatcher(
        variant_candidates=base_variants,
        use_cache=use_cache,
    )
    has_physical_addressing = False
    has_functional_addressing = False
    for use_physical_addressing, req in matcher.request_loop():
        has_physical_addressing = has_physical_addressing or use_physical_addressing
        has_functional_addressing = has_functional_addressing or not use_physical_addressing
        resp = req_resp_mapping.get(req)
        if resp is not None:
            matcher.evaluate(resp)
        else:
            # we don't know about the request. report back an negative response
            matcher.evaluate(b'{ "SID": 127 }')

    assert has_physical_addressing and has_functional_addressing
    assert matcher.has_match()
    assert odxrequire(matcher.matching_variant).short_name == expected_variant


@pytest.mark.parametrize("use_cache", [True, False])
# the req_resp_mapping maps request to responses for the ecu-under-test
@pytest.mark.parametrize(
    "req_resp_mapping, expected_variant",
    [
        # test if full match of matching parameters is accepted
        (
            {
                b"\x22\x10\x00": as_bytes({"id": 2000}),
                b"\x22\x20\x00": as_bytes({"name": {
                    "english": "supplier_B"
                }}),
            },
            "ecu_variant2",
        ),
        # test if partial match of matching parameters is rejected
        (
            {
                b"\x22\x10\x00": as_bytes({"id": 2000}),
                b"\x22\x20\x00": as_bytes({"name": {
                    "english": "supplier_C"
                }}),
            },
            "ecu_variant3",
        ),
        # test if first full match is preferred over second match
        (
            {
                b"\x22\x10\x00": as_bytes({"id": 1000}),
                b"\x22\x20\x00": as_bytes({"name": {
                    "english": "supplier_A"
                }}),
            },
            "ecu_variant1",
        ),
    ],
)
def test_ecu_variant_matching(
    ecu_variants: list[EcuVariant],
    use_cache: bool,
    req_resp_mapping: dict[bytes, bytes],
    expected_variant: str,
) -> None:
    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )
    for use_physical_addressing, req in matcher.request_loop():
        assert use_physical_addressing
        resp = req_resp_mapping[req]
        matcher.evaluate(resp)
    assert matcher.has_match()
    assert odxrequire(matcher.matching_variant).short_name == expected_variant


@pytest.mark.parametrize("use_cache", [True, False])
def test_no_match(ecu_variants: list[EcuVariant], use_cache: bool) -> None:
    # stores the responses for each request for the ecu-under-test
    req_resp_mapping = {
        b"\x22\x10\x00": as_bytes({"id": 1000}),
        b"\x22\x20\x00": as_bytes({"name": {
            "english": "supplier_D"
        }}),
    }

    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )
    for use_physical_addressing, req in matcher.request_loop():
        assert use_physical_addressing
        resp = req_resp_mapping[req]
        matcher.evaluate(resp)
    assert not matcher.has_match()
    assert matcher.matching_variant is None


@pytest.mark.parametrize("use_cache", [True, False])
# test if pending matchers reject the has_match() or active variant query
def test_no_request_loop(ecu_variants: list[EcuVariant], use_cache: bool) -> None:
    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )
    with pytest.raises(RuntimeError):
        matcher.has_match()
    assert matcher.matching_variant is None


@pytest.mark.parametrize("use_cache", [True, False])
# test if runs of the request loop without calling `evaluate(...)` are rejected
def test_request_loop_misuse(ecu_variants: list[EcuVariant], use_cache: bool) -> None:
    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )
    with pytest.raises(RuntimeError):
        for _, _ in matcher.request_loop():
            pass


@pytest.mark.parametrize("use_cache", [True, False])
# test if request loop is idempotent, i.e., the matching is the same regardless of how often the request loop is run
def test_request_loop_idempotency(ecu_variants: list[EcuVariant], use_cache: bool) -> None:
    req_resp_mapping = {
        b"\x22\x10\x00": as_bytes({"id": 2000}),
        b"\x22\x20\x00": as_bytes({"name": {
            "english": "supplier_B"
        }}),
    }

    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )

    for _, req in matcher.request_loop():
        resp = req_resp_mapping[req]
        matcher.evaluate(resp)
    assert matcher.has_match()
    assert odxrequire(matcher.matching_variant).short_name == "ecu_variant2"

    # second run with arbitrary input
    for _, _ in matcher.request_loop():
        matcher.evaluate(b"")

    # idempotency criterion
    assert matcher.has_match()
    assert odxrequire(matcher.matching_variant).short_name == "ecu_variant2"


@pytest.mark.parametrize("use_cache", [True, False])
def test_unresolvable_snpathref(ecu_variants: list[EcuVariant], use_cache: bool) -> None:
    # stores the responses for each request for the ecu-under-test
    req_resp_mapping = {
        b"\x22\x10\x00": as_bytes({"id": 1000}),
        # the snpathref cannot be resolved, because name is not a struct
        b"\x22\x20\x00": as_bytes({"name": "supplier_C"}),
    }

    matcher = VariantMatcher(
        variant_candidates=ecu_variants,
        use_cache=use_cache,
    )

    with pytest.raises(OdxError):
        for _, req in matcher.request_loop():
            resp = req_resp_mapping[req]
            matcher.evaluate(resp)
