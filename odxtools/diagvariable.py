# SPDX-License-Identifier: MIT
import typing
from dataclasses import dataclass, field
from typing import Any, runtime_checkable
from xml.etree import ElementTree

from .admindata import AdminData
from .commrelation import CommRelation
from .element import IdentifiableElement
from .exceptions import odxrequire
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .odxtypes import odxstr_to_bool
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .swvariable import SwVariable
from .table import Table
from .tablerow import TableRow
from .utils import dataclass_fields_asdict
from .variablegroup import VariableGroup


@runtime_checkable
class HasDiagVariables(typing.Protocol):

    @property
    def diag_variables(self) -> "NamedItemList[DiagVariable]":
        ...


@dataclass(kw_only=True)
class DiagVariable(IdentifiableElement):
    """Representation of a diagnostic variable
    """

    admin_data: AdminData | None = None
    variable_group_ref: OdxLinkRef | None = None
    sw_variables: list[SwVariable] = field(default_factory=list)

    # a diag variable must specify either COMM-RELATIONS or a
    # reference to a table row
    comm_relations: list[CommRelation] = field(default_factory=list)

    # these are nested inside the SNREF-TO-TABLEROW tag
    table_snref: str | None = None
    table_row_snref: str | None = None

    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    is_read_before_write_raw: bool | None = None

    @property
    def table(self) -> Table | None:
        return self._table

    @property
    def table_row(self) -> TableRow | None:
        return self._table_row

    @property
    def variable_group(self) -> VariableGroup | None:
        return self._variable_group

    @property
    def is_read_before_write(self) -> bool:
        return self.is_read_before_write_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DiagVariable":
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)
        variable_group_ref = OdxLinkRef.from_et(et_element.find("VARIABLE-GROUP-REF"), context)
        sw_variables = NamedItemList([
            SwVariable.from_et(swv_elem, context)
            for swv_elem in et_element.iterfind("SW-VARIABLES/SW-VARIABLE")
        ])
        comm_relations = [
            CommRelation.from_et(cr_elem, context)
            for cr_elem in et_element.iterfind("COMM-RELATIONS/COMM-RELATION")
        ]

        table_snref = None
        table_row_snref = None
        if (snref_to_tablerow_elem := et_element.find("SNREF-TO-TABLEROW")) is not None:
            table_snref_elem = odxrequire(snref_to_tablerow_elem.find("TABLE-SNREF"))
            table_snref = odxrequire(table_snref_elem.attrib.get("SHORT-NAME"))

            table_row_snref_elem = odxrequire(snref_to_tablerow_elem.find("TABLE-ROW-SNREF"))
            table_row_snref = odxrequire(table_row_snref_elem.attrib.get("SHORT-NAME"))

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        is_read_before_write_raw = odxstr_to_bool(et_element.get("IS-READ-BEFORE-WRITE"))

        return DiagVariable(
            admin_data=admin_data,
            variable_group_ref=variable_group_ref,
            sw_variables=sw_variables,
            comm_relations=comm_relations,
            table_snref=table_snref,
            table_row_snref=table_row_snref,
            sdgs=sdgs,
            is_read_before_write_raw=is_read_before_write_raw,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        for cr in self.comm_relations:
            result.update(cr._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_odxlinks(odxlinks)

        self._variable_group = None
        if self.variable_group_ref is not None:
            self._variable_group = odxlinks.resolve(self.variable_group_ref, VariableGroup)

        for cr in self.comm_relations:
            cr._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_snrefs(context)

        for cr in self.comm_relations:
            cr._resolve_snrefs(context)

        self._table = None
        self._table_row = None
        if self.table_snref is not None:
            ddds = odxrequire(context.diag_layer).diag_data_dictionary_spec
            self._table = resolve_snref(self.table_snref, ddds.tables, Table)
            self._table_row = resolve_snref(
                odxrequire(self.table_row_snref), self._table.table_rows, TableRow)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)
