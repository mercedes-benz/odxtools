# SPDX-License-Identifier: MIT
# Copyright (c) 2023 MBition GmbH

import json
from typing import Union

import pytest

from odxtools.diaglayer import DiagLayer
from odxtools.diaglayertype import DIAG_LAYER_TYPE
from odxtools.ecu_variant_matching import EcuVariantMatcher
from odxtools.ecu_variant_patterns import EcuVariantPattern, MatchingParameter
from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from odxtools.service import DiagService
from odxtools.structures import Request, Response

doc_frags = [OdxDocFragment("pytest", "WinneThePoh")]

odxlinks = OdxLinkDatabase()


@pytest.fixture
def dummy_response(monkeypatch):
    resp = Response(
        odx_id=OdxLinkId(local_id="dummy_resp", doc_fragments=doc_frags),
        short_name="dummy_resp",
        parameters=None,
    )
    odxlinks.update({resp.odx_id: resp})

    def decode(message: Union[bytes, bytearray]):
        msg_str = message.decode(encoding="utf-8")
        msg_dict = json.loads(msg_str)
        return msg_dict

    monkeypatch.setattr(resp, "decode", decode)
    return resp


@pytest.fixture()
def identificationService(monkeypatch, dummy_response):
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
        parameters=[],
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="identService", doc_fragments=doc_frags),
        short_name="identService",
        request=dummy_req,
        positive_responses=[dummy_response],
        negative_responses=[],
    )

    def encode_request():
        return b"\x22\x10\x00"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def supplierService(monkeypatch, dummy_response):
    dummy_req = Request(
        odx_id=OdxLinkId(local_id="dummy_req", doc_fragments=doc_frags),
        short_name="dummy_req",
        parameters=[],
    )
    odxlinks.update({dummy_req.odx_id: dummy_req})

    diagService = DiagService(
        odx_id=OdxLinkId(local_id="supplierService", doc_fragments=doc_frags),
        short_name="supplierService",
        request=dummy_req,
        positive_responses=[dummy_response],
        negative_responses=[],
    )

    def encode_request():
        return b"\x22\x20\x00"

    monkeypatch.setattr(diagService, "encode_request", encode_request)
    return diagService


@pytest.fixture
def ecu_variant_pattern1():
    return EcuVariantPattern(
        matching_parameters=[
            MatchingParameter(
                diag_comm_snref="identService",
                expected_value="1000",
                out_param_if_snref="id",
            ),
            MatchingParameter(
                diag_comm_snref="supplierService",
                expected_value="supplier_A",
                out_param_if_snref="name",
            ),
        ]
    )


@pytest.fixture
def ecu_variant_pattern2():
    return EcuVariantPattern(
        matching_parameters=[
            MatchingParameter(
                diag_comm_snref="identService",
                expected_value="2000",
                out_param_if_snref="id",
            ),
            MatchingParameter(
                diag_comm_snref="supplierService",
                expected_value="supplier_B",
                out_param_if_snref="name",
            ),
        ]
    )


@pytest.fixture
def ecu_variant_pattern3():
    return EcuVariantPattern(
        matching_parameters=[
            MatchingParameter(
                diag_comm_snref="supplierService",
                expected_value="supplier_C",
                out_param_if_snref="name",
            )
        ]
    )


@pytest.fixture
def ecu_variant_1(identificationService, supplierService, ecu_variant_pattern1):
    return DiagLayer(
        variant_type=DIAG_LAYER_TYPE.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant1", doc_fragments=doc_frags),
        short_name="ecu_variant1",
        services=[identificationService, supplierService],
        ecu_variant_patterns=[ecu_variant_pattern1],
        odxlinks=odxlinks,
    )


@pytest.fixture
def ecu_variant_2(identificationService, supplierService, ecu_variant_pattern2):
    return DiagLayer(
        variant_type=DIAG_LAYER_TYPE.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant2", doc_fragments=doc_frags),
        short_name="ecu_variant2",
        services=[identificationService, supplierService],
        ecu_variant_patterns=[ecu_variant_pattern2],
        odxlinks=odxlinks,
    )


@pytest.fixture
def ecu_variant_3(
    identificationService, supplierService, ecu_variant_pattern1, ecu_variant_pattern3
):
    return DiagLayer(
        variant_type=DIAG_LAYER_TYPE.ECU_VARIANT,
        odx_id=OdxLinkId(local_id="ecu_variant3", doc_fragments=doc_frags),
        short_name="ecu_variant3",
        services=[identificationService, supplierService],
        ecu_variant_patterns=[ecu_variant_pattern1, ecu_variant_pattern3],
        odxlinks=odxlinks,
    )


def as_bytes(dikt):
    return bytes(json.dumps(dikt), "utf-8")


@pytest.mark.parametrize("use_cache", [True, False])
# the req_resp_mapping maps request to responses for the ecu-under-test
@pytest.mark.parametrize(
    "req_resp_mapping, expected_variant",
    [
        # test if full match of matching parameters is accepted
        (
            {
                b"\x22\x10\00": as_bytes({"id": 2000}),
                b"\x22\x20\00": as_bytes({"name": "supplier_B"}),
            },
            "ecu_variant2",
        ),
        # test if partial match of matching parameters is rejected
        (
            {
                b"\x22\x10\00": as_bytes({"id": 2000}),
                b"\x22\x20\00": as_bytes({"name": "supplier_C"}),
            },
            "ecu_variant3",
        ),
        # test if first full match is preferred over second match
        (
            {
                b"\x22\x10\00": as_bytes({"id": 1000}),
                b"\x22\x20\00": as_bytes({"name": "supplier_A"}),
            },
            "ecu_variant1",
        ),
    ],
)
def test_ecu_variant_matching(
    ecu_variant_1,
    ecu_variant_2,
    ecu_variant_3,
    use_cache,
    req_resp_mapping,
    expected_variant,
):
    matcher = EcuVariantMatcher(
        ecu_variant_candidates=[ecu_variant_1, ecu_variant_2, ecu_variant_3],
        use_cache=use_cache,
    )
    for req in matcher.request_loop():
        resp = req_resp_mapping[req]
        matcher.evaluate(resp)
    assert matcher.has_match()
    assert matcher.get_active_ecu_variant().short_name == expected_variant


@pytest.mark.parametrize("use_cache", [True, False])
def test_no_match(ecu_variant_1, ecu_variant_2, ecu_variant_3, use_cache):
    # stores the responses for each request for the ecu-under-test
    req_resp_mapping = {
        b"\x22\x10\00": as_bytes({"id": 1000}),
        b"\x22\x20\00": as_bytes({"name": "supplier_D"}),
    }

    matcher = EcuVariantMatcher(
        ecu_variant_candidates=[ecu_variant_1, ecu_variant_2, ecu_variant_3],
        use_cache=use_cache,
    )
    for req in matcher.request_loop():
        resp = req_resp_mapping[req]
        matcher.evaluate(resp)
    assert not matcher.has_match()
    with pytest.raises(AssertionError):
        matcher.get_active_ecu_variant()


@pytest.mark.parametrize("use_cache", [True, False])
# test if pending matchers reject the has_match() or active variant query
def test_no_request_loop(ecu_variant_1, ecu_variant_2, ecu_variant_3, use_cache):
    matcher = EcuVariantMatcher(
        ecu_variant_candidates=[ecu_variant_1, ecu_variant_2, ecu_variant_3],
        use_cache=use_cache,
    )
    with pytest.raises(RuntimeError):
        matcher.has_match()
    with pytest.raises(RuntimeError):
        matcher.get_active_ecu_variant()


@pytest.mark.parametrize("use_cache", [True, False])
# test if runs of the request loop without calling `evaluate(...)` are rejected
def test_request_loop_misuse(ecu_variant_1, ecu_variant_2, ecu_variant_3, use_cache):
    matcher = EcuVariantMatcher(
        ecu_variant_candidates=[ecu_variant_1, ecu_variant_2, ecu_variant_3],
        use_cache=use_cache,
    )
    with pytest.raises(RuntimeError):
        for _ in matcher.request_loop():
            pass


@pytest.mark.parametrize("use_cache", [True, False])
# test if request loop is idempotent, i.e., the matching is the same regardless of how often the request loop is run
def test_request_loop_idempotency(
    ecu_variant_1, ecu_variant_2, ecu_variant_3, use_cache
):
    matcher = EcuVariantMatcher(
        ecu_variant_candidates=[ecu_variant_1, ecu_variant_2, ecu_variant_3],
        use_cache=use_cache,
    )
    with pytest.raises(RuntimeError):
        for _ in matcher.request_loop():
            pass
