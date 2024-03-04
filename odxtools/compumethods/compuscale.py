# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from ..utils import create_description_from_et
from .compurationalcoeffs import CompuRationalCoeffs
from .limit import Limit


@dataclass
class CompuScale:
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
        compu_inverse_value=2, # required if lower_limit != upper_limit
        compu_const="true", # required: physical value to be shown to the user
    )
    ```

    Almost all attributes are optional but there are compu-method-specific restrictions.
    E.g., lower_limit must always be defined unless the COMPU-METHOD is of CATEGORY LINEAR or RAT-FUNC.
    Either `compu_const` or `compu_rational_coeffs` must be defined but never both.
    """

    short_label: Optional[str]
    description: Optional[str]
    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    compu_inverse_value: Optional[AtomicOdxType]
    compu_const: Optional[AtomicOdxType]
    compu_rational_coeffs: Optional[CompuRationalCoeffs]

    # the following two attributes are not specified for COMPU-SCALE
    # tags in the XML, but they are required to do anything useful
    # with it.
    internal_type: DataType
    physical_type: DataType

    @staticmethod
    def compuscale_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                           internal_type: DataType, physical_type: DataType) -> "CompuScale":
        short_label = et_element.findtext("SHORT-LABEL")
        description = create_description_from_et(et_element.find("DESC"))

        lower_limit = Limit.limit_from_et(
            et_element.find("LOWER-LIMIT"), doc_frags, value_type=internal_type)
        upper_limit = Limit.limit_from_et(
            et_element.find("UPPER-LIMIT"), doc_frags, value_type=internal_type)

        compu_inverse_value = internal_type.create_from_et(et_element.find("COMPU-INVERSE-VALUE"))
        compu_const = physical_type.create_from_et(et_element.find("COMPU-CONST"))

        compu_rational_coeffs: Optional[CompuRationalCoeffs] = None
        if (crc_elem := et_element.find("COMPU-RATIONAL-COEFFS")) is not None:
            compu_rational_coeffs = CompuRationalCoeffs.from_et(crc_elem, doc_frags)

        return CompuScale(
            short_label=short_label,
            description=description,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            compu_inverse_value=compu_inverse_value,
            compu_const=compu_const,
            compu_rational_coeffs=compu_rational_coeffs,
            internal_type=internal_type,
            physical_type=physical_type)

    def applies(self, internal_value: AtomicOdxType) -> bool:

        if self.lower_limit is None and self.upper_limit is None:
            # Everything is allowed: No limits have been specified
            return True
        elif self.upper_limit is None:
            # no upper limit has been specified. the spec says that
            # the value specified by the lower limit is the only one
            # which is allowed (cf section 7.3.6.6.1)
            assert self.lower_limit is not None

            return internal_value == self.lower_limit.value
        elif self.lower_limit is None:
            # only the upper limit has been specified. the spec is
            # ambiguous: it only says that if no upper limit is
            # defined, the lower limit shall also be used as the upper
            # limit and a closed interval type ought to be assumed,
            # but it does not say what happens if the lower limit is
            # not defined (which is allowed by the XSD). We thus
            # assume that if only the upper limit is defined, is
            # treated the same way as if only the lower limit is
            # specified.
            assert self.upper_limit is not None

            return internal_value == self.upper_limit.value

        return self.lower_limit.complies_to_lower(internal_value) and \
            self.upper_limit.complies_to_upper(internal_value)
