# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING, List, Union
from xml.etree import ElementTree

from .createsdgs import create_sdgs_from_et
from .exceptions import odxrequire
from .globals import logger
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkId
from .odxtypes import odxstr_to_bool
from .parameters.createanyparameter import create_any_parameter_from_et
from .structure import Structure
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .request import Request
    from .response import Response


def create_any_structure_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]
                                ) -> Union[Structure, "Request", "Response", None]:
    from .request import Request
    from .response import Response

    odx_id = odxrequire(OdxLinkId.from_et(et_element, doc_frags))
    short_name = odxrequire(et_element.findtext("SHORT-NAME"))
    long_name = et_element.findtext("LONG-NAME")
    description = create_description_from_et(et_element.find("DESC"))
    parameters = [
        create_any_parameter_from_et(et_parameter, doc_frags)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

    res: Union[Structure, Request, Response, None]
    if et_element.tag == "REQUEST":
        res = Request(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            is_visible_raw=None,
            parameters=NamedItemList(short_name_as_id, parameters),
            byte_size=None,
            sdgs=sdgs,
        )
    elif et_element.tag in ["POS-RESPONSE", "NEG-RESPONSE", "GLOBAL-NEG-RESPONSE"]:
        res = Response(
            odx_id=odx_id,
            short_name=short_name,
            response_type=et_element.tag,
            long_name=long_name,
            description=description,
            is_visible_raw=None,
            parameters=NamedItemList(short_name_as_id, parameters),
            byte_size=None,
            sdgs=sdgs,
        )
    elif et_element.tag == "STRUCTURE":
        byte_size_text = et_element.findtext("BYTE-SIZE")
        byte_size = int(byte_size_text) if byte_size_text is not None else None
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))
        res = Structure(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            is_visible_raw=is_visible_raw,
            parameters=NamedItemList(short_name_as_id, parameters),
            byte_size=byte_size,
            sdgs=sdgs,
        )
    else:
        res = None
        logger.critical(f"Did not recognize structure {et_element.tag} {short_name}")
    return res
