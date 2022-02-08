# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import List, NamedTuple, Optional


class CompuRationalCoeffs(NamedTuple):
    numerators: List[float]
    denominators: Optional[List[float]] = None
