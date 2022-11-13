# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Optional, List, TYPE_CHECKING
import warnings

from odxtools.exceptions import OdxWarning

from .odxlink import OdxLinkDatabase, OdxLinkRef, OdxDocFragment
from .utils import read_description_from_odx
from .comparam_subset import BaseComparam, Comparam, ComplexComparam, read_complex_value_from_odx


def _get_comparam_value(comparam: BaseComparam, value):
    if not comparam:
        return value
    if value is None:
        value = comparam.physical_default_value

    if isinstance(comparam, Comparam):
        return comparam.dop.physical_type.base_data_type.from_string(value)

    if isinstance(comparam, ComplexComparam) and isinstance(value, list):
        value = value + [None] * (len(comparam.comparams) - len(value))
        result = dict()
        for i, cp in enumerate(comparam.comparams):
            result[cp.short_name] = _get_comparam_value(cp, value[i])
        return result

    return value


class CommunicationParameterRef:

    def __init__(self,
                 value,
                 id_ref: OdxLinkRef,
                 description: Optional[str] = None,
                 protocol_sn_ref: Optional[str] = None,
                 prot_stack_sn_ref: Optional[str] = None):
        self._value = value
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

    @property
    def short_name(self):
        if self.comparam:
            return self.comparam.short_name
        # ODXLINK IDs allow dots and hyphens, but python identifiers do not.
        # This should not happen anyway in a correct PDX
        return self.id_ref.ref_id.replace(".", "__").replace("-", "_")

    @property
    def value(self):
        return _get_comparam_value(self.comparam, self._value)


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
    protocol_sn_ref = et_element.findtext("PROTOCOL-SNREF")
    prot_stack_sn_ref = et_element.findtext("PROT-STACK-SNREF")
    return CommunicationParameterRef(value,
                                     id_ref,
                                     description=description,
                                     protocol_sn_ref=protocol_sn_ref,
                                     prot_stack_sn_ref=prot_stack_sn_ref
                                     )
