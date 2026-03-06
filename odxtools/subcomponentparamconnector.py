# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .diagservice import DiagService
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .inputparam import InputParam
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, resolve_snref
from .outputparam import OutputParam
from .parameters.parameter import Parameter
from .singleecujob import SingleEcuJob
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SubComponentParamConnector(IdentifiableElement):
    diag_comm_snref: str

    # TODO: we currently only support SNREFs, not SNPATHREFs
    out_param_if_refs: list[str] = field(default_factory=list)
    in_param_if_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._out_param_ifs: NamedItemList[Parameter] | NamedItemList[OutputParam]
        self._in_param_ifs: NamedItemList[Parameter] | NamedItemList[InputParam]

    @property
    def diag_comm(self) -> DiagComm:
        return self._diag_comm

    @property
    def out_param_ifs(self) -> NamedItemList[Parameter] | NamedItemList[OutputParam]:
        return self._out_param_ifs

    @property
    def in_param_ifs(self) -> NamedItemList[Parameter] | NamedItemList[InputParam]:
        return self._in_param_ifs

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                context: OdxDocContext) -> "SubComponentParamConnector":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

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

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        diag_comm = resolve_snref(
            self.diag_comm_snref,
            odxrequire(context.diag_layer).diag_comms,
            DiagComm,
            use_weakrefs=context.use_weakrefs)
        self._diag_comm = diag_comm

        if isinstance(diag_comm, DiagService):
            if not diag_comm.positive_responses:
                odxraise(f"The DIAG-SERVICE '{diag_comm.short_name}' referenced by "
                         f"SUB-COMPONENT-PARAM-CONNECTOR '{self.short_name}' does "
                         f"not exhibit any positive responses")
                return

            if (request := diag_comm.request) is None:
                odxraise(f"The DIAG-SERVICE '{diag_comm.short_name}' referenced by "
                         f"SUB-COMPONENT-PARAM-CONNECTOR '{self.short_name}' does "
                         f"not exhibit a request")
                return

            # TODO: The output parameters are probably part of a response
            # (?). If so, they cannot be resolved ahead of time because
            # the diag_comm in question can have multiple responses
            # associated with it and each of these has its own set of
            # parameters. In the meantime, we simply use the first
            # positive response specified.
            response = diag_comm.positive_responses[0]
            out_param_service_ifs = []
            for x in self.out_param_if_refs:
                out_param_service_ifs.append(
                    resolve_snref(
                        x, response.parameters, Parameter, use_weakrefs=context.use_weakrefs))

            in_param_service_ifs = []
            for x in self.in_param_if_refs:
                in_param_service_ifs.append(
                    resolve_snref(
                        x, request.parameters, Parameter, use_weakrefs=context.use_weakrefs))

            self._out_param_ifs = NamedItemList(out_param_service_ifs)
            self._in_param_ifs = NamedItemList(in_param_service_ifs)

        elif isinstance(diag_comm, SingleEcuJob):
            # single-ECU jobs specify their input and output parameters directly
            out_param_secuj_ifs = []
            for x in self.out_param_if_refs:
                out_param_secuj_ifs.append(
                    resolve_snref(
                        x, diag_comm.output_params, OutputParam, use_weakrefs=context.use_weakrefs))

            in_param_secuj_ifs = []
            for x in self.in_param_if_refs:
                in_param_secuj_ifs.append(
                    resolve_snref(
                        x, diag_comm.input_params, InputParam, use_weakrefs=context.use_weakrefs))

            self._out_param_ifs = NamedItemList(out_param_secuj_ifs)
            self._in_param_ifs = NamedItemList(in_param_secuj_ifs)

        else:
            odxraise(f"Reference to DIAG-COMM of type {type(diag_comm).__name__} "\
                     f"is not supported")
            return
