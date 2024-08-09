# SPDX-License-Identifier: MIT
import typing
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, runtime_checkable
from xml.etree import ElementTree

from .admindata import AdminData
from .commrelation import CommRelation
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .swvariable import SwVariable
from .utils import dataclass_fields_asdict
from .variablegroup import VariableGroup


@runtime_checkable
class HasDiagVariables(typing.Protocol):

    @property
    def diag_variables(self) -> "NamedItemList[DiagVariable]":
        ...


@dataclass
class DiagVariable(IdentifiableElement):
    """Representation of a diagnostic variable
    """

    admin_data: Optional[AdminData]
    variable_group_ref: OdxLinkRef
    sw_variables: List[SwVariable]
    comm_relations: List[CommRelation]
    #snref_to_tablerow: Optional[SnrefToTableRow] # TODO
    sdgs: List[SpecialDataGroup]
    is_read_before_write_raw: Optional[bool]

    @property
    def variable_group(self) -> VariableGroup:
        return self._variable_group

    @property
    def is_read_before_write(self) -> bool:
        return self.is_read_before_write_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagVariable":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        variable_group_ref = odxrequire(
            OdxLinkRef.from_et(et_element.find("VARIABLE-GROUP-REF"), doc_frags))
        sw_variables = NamedItemList([
            SwVariable.from_et(swv_elem, doc_frags)
            for swv_elem in et_element.iterfind("SW-VARIABLES/SW-VARIABLE")
        ])
        comm_relations = [
            CommRelation.from_et(cr_elem, doc_frags)
            for cr_elem in et_element.iterfind("COMM-RELATIONS/COMM-RELATION")
        ]
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]
        is_read_before_write_raw = odxstr_to_bool(et_element.get("IS-READ-BEFORE-WRITE"))

        return DiagVariable(
            admin_data=admin_data,
            variable_group_ref=variable_group_ref,
            sw_variables=sw_variables,
            comm_relations=comm_relations,
            sdgs=sdgs,
            is_read_before_write_raw=is_read_before_write_raw,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        for cr in self.comm_relations:
            result.update(cr._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._variable_group = odxlinks.resolve(self.variable_group_ref, VariableGroup)

        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        for cr in self.comm_relations:
            cr._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

        for cr in self.comm_relations:
            cr._resolve_snrefs(context)
