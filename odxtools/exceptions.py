# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

class OdxError(Exception):
    """Any error that happens during interacting with diagnostic objects."""

class EncodeError(OdxError):
    """Encoding of a message to raw data failed."""

class DecodeError(OdxError):
    """Decoding raw data failed."""

class OdxWarning(Warning):
    """Any warning that happens during interacting with diagnostic objects."""
