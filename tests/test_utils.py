# SPDX-License-Identifier: MIT
# Copyright (c) 2023 MBition GmbH

import pytest

from odxtools.utils import is_short_name, is_short_name_path


@pytest.mark.parametrize(
    "val, expected",
    [
        ("abcXYZ", True),
        ("_aA09_", True),
        ("abcde+", False),
        ("+abcde", False),
        ("ab++cd", False),
    ],
)
def test_is_short_name(val: str, expected: bool):
    assert is_short_name(val) == expected


@pytest.mark.parametrize(
    "val, expected",
    [
        ("abcdefghi", True),
        ("abc.def.g", True),
        (".abcdefgh", False),
        ("abc..defg", False),
        ("abc.defg.", False),
    ],
)
def test_is_short_name_path(val: str, expected: bool):
    assert is_short_name_path(val) == expected
