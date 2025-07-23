# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .diagcomm import DiagComm
from .inputparam import InputParam
from .nameditemlist import NamedItemList
from .negoutputparam import NegOutputParam
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .outputparam import OutputParam
from .progcode import ProgCode
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class SingleEcuJob(DiagComm):
    """A single ECU job is a diagnostic communication primitive.

    A single ECU job is more complex than a diagnostic service and is
    not provided natively by the ECU.  In particular, the job is
    defined in external programs which are referenced by the attribute
    `.prog_codes`.

    In contrast to "multiple ECU jobs", a single ECU job only involves
    calls to services provided by a single ECU.

    Single ECU jobs are defined in section 7.3.5.7 of the ASAM MCD-2
    standard.
    """

    prog_codes: list[ProgCode] = field(default_factory=list)
    input_params: NamedItemList[InputParam] = field(default_factory=NamedItemList)
    output_params: NamedItemList[OutputParam] = field(default_factory=NamedItemList)
    neg_output_params: NamedItemList[NegOutputParam] = field(default_factory=NamedItemList)

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "SingleEcuJob":
        kwargs = dataclass_fields_asdict(DiagComm.from_et(et_element, context))

        prog_codes = [
            ProgCode.from_et(pc_elem, context)
            for pc_elem in et_element.iterfind("PROG-CODES/PROG-CODE")
        ]

        input_params = NamedItemList([
            InputParam.from_et(el, context)
            for el in et_element.iterfind("INPUT-PARAMS/INPUT-PARAM")
        ])
        output_params = NamedItemList([
            OutputParam.from_et(el, context)
            for el in et_element.iterfind("OUTPUT-PARAMS/OUTPUT-PARAM")
        ])
        neg_output_params = NamedItemList([
            NegOutputParam.from_et(el, context)
            for el in et_element.iterfind("NEG-OUTPUT-PARAMS/NEG-OUTPUT-PARAM")
        ])

        return SingleEcuJob(
            prog_codes=prog_codes,
            input_params=input_params,
            output_params=output_params,
            neg_output_params=neg_output_params,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        for prog_code in self.prog_codes:
            result.update(prog_code._build_odxlinks())
        for input_param in self.input_params:
            result.update(input_param._build_odxlinks())
        for output_param in self.output_params:
            result.update(output_param._build_odxlinks())
        for neg_output_param in self.neg_output_params:
            result.update(neg_output_param._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        for prog_code in self.prog_codes:
            prog_code._resolve_odxlinks(odxlinks)
        for input_param in self.input_params:
            input_param._resolve_odxlinks(odxlinks)
        for output_param in self.output_params:
            output_param._resolve_odxlinks(odxlinks)
        for neg_output_param in self.neg_output_params:
            neg_output_param._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        context.single_ecu_job = self

        super()._resolve_snrefs(context)

        for prog_code in self.prog_codes:
            prog_code._resolve_snrefs(context)
        for input_param in self.input_params:
            input_param._resolve_snrefs(context)
        for output_param in self.output_params:
            output_param._resolve_snrefs(context)
        for neg_output_param in self.neg_output_params:
            neg_output_param._resolve_snrefs(context)

        context.single_ecu_job = None
