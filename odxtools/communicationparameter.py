# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Optional, Any, Union, List, TYPE_CHECKING
import warnings

from odxtools.exceptions import OdxWarning

from .odxlink import OdxLinkDatabase, OdxLinkRef, OdxDocFragment
from .utils import read_description_from_odx
from .comparam_subset import BaseComparam, Comparam, ComplexComparam, ComplexValue, read_complex_value_from_odx


class CommunicationParameterRef:

    def __init__(self,
                 value : Union[str, ComplexValue],
                 id_ref: OdxLinkRef,
                 description: Optional[str] = None,
                 protocol_sn_ref: Optional[str] = None,
                 prot_stack_sn_ref: Optional[str] = None) -> None:
        self.value = value
        self.id_ref = id_ref
        self.description = description
        self.protocol_sn_ref = protocol_sn_ref
        self.prot_stack_sn_ref = prot_stack_sn_ref
        self.comparam: Optional[BaseComparam] = None

    def __repr__(self) -> str:
        val = self.value
        if isinstance(val, str):
            val = f"'{val}'"
        return f"CommunicationParameter('{self.short_name}', value={val})"

    def __str__(self) -> str:
        return self.__repr__()

    def _resolve_references(self, odxlinks: OdxLinkDatabase):
        # Temporary lenient until tests are updated
        self.comparam = odxlinks.resolve_lenient(self.id_ref)
        if not self.comparam:
            warnings.warn(f"Could not resolve COMPARAM '{self.id_ref}'", OdxWarning)

    def get_value(self) \
            -> Optional[str]:
        """Retrieve the value of a simple communication parameter

        This takes the default value of the comparam (if any) into
        account.
        """

        assert isinstance(self.comparam, Comparam)

        result: Any = None
        if self.value:
            result = self.value
        else:
            result = self.comparam.physical_default_value

        assert isinstance(result, str)

        return result

    def get_subvalue(self, subparam_name: str) \
            -> Optional[str]:
        """Retrieve the value of a complex communication parameter's sub-parameter by name

        This takes the default value of the comparam (if any) into
        account.
        """
        comparam_spec = self.comparam
        assert isinstance(comparam_spec, ComplexComparam)

        value_list = self.value
        if not isinstance(value_list, list):
            warnings.warn(f"The values of complex communication parameter "
                          f"'{self.short_name}' are not specified "
                          f"correctly.", OdxWarning)
            return None

        name_list = [ cp.short_name for cp in comparam_spec.comparams ]
        try:
            idx = name_list.index(subparam_name)
        except ValueError:
            warnings.warn(f"Communication parameter '{self.short_name}' "
                          f"does not specify a '{subparam_name}' sub-parameter.",
                          OdxWarning)
            return None

        result = value_list[idx]
        if not result and \
           (default_values := comparam_spec.complex_physical_default_value):
            result = default_values[idx]
        assert isinstance(result, str)

        return result

    @property
    def short_name(self):
        if self.comparam:
            return self.comparam.short_name
        # ODXLINK IDs allow dots and hyphens, but python identifiers do not.
        # This should not happen anyway in a correct PDX
        return self.id_ref.ref_id.replace(".", "__").replace("-", "_")

def read_communication_param_ref_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    id_ref = OdxLinkRef.from_et(et_element, doc_frags)
    assert id_ref is not None

    # ODX standard v2.0.0 defined only VALUE
    # ODX standard v2.0.1 decided to break things and change it to choice between SIMPLE-VALUE and COMPLEX-VALUE
    if et_element.find("VALUE") is not None:
        value = et_element.findtext("VALUE")
    elif et_element.find("SIMPLE-VALUE") is not None:
        value = et_element.findtext("SIMPLE-VALUE")
    else:
        value = read_complex_value_from_odx(et_element.find("COMPLEX-VALUE"))

    description = read_description_from_odx(et_element.find("DESC"))

    prot_stack_snref = None
    if (psnref_elem := et_element.find("PROT-STACK-SNREF")) is not None:
        prot_stack_snref = psnref_elem.get("SHORT-NAME")

    protocol_snref = None
    if (psnref_elem := et_element.find("PROTOCOL-SNREF")) is not None:
        protocol_snref = psnref_elem.get("SHORT-NAME")

    return CommunicationParameterRef(value,
                                     id_ref,
                                     description=description,
                                     protocol_sn_ref=protocol_snref,
                                     prot_stack_sn_ref=prot_stack_snref
                                     )
