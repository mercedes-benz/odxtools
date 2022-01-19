# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from odxtools.utils import read_description_from_odx


class CommunicationParameterRef:

    def __init__(self,
                 value,
                 id_ref,
                 description=None,
                 protocol_sn_ref=None,
                 prot_stack_sn_ref=None):
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

    def _python_name(self):
        return self.id_ref.replace(".", "__")


def _read_complex_value_from_odx(et_element):
    if et_element.tag == "SIMPLE-VALUE":
        return et_element.text
    else:
        return [el.text if el.tag == "SIMPLE-VALUE" else _read_complex_value_from_odx(el) for el in et_element.findall("*")]


def read_communication_param_ref_from_odx(et_element):
    if et_element.find("SIMPLE-VALUE") is not None:
        value = et_element.find("SIMPLE-VALUE").text
    else:
        value = _read_complex_value_from_odx(et_element.find("COMPLEX-VALUE"))

    id_ref = et_element.get("ID-REF")
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
