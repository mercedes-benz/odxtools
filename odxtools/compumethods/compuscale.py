# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH


from typing import NamedTuple, Optional, Union

from .compurationalcoeffs import CompuRationalCoeffs
from .limit import Limit


class CompuScale(NamedTuple):
    """A COMPU-SCALE represents one value range of a COMPU-METHOD.

    Example:

    For a TEXTTABLE compu method a compu scale within COMPU-INTERNAL-TO-PHYS
    can be defined with
    ```
    scale = CompuScale(
        short_label="example_label", # optional: provide a label
        description="<p>fancy description</p>", # optional: provide a description
        lower_limit=Limit(0), # required: lower limit
        upper_limit=Limit(3), # required: upper limit
        compu_inverse_value=2, # required iff lower_limit != upper_limit
        compu_const="true", # required: physical value to be shown to the user
    )
    ```

    Almost all attributes are optional but there are compu-method-specific restrictions.
    E.g., lower_limit must always be defined unless the COMPU-METHOD is of CATEGORY LINEAR or RAT-FUNC.
    Either `compu_const` or `compu_rational_coeffs` must be defined but never both.
    """
    short_label: Optional[str] = None
    description: Optional[str] = None
    lower_limit: Optional[Limit] = None
    upper_limit: Optional[Limit] = None
    compu_inverse_value: Optional[Union[float, str, bytearray]] = None
    compu_const: Optional[Union[float, str]] = None
    compu_rational_coeffs: Optional[CompuRationalCoeffs] = None
