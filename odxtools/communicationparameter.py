# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Optional, List

from .odxlink import OdxLinkRef, OdxDocFragment
from .utils import read_description_from_odx

class CommunicationParameterRef:

    def __init__(self,
                 value,
                 id_ref: OdxLinkRef,
                 description: Optional[str] = None,
                 protocol_sn_ref: Optional[str] = None,
                 prot_stack_sn_ref: Optional[str] = None):
        self.value = value
        self.id_ref = id_ref
        self.description = description
        self.protocol_sn_ref = protocol_sn_ref
        self.prot_stack_sn_ref = prot_stack_sn_ref

    def __repr__(self) -> str:
        val = self.value
        if not isinstance(self.value, list):
            val = f"'{val}'"

        return f"CommunicationParameter('{self.id_ref}', value={val})"

    def __str__(self) -> str:
        val = self.value
        if not isinstance(self.value, list):
            val = f"'{val}'"

        return f"CommunicationParameter('{self.id_ref}', value={val})"

    def _python_name(self) -> str:
        # ODXLINK IDs allow dots and hyphens, but python identifiers
        # do not. since _python_name() must return the latter, we have
        # to replace these characters...
        return self.id_ref.ref_id.replace(".", "__").replace("-", "_")


def _read_complex_value_from_odx(et_element):
    result = []
    for el in et_element.findall("*"):
        if el.tag == "SIMPLE-VALUE":
            result.append('' if el.text is None else el.text)
        else:
            result.append(_read_complex_value_from_odx(el))
    return result


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
        value = _read_complex_value_from_odx(et_element.find("COMPLEX-VALUE"))

    description = read_description_from_odx(et_element.find("DESC"))
    protocol_sn_ref = et_element.find(
        "PROTOCOL-SNREF").text if et_element.find("PROTOCOL-SNREF") is not None else None
    prot_stack_sn_ref = et_element.find(
        "PROT-STACK-SNREF").text if et_element.find("PROT-STACK-SNREF") is not None else None
    return CommunicationParameterRef(value,
                                     id_ref,
                                     description=description,
                                     protocol_sn_ref=protocol_sn_ref,
                                     prot_stack_sn_ref=prot_stack_sn_ref
                                     )
