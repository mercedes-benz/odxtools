# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .dataobjectproperty import DataObjectProperty
from .dtcdop import DtcDop
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .odxtypes import AtomicOdxType, odxstr_to_bool
from .preconditionstateref import PreConditionStateRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .statetransitionref import StateTransitionRef
from .structure import Structure
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .table import Table


@dataclass(kw_only=True)
class TableRow(IdentifiableElement):
    """This class represents a TABLE-ROW."""
    table_ref: OdxLinkRef
    key_raw: str

    # The spec mandates that either a structure or a non-complex DOP
    # must be referenced here, i.e., exactly one of the four
    # attributes below is not None
    dop_ref: OdxLinkRef | None = None
    dop_snref: str | None = None
    structure_ref: OdxLinkRef | None = None
    structure_snref: str | None = None

    sdgs: list[SpecialDataGroup] = field(default_factory=list)
    audience: Audience | None = None
    functional_class_refs: list[OdxLinkRef] = field(default_factory=list)
    state_transition_refs: list[StateTransitionRef] = field(default_factory=list)
    pre_condition_state_refs: list[PreConditionStateRef] = field(default_factory=list)
    admin_data: AdminData | None = None

    is_executable_raw: bool | None = None
    semantic: str | None = None
    is_mandatory_raw: bool | None = None
    is_final_raw: bool | None = None

    @property
    def table(self) -> "Table":
        return self._table

    # the value of the key expressed in the type represented by the
    # referenced DOP
    @property
    def key(self) -> AtomicOdxType | None:
        return self._key

    @property
    def dop(self) -> DataObjectProperty | None:
        """The data object property object resolved by dop_ref."""
        return self._dop

    @property
    def structure(self) -> Structure | None:
        """The structure associated with this table row."""
        return self._structure

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def is_executable(self) -> bool:
        return self.is_executable_raw in (None, True)

    @property
    def is_mandatory(self) -> bool:
        return self.is_mandatory_raw is True

    @property
    def is_final(self) -> bool:
        return self.is_final_raw is True

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> Any:
        raise RuntimeError(
            "Calling TableRow.from_et() is not allowed. Use TableRow.tablerow_from_et().")

    @staticmethod
    def tablerow_from_et(et_element: ElementTree.Element, context: OdxDocContext, *,
                         table_ref: OdxLinkRef) -> "TableRow":
        """Reads a TABLE-ROW."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, context))

        key_raw = odxrequire(et_element.findtext("KEY"))

        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), context)
        dop_snref: str | None = None
        if (dop_snref_elem := et_element.find("DATA-OBJECT-PROP-SNREF")) is not None:
            dop_snref = dop_snref_elem.attrib["SHORT-NAME"]

        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), context)
        structure_snref: str | None = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = structure_snref_elem.attrib["SHORT-NAME"]

        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, context)

        functional_class_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
        ]

        state_transition_refs = [
            StateTransitionRef.from_et(el, context)
            for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF")
        ]

        pre_condition_state_refs = [
            PreConditionStateRef.from_et(el, context)
            for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF")
        ]

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), context)

        is_executable_raw = odxstr_to_bool(et_element.attrib.get("IS-EXECUTABLE"))
        semantic = et_element.attrib.get("SEMANTIC")
        is_mandatory_raw = odxstr_to_bool(et_element.attrib.get("IS-MANDATORY"))
        is_final_raw = odxstr_to_bool(et_element.attrib.get("IS-FINAL"))

        return TableRow(
            table_ref=table_ref,
            key_raw=key_raw,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            sdgs=sdgs,
            audience=audience,
            functional_class_refs=functional_class_refs,
            state_transition_refs=state_transition_refs,
            pre_condition_state_refs=pre_condition_state_refs,
            admin_data=admin_data,
            is_executable_raw=is_executable_raw,
            semantic=semantic,
            is_mandatory_raw=is_mandatory_raw,
            is_final_raw=is_final_raw,
            **kwargs)

    def __post_init__(self) -> None:
        self._dop: DataObjectProperty | None = None
        self._structure: Structure | None = None

        n = sum([0 if x is None else 1 for x in (self.dop_ref, self.dop_snref)])
        odxassert(
            n <= 1,
            f"Table row {self.short_name}: The dop can either be defined using ODXLINK or SNREF but not both."
        )

        n = sum([0 if x is None else 1 for x in (self.structure_ref, self.structure_snref)])
        odxassert(
            n <= 1,
            f"Table row {self.short_name}: The structure can either be defined using ODXLINK or SNREF but not both."
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        if self.audience is not None:
            result.update(self.audience._build_odxlinks())

        for st_ref in self.state_transition_refs:
            result.update(st_ref._build_odxlinks())

        for pc_ref in self.pre_condition_state_refs:
            result.update(pc_ref._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if TYPE_CHECKING:
            self._table = odxlinks.resolve(self.table_ref, Table)
        else:
            self._table = odxlinks.resolve(self.table_ref)

        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref)
            if not isinstance(self._dop, (DataObjectProperty, DtcDop)):
                odxraise("The DOP-REF of TABLE-ROWs must reference a simple DOP!")
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref, Structure)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        if self.audience is not None:
            self.audience._resolve_odxlinks(odxlinks)

        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])

        for st_ref in self.state_transition_refs:
            st_ref._resolve_odxlinks(odxlinks)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # convert the raw key into the proper internal
        # representation. note that we cannot do this earlier because
        # the table's ODXLINKs must be resolved and the order of
        # ODXLINK resolution between tables and table-rows is
        # undefined.
        key_dop = self.table.key_dop
        self._key: AtomicOdxType
        if key_dop is None:
            # if the table does not define a DOP for the keys: though
            # luck, expose the raw key string. This is probably a gap
            # in the ODX specification because table-rows must exhibit
            # a "KEY" sub-tag, while the KEY-DOP-REF is optional for
            # tables (and non-existant for table rows...)
            self._key = self.key_raw
        else:
            self._key = key_dop.physical_type.base_data_type.from_string(self.key_raw)

        ddd_spec = odxrequire(context.diag_layer).diag_data_dictionary_spec

        if self.structure_snref is not None:
            self._structure = resolve_snref(self.structure_snref, ddd_spec.structures, Structure)
        if self.dop_snref is not None:
            self._dop = resolve_snref(self.dop_snref, ddd_spec.data_object_props)
            if not isinstance(self._dop, (DataObjectProperty, DtcDop)):
                odxraise("The DOP-SNREF of TABLE-ROWs must reference a simple DOP!")

        if self.audience is not None:
            self.audience._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

        for st_ref in self.state_transition_refs:
            st_ref._resolve_snrefs(context)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_snrefs(context)

    def __reduce__(self) -> tuple[Any, ...]:
        """This ensures that the object can be correctly reconstructed during unpickling."""
        state = self.__dict__.copy()
        return self.__class__, tuple([getattr(self, x.name) for x in fields(self)]), state
