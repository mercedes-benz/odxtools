# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .dopbase import DopBase


@dataclass(kw_only=True)
class ComplexDop(DopBase):
    """Base class for all complex data object properties.

    Complex DOPs are e.g., structures, fields and environment datas.
    """
    pass
