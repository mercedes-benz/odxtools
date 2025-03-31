# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List
from xml.etree import ElementTree

from .diagservice import DiagService
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, resolve_snref
from .parameters.parameter import Parameter
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class SubComponentParamConnector(IdentifiableElement):
    diag_comm_snref: str

    # TODO: we currently only support SNREFs, not SNPATHREFs
    out_param_if_refs: List[str]
    in_param_if_refs: List[str]

    @property
    def service(self) -> DiagService:
        return self._service

    @property
    def out_param_ifs(self) -> NamedItemList[Parameter]:
        return self._out_param_ifs

    @property
    def in_param_ifs(self) -> NamedItemList[Parameter]:
        return self._in_param_ifs

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "SubComponentParamConnector":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        diag_comm_snref = odxrequire(
            odxrequire(et_element.find("DIAG-COMM-SNREF")).get("SHORT-NAME"))

        out_param_if_refs = []
        for elem in et_element.find("OUT-PARAM-IF-REFS") or []:
            if elem.tag != "OUT-PARAM-IF-SNREF":
                odxraise("Currently, only SNREFS are supported for OUT-PARAM-IF-REFS")
                continue
            else:
                odxassert(elem.tag == "OUT-PARAM-IF-SNREF")
                out_param_if_refs.append(odxrequire(elem.attrib.get("SHORT-NAME")))

        in_param_if_refs = []
        for elem in et_element.find("IN-PARAM-IF-REFS") or []:
            if elem.tag != "IN-PARAM-IF-SNREF":
                odxraise("Currently, only SNREFS are supported for IN-PARAM-IF-REFS")
                continue
            else:
                odxassert(elem.tag == "IN-PARAM-IF-SNREF")
                in_param_if_refs.append(odxrequire(elem.attrib.get("SHORT-NAME")))

        return SubComponentParamConnector(
            diag_comm_snref=diag_comm_snref,
            out_param_if_refs=out_param_if_refs,
            in_param_if_refs=in_param_if_refs,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        service = resolve_snref(self.diag_comm_snref,
                                odxrequire(context.diag_layer).diag_comms, DiagService)
        self._service = service

        if self._service.request is not None:
            odxraise()
            return
        if not self._service.positive_responses:
            odxraise()
            return

        request = odxrequire(service.request)
        in_param_ifs = []
        for x in self.in_param_if_refs:
            in_param_ifs.append(resolve_snref(x, request.parameters, Parameter))

        # TODO: The output parameters are probably part of a response
        # (?). If so, they cannot be resolved ahead of time because
        # the service in question can have multiple responses
        # associated with it and each of these has its own set of
        # parameters. In the meantime, we simply use the first
        # positive response specified.
        response = service.positive_responses[0]
        out_param_ifs = []
        for x in self.out_param_if_refs:
            out_param_ifs.append(resolve_snref(x, response.parameters, Parameter))

        self._in_param_ifs = NamedItemList(in_param_ifs)
        self._out_param_ifs = NamedItemList(out_param_ifs)
