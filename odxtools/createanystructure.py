# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING, List, Union
from xml.etree import ElementTree

from .admindata import AdminData
from .createsdgs import create_sdgs_from_et
from .element import IdentifiableElement
from .globals import logger
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment
from .parameters.createanyparameter import create_any_parameter_from_et
from .structure import Structure
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .request import Request
    from .response import Response


def create_any_structure_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]
                                ) -> Union[Structure, "Request", "Response", None]:
    from .request import Request
    from .response import Response

    kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
    parameters = [
        create_any_parameter_from_et(et_parameter, doc_frags)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
    sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

    res: Union[Structure, Request, Response, None]
    if et_element.tag == "REQUEST":
        res = Request(
            parameters=NamedItemList(parameters),
            byte_size=None,
            admin_data=admin_data,
            sdgs=sdgs,
            **kwargs)
    elif et_element.tag in ["POS-RESPONSE", "NEG-RESPONSE", "GLOBAL-NEG-RESPONSE"]:
        res = Response(
            response_type=et_element.tag,
            parameters=NamedItemList(parameters),
            byte_size=None,
            admin_data=admin_data,
            sdgs=sdgs,
            **kwargs)
    elif et_element.tag == "STRUCTURE":
        byte_size_text = et_element.findtext("BYTE-SIZE")
        byte_size = int(byte_size_text) if byte_size_text is not None else None
        res = Structure(
            parameters=NamedItemList(parameters),
            byte_size=byte_size,
            admin_data=admin_data,
            sdgs=sdgs,
            **kwargs)
    else:
        res = None
        logger.critical(f"Did not recognize structure {et_element.tag} {kwargs['short_name']}")
    return res
