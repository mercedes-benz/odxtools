# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from ..description import Description
from ..odxlink import OdxDocFragment
from ..odxtypes import AtomicOdxType, DataType
from .compuconst import CompuConst
from .compuinversevalue import CompuInverseValue
from .compurationalcoeffs import CompuRationalCoeffs
from .limit import Limit


@dataclass
class CompuScale:
    """A COMPU-SCALE represents one value range of a COMPU-METHOD.
    """

    short_label: Optional[str]
    description: Optional[Description]
    lower_limit: Optional[Limit]
    upper_limit: Optional[Limit]
    compu_inverse_value: Optional[CompuInverseValue]
    compu_const: Optional[CompuConst]
    compu_rational_coeffs: Optional[CompuRationalCoeffs]

    # the following two attributes are not specified for COMPU-SCALE
    # tags in the XML, but they are required to do anything useful
    # with compu scales: The domain type is the input set of the
    # function associated with the compu scale object, whilst the
    # range type represents the output set. IOW, for scales contained
    # by the internal-to-physical mapping function, the domain type is
    # the internal and the range type is the physical type of the
    # compu method. (Vice versa for scales specified by the
    # physical-to-internal mapping function.)
    domain_type: DataType
    range_type: DataType

    @staticmethod
    def compuscale_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                           domain_type: DataType, range_type: DataType) -> "CompuScale":
        short_label = et_element.findtext("SHORT-LABEL")
        description = Description.from_et(et_element.find("DESC"), doc_frags)

        lower_limit = Limit.limit_from_et(
            et_element.find("LOWER-LIMIT"), doc_frags, value_type=domain_type)
        upper_limit = Limit.limit_from_et(
            et_element.find("UPPER-LIMIT"), doc_frags, value_type=domain_type)

        compu_inverse_value = None
        if (cive := et_element.find("COMPU-INVERSE-VALUE")) is not None:
            compu_inverse_value = CompuInverseValue.compuvalue_from_et(cive, data_type=domain_type)

        compu_const = None
        if (cce := et_element.find("COMPU-CONST")) is not None:
            compu_const = CompuConst.compuvalue_from_et(cce, data_type=range_type)

        compu_rational_coeffs: Optional[CompuRationalCoeffs] = None
        if (crc_elem := et_element.find("COMPU-RATIONAL-COEFFS")) is not None:
            compu_rational_coeffs = CompuRationalCoeffs.coeffs_from_et(
                crc_elem, doc_frags, value_type=range_type)

        return CompuScale(
            short_label=short_label,
            description=description,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            compu_inverse_value=compu_inverse_value,
            compu_const=compu_const,
            compu_rational_coeffs=compu_rational_coeffs,
            domain_type=domain_type,
            range_type=range_type)

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
